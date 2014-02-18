miss-alt
========

Installation For Mac
--------------------

Install homebrew:

http://brew.sh/

Using homebrew, install mongodb:
http://docs.mongodb.org/manual/tutorial/install-mongodb-on-os-x/

```
brew update
brew install mongodb
```

Make sure you have Python 2.7.6 installed:

```
python --version
```

Use the Python package manager pip to install Flask:
http://flask.pocoo.org/

```
pip install flask
```

Use pip to install PyMongo:
http://api.mongodb.org/python/current/installation.html

```
pip install pymongo
```

Open a new tab in Terminal and start mongodb:
```
mongod
```

Open a new tab in Terminal, clone the application repo and run the application:
```
git clone https://github.com/willynilly/miss-alt.git
cd miss-alt
python application.py
```
