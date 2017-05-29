#############################################################################################################################################
"""web.py: This is the web server.  Keep this running"""

__author__ = "Anand Iyer"
__copyright__ = "Copyright 2016-17, Anand Iyer"
__credits__ = ["Anand Iyer"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Anand Iyer"
__email__ = "ananddotiyer@gmail.com"
__status__ = "Production"
#############################################################################################################################################

from importlib import import_module

from flask import Flask, session, escape, request, send_from_directory, render_template, redirect, url_for, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, validators
from wtforms.validators import Required, Length
from werkzeug.utils import secure_filename
from uuid import getnode as get_mac
import traceback
from support import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
bootstrap = Bootstrap(app)

#if __name__ == '__main__' and __package__ is None:
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from main import main_config, main_driver
from tests.tests_suite import *

@app.route('/')
def index():
    if 'username' in session and not escape(session['username']) == "":
        info = logged_in_user (session)
        return render_template('user.html', info=info, username=escape(session['username']))
    else:
        return redirect(url_for('login'))    

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    #if request.method == 'POST':
    if form.validate_on_submit():
        #if form.password.data == form.username.data[::-1]:
        session['username'] = form.username.data
        return redirect(url_for('tests'))

    # mac = '-'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
    # form.username.data = '%s' %(mac[:-3])
    return render_template ('login.html', form=form)

    # return '''
    #     <form action="" method="post">
    #         <p><input type=text name=username>
    #         <p><input type=submit value=Login>
    #     </form>
    # '''

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/tests', methods=('GET', 'POST'))
def tests():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    test_list = []

    global_dict = main_config (True, escape(session['username']))

    for test in global_dict["tests"]:
        test_list.append (test[0]) #global_dict["tests"] is a tuple consisting of tests, test_category and subfolder

    if request.method == "POST":
        run_selected = []
        check_list = request.form.getlist("select")
        
        for each_test in global_dict["tests"]:
            test = each_test[0] #each_test is a tuple of test, test_category, subfolder.
            cat = each_test[1]
            subfolder = each_test[2]
            
            for check in check_list:
                check = check.split (',')
                if cat == check[0] and test["api_name"] == check[1]:
                    run_selected.append (each_test)
                    break

        global_dict["run_selected"] = run_selected
        
        if not global_dict["running"]:
            global_dict["running"] = True #so that you don't run it again!
            main_driver (True, escape(session['username']))
        
        global_dict["running"] = False #so that you can run it again!
        return redirect(url_for('results'))
    
    return render_template('tests.html', tests=test_list, username=escape(session['username']))

@app.route ("/results")
def results ():
    import csv
    import os

    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))
    
    try:
        tests_folder = global_dict["test_folder"]
        reader = csv.DictReader(open(tests_folder + 'passfaillog.csv'))

        results_list = []
        for line in reader:
            results_list.append(line)
            
            #making the path for the exported csv file
            file_path = extract_filename_from_hyperlink (line["test_path"])
            
            folder_parts = file_path.split ('\\')
            folder = tests_folder + '\\'.join (folder_parts[:-1]) #tests folder
            filename = folder_parts[-1] #only the filename
            line["test_path"] = "download?folder=%s/&filename=%s" %(folder, filename)
            
            file_path = extract_filename_from_hyperlink (line["result"])
            folder_parts = file_path.split ('\\')
            filename = folder_parts[-1] #only the filename
            line["debuglog"] = "debuglog?debuglog=%s" %(filename)
            line["result"] = extract_text_from_hyperlink (line["result"]) #FAIL, PASS

            file_path = extract_filename_from_hyperlink (line["schema"])
            folder_parts = file_path.split ('\\')
            filename = folder_parts[-1] #only the filename
            schema_file = global_dict["schema_folder"] + filename
            if not os.path.isfile(schema_file):
                line["schema"] = "none"
            line["schema"] = "schema?schema=%s" %(filename)
        return render_template ('results.html', results=results_list, username=escape(session['username']))
    except:
        traceback.print_exc ()
        return render_template ('no_results.html', running=global_dict["running"], username=escape(session['username']))

