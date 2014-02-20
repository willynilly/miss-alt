from flask import Flask, flash, session, redirect, url_for, escape, request, render_template
from flask.ext.pymongo import PyMongo, ObjectId

import hashlib, uuid
import datetime

app = Flask(__name__)
mongo = PyMongo(app)

@app.route('/')
def index():
    if is_logged_in:
        reports = get_reports_by_user(get_current_user())
    else:
        reports = None
    return render_template('home.html', reports=reports)

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

@app.route('/report', methods=['GET', 'POST'])
def report():
    error = None
    img_url = page_url = img_current_alt_text = img_ideal_alt_text = ""
    if request.method == 'POST':
        page_url = request.form['page_url'].strip()
        if not page_url:
            error = "Please enter the URL for the web page containing the image."
        else:
            img_url = request.form['img_url'].strip()
            if not img_url:
                error = "Please enter the URL for the image file."
            else:
                img_current_alt_text = request.form['img_current_alt_text'].strip()
                img_ideal_alt_text = request.form['img_current_alt_text'].strip()
                report = mongo.db.reports.find_one({'img_url': img_url, 'page_url': page_url})    
                if report is None:
                    report = {"img_url": img_url, "page_url": page_url, "created_on": datetime.datetime.utcnow(), "reporters": []}
                report['img_current_alt_text'] = img_current_alt_text
                report['img_ideal_alt_text'] = img_ideal_alt_text
                if is_logged_in():        
                    reporter = session['user_id']
                else:
                    reporter = None
                report['reporters'].append(reporter)
                report['updated_on'] = datetime.datetime.utcnow()
                mongo.db.reports.update({'img_url': img_url, 'page_url': page_url}, report, True)
                flash('The image was successfully reported.')
                return redirect(url_for('index'))
                
    return render_template('report.html', error=error, page_url=page_url, img_url=img_url, img_current_alt_text=img_current_alt_text, img_ideal_alt_text=img_ideal_alt_text)

def get_hashed_password(password, salt="somesalt"):
    return hashlib.sha512(password + salt).hexdigest()

def is_logged_in():
    return session is not None and 'user_id' in session and session['user_id'] is not None

def get_current_user():
    if is_logged_in():
        return mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    else:
        return None

def get_reports_by_user(user):
    if user is None:
        return None
    else:
        #return mongo.db.reports.find()
        # https://stackoverflow.com/questions/10242149/sorting-with-mongodb-and-python
        return mongo.db.reports.find({'reporters': {'$all': [str(user['_id'])]}}).sort([("created_on", -1)])    
        
# @app.route('/img/<imgid>')
# def img_profile(imgid):
#     user = mongo.db.imgs.find_one_or_404({'_id': imgid})
#     return render_template('img.html',
#         img=img)

app.jinja_env.globals['is_logged_in'] = is_logged_in

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

app.debug = True

if __name__ == '__main__':
    app.run()