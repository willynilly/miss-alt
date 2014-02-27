from flask import Flask, flash, session, redirect, url_for, escape, request, render_template, Response
from flask.ext.pymongo import PyMongo, ObjectId
from collections import Counter
from smartjson import smart_jsonify, request_wants_json
from utility import get_full_filename_from_url
from crossdomain import crossdomain

import hashlib, uuid
import datetime

app = Flask(__name__)
mongo = PyMongo(app)

def get_hashed_password(password, salt="somesalt"):
    return hashlib.sha512(password + salt).hexdigest()

def is_logged_in():
    return session is not None and 'user_id' in session and session['user_id'] is not None

def get_current_user():
    if is_logged_in():
        return mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    else:
        return None

def get_object_by_form_or_json(var_names=[]):
    obj = {k:'' for k in var_names}
    json = request.get_json(silent=True)
    if json is None:
        issue = {k:request.form[k].strip() for k in var_names}
    else:
        issue = dict(obj.items() + json.items())
    return issue

@app.route('/')
def index():
    if is_logged_in:
        issues = get_issues_by_user(get_current_user())
        issues = list(issues)
        for i in issues:
            i['complaint_count'] = sum(i['reporters'].values())
            i['img_filename'] = get_full_filename_from_url(i['img_url'])
    else:
        issues = None
    return render_template('home.html', issues=issues)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    email = password = disability = organization = ""
    if request.method == 'POST':
        email = request.form['email'].strip()
        user = mongo.db.users.find_one({'email': email})
        if user is None:
            password = request.form['password'].strip()
            if len(password) < 8:
                error = 'Please enter a password that has at least 8 alphanumeric characters.'
            else:
                disability = request.form['disability'].strip()
                organization = request.form['organization'].strip()
                user = {"email": email, 
                        "hashed_password": get_hashed_password(password),
                        "disability": disability,
                        "organization": organization,
                        "created_on": datetime.datetime.utcnow(),
                        "updated_on": datetime.datetime.utcnow()}
                user_id = mongo.db.users.insert(user)
                session['user_id'] = str(user_id)
                return redirect(url_for('index'))
        else:
            error = 'Please choose a different email address.'
    return render_template('register.html', error=error, email=email, password=password, disability=disability, organization=organization)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    email = password = ""
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        user = mongo.db.users.find_one({'email': email, 'hashed_password': get_hashed_password(password)})
        if user is not None:
            session['user_id'] = str(user['_id'])
            return redirect(url_for('index'))
        else:
            error = 'Invalid email address or password.'
    return render_template('login.html', error=error)
    
@app.route('/logout')
def logout():
    # remove the user from the session if it's there
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/user/<userid>')
def user_profile(userid):
    user = mongo.db.users.find_one_or_404({'_id': userid})
    return render_template('user.html', user=user)

@app.route('/report', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/issue', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def report():
    error = None
    issue_var_names =  ['page_url', 'img_url', 'img_current_alt_text', 'img_suggested_alt_text']
    issue = {k:'' for k in issue_var_names}
    respond_with_json = request_wants_json(request)

    if request.method == 'POST':
        issue = get_object_by_form_or_json(issue_var_names)
                    
        if not issue['page_url']:
            error = "Please enter the URL for the web page containing the image."
        else:
            if not issue['img_url']:
                error = "Please enter the URL for the image file."
        
        if error is None:
            
            if is_logged_in():        
                reporter_user_id = session['user_id']
            else:
                reporter_user_id = None
                
            issue = add_issue(reporter_user_id, issue)
            
            if respond_with_json:
                return smart_jsonify(issue)
            else:
                flash('The image was successfully reported.')
                return redirect(url_for('index'))
        else:
            if respond_with_json:
                return smart_jsonify(error=error)
    
    if respond_with_json:
        issues = mongo.db.issues.find()
        return smart_jsonify(issues)
    else:
        return make_response(render_template('report.html', error=error, issue=issue))

def add_issue(reporter_user_id, issue):
    if reporter_user_id is None:
        reporter_user_id = 'Unknown'
    n_issue = mongo.db.issues.find_one({'img_url': issue['img_url'], 'page_url': issue['page_url']})    
    if n_issue is None:
        n_issue = {"img_url": issue['img_url'], \
                    "page_url": issue['page_url'], \
                    "created_on": datetime.datetime.utcnow(), \
                    "reporters": []}
    n_issue['img_current_alt_text'] = issue['img_current_alt_text']
    n_issue['img_suggested_alt_text'] = issue['img_suggested_alt_text']
    
    # add reporter_id frequencies
    n_issue['reporters'] = {k:v for (k, v) in (Counter(n_issue['reporters']) + Counter({reporter_user_id:1})).iteritems()}
    
    n_issue['updated_on'] = datetime.datetime.utcnow()

    #print n_issue
    
    mongo.db.issues.update({'img_url': issue['img_url'], 'page_url': issue['page_url']}, n_issue, True)
    n_issue = mongo.db.issues.find_one({'img_url': n_issue['img_url'], 'page_url': n_issue['page_url']})    
    return n_issue


def get_issues_by_user(user):
    if user is None:
        return None
    else:
        # https://stackoverflow.com/questions/10242149/sorting-with-mongodb-and-python
        #return mongo.db.issues.find().sort([("created_on", -1)])    
        return mongo.db.issues.find({'reporters': {'$exists': [str(user['_id'])]}}).sort([("created_on", -1)])    
        
# @app.route('/img/<imgid>')
# def img_profile(imgid):
#     user = mongo.db.imgs.find_one_or_404({'_id': imgid})
#     return render_template('img.html',
#         img=img)

# extra global helper functions for templating engine
app.jinja_env.globals['is_logged_in'] = is_logged_in

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

app.debug = True

if __name__ == '__main__':
    app.run()