@app.route ("/run")
def run ():
    import csv
    import os

    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))
    
    try:
        # if not global_dict["running"]:
        #     global_dict["running"] = True #so that you don't run it again!
        #     main_driver (True)

        global_dict["running"] = False

        tests_folder = global_dict["test_folder"]
        reader = csv.DictReader(open(tests_folder + 'passfaillog.csv'))

        results_list = []
        for line in reader:
            results_list.append(line)
            
            #making the path for the exported csv file
            file_path = extract_filename_from_hyperlink (line["test_path"])
            folder_parts = file_path.split ('\\')
            folder = tests_folder + '\\'.join (folder_parts[:-1]) #tests folder
            filename = folder_parts[-1] #only the filename
            line["test_path"] = "download?folder=%s&filename=%s" %(folder, filename)
            
            #making the path for the specific debuglog
            file_path = extract_filename_from_hyperlink (line["result"])
            folder_parts = file_path.split ('\\')
            filename = folder_parts[-1] #only the filename
            line["debuglog"] = "debuglog?debuglog=%s" %(filename)
            line["result"] = extract_text_from_hyperlink (line["result"]) #FAIL, PASS

            #making the path for the schema compare file
            file_path = extract_filename_from_hyperlink (line["schema"])
            folder_parts = file_path.split ('\\')
            filename = folder_parts[-1] #only the filename
            schema_file = global_dict["schema_folder"] + filename
            if not os.path.isfile(schema_file):
                line["schema"] = "none"
            line["schema"] = "schema?schema=%s" %(filename)
             
        return render_template ('run.html', results=results_list, username=escape(session['username']))
    except:
        traceback.print_exc ()
        return render_template ('no_results.html', running=global_dict["running"], username=escape(session['username']))

@app.route ("/run_ci")
def run_ci ():
    import csv
    import json

    try:
        username = request.args.get ('username')
    
        global_dict = main_config (True, username=username)
        global_dict["run_selected"] = global_dict["tests"]
    
        main_driver (True, username=username)
    
        tests_folder = global_dict["test_folder"].replace ('\\', '/')
        print tests_folder
        
        line = {"report":"http://localhost:5000/download?folder=%s&filename=passfaillog.csv" %(tests_folder)}
       
        line = json.dumps (line)
        return line
    except:
        return render_template ('no_ops.html', username=escape(session['username']))

@app.route ("/schema")
def schema ():
    lines = []
    tabs = []

    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))

    filename = request.args.get ('schema')
    try:
        if not filename:
            reader = open(global_dict["test_folder"] + "/schema.txt")
        else:
            reader = open(global_dict["schema_folder"] + "/" + filename)
        
        for line in reader:
            tabs_num = (len(line) - len(line.lstrip(' '))) / 4 #number of tabs
            tabs.append (tabs_num)
            lines.append(line.strip ())
        reader.close()
    
        return render_template ('schema.html', indices=range (len (tabs)), tabs=tabs, schema=lines, username=escape(session['username']))
    except:
        return render_template ('no_schema.html', username=escape(session['username']))

@app.route ("/cleanup")
def cleanup ():
    import os
    import shutil
    
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))
    
    try:
        schema_folder = global_dict["schema_folder"]
        for file in os.listdir(schema_folder):
            if not file == "__init__.py":
                os.remove (schema_folder + "\\" + file)
    
        debuglog_folder = global_dict["debuglog"]
        for file in os.listdir(debuglog_folder):
            if not file == "__init__.py":
                os.remove (debuglog_folder + "\\" + file)
    
        shutil.copy (global_dict["test_folder"] + "passfaillog_blank.csv", global_dict["test_folder"] + "passfaillog.csv")
    
        return render_template ('cleanup.html', username=escape(session['username']))
    except:
        return render_template ('no_ops.html', username=escape(session['username']))

@app.route ("/debuglog")
def debuglog ():
    lines = []

    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))

    filename = request.args.get ('debuglog')
    reader = open(global_dict["debuglog"] + "/" + filename)
    for line in reader:
        lines.append(line.strip ())
    reader.close()

    try:
        return render_template ('debuglog.html', lines=lines, username=escape(session['username']))
    except:
        return render_template ('no_results.html', running=global_dict["running"], username=escape(session['username']))

