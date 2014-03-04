from flask import Flask, flash, session, redirect, url_for, escape, request, render_template, make_response, Response
from flask.ext.classy import FlaskView
from flask.ext.pymongo import PyMongo, ObjectId
from smartjson import smart_jsonify, request_wants_json
from utility import get_full_filename_from_url
from crossdomain import crossdomain
from issue import Issue
import hashlib, uuid
import datetime

app = Flask(__name__)
mongo = PyMongo(app)
Issue.mongo = mongo

# class IssuesView:
#     def index(self):
#         pass
#         
#     def get(self, id):
#         pass
#         
#     def post(self, id):
#         pass
#     
#     def delete(self, id):
#         pass
#     
# class UsersView:    
#     pass

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
        obj = dict(obj.items() + {k:request.form[k].strip() for k in request.form.keys() if k in var_names}.items())
    else:
        obj = dict(obj.items() + json.items())
    return obj

@app.route('/')
def index():
    issues = None
    if is_logged_in():
        issues = Issue.get_issues_by_user(get_current_user())
        for i in issues:
            i['complaint_count'] = sum(i['reporters'].values())
            i['img_filename'] = get_full_filename_from_url(i['img_url'])
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

# make sure to hide this for production site
@app.route('/clear', methods=['GET'])
def clear_all():
    mongo.db.issues.drop()
    return redirect(url_for('index'))

@app.route('/new-issue', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def new_issue():
    if request.method == 'POST':
        return _post_issue(success_redirect_name='index', error_template='new_issue.html')
    else:
        issue = {k:'' for k in Issue.var_names}
        return make_response(render_template('new_issue.html', error=None, issue=issue))
            
@app.route('/issues', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def issues():
    if request.method == 'GET':
        issues = Issue.get_issues_by_params(params=None)
        for i in issues:
            i['complaint_count'] = sum(i['reporters'].values())
            i['img_filename'] = get_full_filename_from_url(i['img_url'])
        return render_template('issues.html', issues=issues)
    elif request.method == 'POST':
        return _post_issue(success_redirect_name='issues', error_template='issues.html')
    else:
        return ''
        
@app.route('/issue/<issueid>', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*')
def issue(issueid):
    if request.method == 'GET':
        issue = mongo.db.users.find_one({'_id': ObjectId(issueid)})
        issue['complaint_count'] = sum(issue['reporters'].values())
        issue['img_filename'] = get_full_filename_from_url(issue['img_url'])
        return render_template('issue.html', issue=issue)
    else:
        return ''

def _post_issue(success_redirect_name='index', error_template='new_issue.html'):
    error = None
    respond_with_json = request_wants_json(request)
    issue = get_object_by_form_or_json(Issue.var_names)
    if not issue['page_url']:
        error = "Please enter the URL for the web page containing the image."
    else:
        if not issue['img_url']:
            error = "Please enter the URL for the image file."
    if error is None:
        if is_logged_in():        
            reporter_user_id = session['user_id']
        elif issue['creator']:
            reporter_user_id = issue['creator']
        else:
            reporter_user_id = None
        issue = Issue.add_or_update_issue(reporter_user_id, issue)
        if respond_with_json:
            return smart_jsonify(issue)
        else:
            flash('The image was successfully reported.')
            return redirect(url_for(success_redirect_name))
    else:
        if respond_with_json:
            return smart_jsonify(error=error)
        else:
            return make_response(render_template(error_template, error=error, issue=issue))

@app.route('/account', methods=['GET', 'POST', 'OPTIONS'])
def account():
    user = get_current_user()
    if user is None:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        n_user = get_object_by_form_or_json(['disability', 'organization'])
        user['disability'] = n_user['disability']
        user['organization'] = n_user['organization']
        Issue.mongo.db.users.update({'_id': user['_id']}, user, True)
        
    return render_template('account.html', user=user)
    

@app.route('/user/<userid>')
@crossdomain(origin='*')
def user_profile(userid):
    user = mongo.db.users.find_one_or_404({'_id': userid})
    return render_template('user.html', user=user)
        
# extra global helper functions for templating engine
app.jinja_env.globals['is_logged_in'] = is_logged_in

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

# set debugging status of the app
app.debug = True

if __name__ == '__main__':
    app.run()