class CreateNewTest (FlaskForm):
    def __init__(self, api_category, api_name, *args, **kwargs):
        super(CreateNewTest, self).__init__(*args, **kwargs)
        self.api_category = api_category
        self.api_name = api_name
        
    category = StringField('Category: ', render_kw={'readonly': True})
    name = StringField('Name: ', validators=[Required(), Length(1, 30)])
    method = StringField('Type: ')
    url = StringField('URL: ', validators=[Required(), Length(1, 1000)], render_kw={"style":"width: 1000px;"})
    parameters = StringField('Parameters: ', render_kw={"style":"width: 1000px;"})
    expected = StringField('Expected: ', validators=[Required()], render_kw={"style":"width: 1000px;"})
    repl = StringField('Replace string: ')
    store = StringField('Store: ')
    function = StringField('Function: ', validators=[Required()])
    output = StringField('Output mode: ', validators=[Required(), Length(1, 3)])
    #upload = FileField ()

    def validate_name (form, field):
        if field.data == '"%s"' %(form.api_name):
            print 'api name already exists!'
            raise validators.ValidationError('api name already exists')
    
    submit = SubmitField('Duplicate')

class EditTest (FlaskForm):
    def __init__(self, api_category, api_name, *args, **kwargs):
        super(EditTest, self).__init__(*args, **kwargs)
        self.api_category = api_category
        self.api_name = api_name
        
    category = StringField('Category: ', render_kw={'readonly': True})
    name = StringField('Name: ', validators=[Required(), Length(1, 30)])
    method = StringField('Type: ')
    url = StringField('URL: ', validators=[Required(), Length(1, 1000)], render_kw={"style":"width: 1000px;"})
    parameters = StringField('Parameters: ', render_kw={"style":"width: 1000px;"})
    expected = StringField('Expected: ', validators=[Required()], render_kw={"style":"width: 1000px;"})
    repl = StringField('Replace string: ')
    store = StringField('Store: ')
    function = StringField('Function: ', validators=[Required()])
    output = StringField('Output mode: ', validators=[Required(), Length(1, 3)])
    #upload = FileField ()

    def validate_name (form, field):
        if not field.data == '"%s"' %(form.api_name):
            raise validators.ValidationError('api name cannot be changed')
    
    submit = SubmitField('Edit')
    
class UploadTest (FlaskForm):
    import_from_postman = FileField ()
    upload_tests = FileField ()

    submit = SubmitField('Upload')

class LoginForm (FlaskForm):
    username =  StringField ('User name')
    password =  PasswordField ('Password')

    submit = SubmitField('Login')

    def validate_username (form, field):
        tests_folder_name = "tests_%s" %(field.data)
        tests_folder = "%s/%s" %(path.dirname(path.dirname(path.abspath(__file__))), tests_folder_name)
        tests_modules_name = "%s." %(tests_folder_name)
        try:
            print tests_modules_name + "tests_suite"
            import_module (tests_modules_name + "tests_suite")
        except:
            raise validators.ValidationError('User does not exist')

    def validate_password(form, field):
            if not form.username.data == field.data[::-1]:
                raise validators.ValidationError('Password incorrect')
    
@app.route ("/test_upload", methods=('GET', 'POST'))
def test_upload ():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))

    try:
        form = UploadTest()

        import_result = ""
        upload_result = ""

        if form.validate_on_submit():
            tests_folder = global_dict["test_folder"] + "Misc"
            #Import POSTMAN tests (exported from POSTMAN)   
            f = form.import_from_postman.data
            if not f.filename == "":
                filename = secure_filename(f.filename)
                f.save(tests_folder + "\\" + filename)
                import_result = import_from_postman (tests_folder, filename, "tests_user_defined")
                if import_result:
                    import_result = "Successfully imported %s into 'Misc' test category" %(filename)
                else:
                    import_result = ""
            
            #Upload the exported file
            f = form.upload_tests.data
            if not f.filename == "":
                filename = secure_filename(f.filename)
                try:
                    f.save(tests_folder + "\\" + filename)
                    upload_result = True
                except:
                    upload_result = False

                if upload_result:
                    upload_result = "Successfully uploaded %s to the server" %(filename)
                else:
                    upload_result = ""
            
            return redirect(url_for('test_uploaded', import_result=import_result, upload_result=upload_result))

        return render_template ('test_upload.html', form=form, username=escape(session['username']))
    except:
        traceback.print_exc ()
        #return render_template ('no_test.html')
        return redirect(url_for('test_uploaded', import_result=import_result, upload=upload_result))

@app.route ("/test_created_upload", methods=('GET', 'POST'))
def test_created_upload ():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))

    try:
        form = UploadTest()

        if request.method == 'GET':
            form.upload.data = '"tests_user_defined.py"'

        if form.validate_on_submit():
            #Upload the exported file
            tests_folder = global_dict["test_folder"] + "Misc"
            f = form.upload.data
            filename = secure_filename(f.filename)
            f.save(tests_folder + "\\" + filename)

            return redirect(url_for('test_uploaded'))

        return render_template ('test_upload.html', form=form, username=escape(session['username']))
    except:
        traceback.print_exc ()
        return render_template ('no_results.html', running=global_dict["running"], username=escape(session['username']))

@app.route ("/duplicate", methods=('GET', 'POST'))
def duplicate ():
    lines = []

    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))
    tests = global_dict["tests"]

    api_category = request.args.get ('cat')
    api_name = request.args.get ('name')
    
    for each_test in tests:
        test = each_test[0]
        cat = each_test[1]
        subfolder = each_test[2]
        
        if cat == api_category and test["api_name"] == api_name:
            break
    try:
        form = CreateNewTest(api_category, api_name)
        
        #Pre-populate data
        if request.method == 'GET':
            form.category.data = "Misc.tests_user_defined" #disabled in the jinja template
            form.name.data = '"%s"' %(test["api_name"])
            form.method.data = '"%s"' %(test["api_type"])
            form.url.data = '"%s"' %(test["api_url"])
            form.parameters.data = test["api_params"]
            form.expected.data = test["api_expected"]
            form.repl.data = test["api_repl"]
            form.store.data = test["api_store"]
            form.function.data = '"%s"' %(test["api_function"])
            form.output.data = '"%s"' %(test["output_mode"])
        
        new_test = {}
        if form.validate_on_submit():
            new_test["api_name"] = form.name.data
            new_test["api_type"] = form.method.data
            new_test["api_url"] = form.url.data
            new_test["api_params"] = form.parameters.data
            new_test["api_expected"] = form.expected.data
            new_test["api_repl"] = form.repl.data
            new_test["api_store"] = form.store.data
            new_test["api_function"] = form.function.data
            new_test["output_mode"] = form.output.data

            mod = import_module (global_dict["test_module"] + "Misc.tests_user_defined")
            tests = getattr (mod, "tests_user_defined")
            
            tests_folder = global_dict["test_folder"] + "Misc/"
            with open (tests_folder + "tests_user_defined.py", "w") as fp:
                fp.write ("tests_user_defined = [\n")
                #existing tests
                for test in tests:
                    fp.write ("{\n")
                    for each in test:
                        if not type (test[each] ) == dict or type (test[each] ) == list:
                            fp.write ('\t"%s" : "%s",\n' %(each, test[each]))
                        else:
                            fp.write ('\t"%s" : %s,\n' %(each, test[each]))
                            
                    fp.write ("},\n")
                
                #new test
                fp.write ("{\n")
                for each in new_test:
                    fp.write ('\t"%s" : %s,\n' %(each, new_test[each]))
                fp.write ("}\n")
                fp.write ("]")

            return redirect(url_for('test_created')) #creates test (tests_user_defined.py) in tests folder in server.
        return render_template ('duplicate.html', form=form, username=escape(session['username']))
    except:
        traceback.print_exc ()
        return render_template ('no_ops.html', username=escape(session['username']))

@app.route ("/edittest", methods=('GET', 'POST'))
def edittest ():
    lines = []

    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))
    tests = global_dict["tests"]

    api_category = request.args.get ('cat')
    api_name = request.args.get ('name')
    
    for each_test in tests:
        test = each_test[0]
        cat = each_test[1]
        subfolder = each_test[2]
        
        if cat == api_category and test["api_name"] == api_name:
            break
    try:
        form = EditTest(api_category, api_name)
        
        #Pre-populate data
        if request.method == 'GET':
            form.category.data = "Misc.tests_user_defined" #disabled in the jinja template
            form.name.data = '"%s"' %(test["api_name"])
            form.method.data = '"%s"' %(test["api_type"])
            form.url.data = '"%s"' %(test["api_url"])
            form.parameters.data = test["api_params"]
            form.expected.data = test["api_expected"]
            form.repl.data = test["api_repl"]
            form.store.data = test["api_store"]
            form.function.data = '"%s"' %(test["api_function"])
            form.output.data = '"%s"' %(test["output_mode"])
        
        edited_test = {}
        if form.validate_on_submit():
            edited_test["api_name"] = form.name.data
            edited_test["api_type"] = form.method.data
            edited_test["api_url"] = form.url.data
            edited_test["api_params"] = form.parameters.data
            edited_test["api_expected"] = form.expected.data
            edited_test["api_repl"] = form.repl.data
            edited_test["api_store"] = form.store.data
            edited_test["api_function"] = form.function.data
            edited_test["output_mode"] = form.output.data

            mod = import_module (global_dict["test_module"] + "Misc.tests_user_defined")
            tests = getattr (mod, "tests_user_defined")
            tests.remove (test)
            
            tests_folder = global_dict["test_folder"] + "Misc/"
            with open (tests_folder + "tests_user_defined.py", "w") as fp:
                fp.write ("tests_user_defined = [\n")
                #existing tests
                for test in tests:
                    fp.write ("{\n")
                    for each in test:
                        if not type (test[each] ) == dict or type (test[each] ) == list:
                            fp.write ('\t"%s" : "%s",\n' %(each, test[each]))
                        else:
                            fp.write ('\t"%s" : %s,\n' %(each, test[each]))
                            
                    fp.write ("},\n")
                #edited test
                fp.write ("{\n")
                for each in edited_test:
                    fp.write ('\t"%s" : %s,\n' %(each, edited_test[each]))
                fp.write ("}\n")
                fp.write ("]")

            return redirect(url_for('test_edited')) #creates test (tests_user_defined.py) in tests folder in server.
        return render_template ('edittest.html', form=form, username=escape(session['username']))
    except:
        traceback.print_exc ()
        return render_template ('no_ops.html', username=escape(session['username']))

@app.route ("/delete", methods=('GET','POST'))
def delete ():
    lines = []

    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    global_dict = main_config (True, escape(session['username']))
    tests = global_dict["tests"]

    api_category = request.args.get ('cat')
    api_name = request.args.get ('name')
    
    for each_test in tests:
        test = each_test[0] #each_test is a tuple of test, test_category, subfolder.
        cat = each_test[1]
        subfolder = each_test[2]

        if cat == api_category and test["api_name"] == api_name:
            break
    try:
        mod = import_module (global_dict["test_module"] + "Misc.tests_user_defined")
        tests = getattr (mod, "tests_user_defined")

        #Before and after print is an odd fix to a server crash.  Possibly, this is creating a required delay.
        print "Before: " + str (len (tests))
        tests.remove (test)
        print "After:" + str (len (tests))
        tests_folder = global_dict["test_folder"] + "Misc/"
        with open (tests_folder + "tests_user_defined.py", "w") as fp:
            fp.write ("tests_user_defined = [\n")
            #existing tests
            for test in tests:
                fp.write ("{\n")
                for each in test:
                    if type (test[each] ) == str or type (test[each] ) == unicode:
                        fp.write ('\t"%s" : "%s",\n' %(each, test[each]))
                    else:
                        fp.write ('\t"%s" : %s,\n' %(each, test[each]))
                        
                fp.write ("},\n")
            fp.write ("]")
                
            return redirect(url_for('test_deleted')) #deletes test (tests_user_defined.py) in tests folder in server.
    except:
        traceback.print_exc ()
        return render_template ('no_test.html', username=escape(session['username']))

@app.route ("/download")
def download ():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    folder = request.args.get ('folder')
    filename = request.args.get ('filename')
    
    if "tests_%s" %(escape(session['username'])) in folder: #allow only tests for the corresponding login to be downloaded
        return send_from_directory(folder, filename, as_attachment=True)
    else:
        return render_template ('no_test.html', username=escape(session['username']))

@app.route ("/test_uploaded")
def test_uploaded ():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    return render_template ('test_uploaded.html',import_result=request.args.get ("import_result"), upload_result=request.args.get ("upload_result"), username=escape(session['username']))

@app.route ("/test_created")
def test_created ():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    return render_template ('test_created.html', username=escape(session['username']))

@app.route ("/test_edited")
def test_edited ():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    return render_template ('test_edited.html', username=escape(session['username']))

@app.route ("/test_deleted")
def test_deleted ():
    if not 'username' in session:
        info = logged_in_user (session)
        return render_template('user.html', info=info)

    return render_template ('test_deleted.html', username=escape(session['username']))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

#Following code has been commented, since it's preferrable to run the server using the flask-cli
#Steps to use to run flask-cli:
#Add the path to web.py to PYTHONPATH
#In the cmd shell,  run the following commands.
#cd <folder path>\modules\web
#set FLASK_APP=web.py
#set FLASK_DEBUG=1
#flask run --with-threads

# if __name__ == '__main__':
#     # set the secret key.  keep this really secret:
#     #app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#     while True:
#         print "Restarting..."
#         app.run(host='0.0.0.0', threaded=True, debug=True)
#     
#     print "Exiting..."