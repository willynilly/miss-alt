from datetime import timedelta
from flask import make_response, request, current_app, Response
from functools import update_wrapper

# adapted from http://flask.pocoo.org/snippets/56/
def crossdomain(origin=None):    
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    def decorator(f):
        def wrapped_function(*args, **kwargs):            
            if request.method == 'OPTIONS':
                resp = Response(status=200,
                                mimetype="application/json")
                resp.headers['Access-Control-Allow-Origin'] = '*'
                resp.headers['Access-Control-Allow-Methods'] = 'HEAD,GET,POST,PUT,DELETE,OPTIONS' #'HEAD,GET,POST,PUT,DELETE,OPTIONS'
                resp.headers['Access-Control-Max-Age'] = '1000'
                # note that '*' is not valid for Access-Control-Allow-Headers
                resp.headers['Access-Control-Allow-Headers'] = 'origin, x-csrftoken, content-type, accept'
                return resp
            else:
                resp = make_response(f(*args, **kwargs))
                resp.headers['Access-Control-Allow-Origin'] = origin
                return resp
        return update_wrapper(wrapped_function, f)
    return decorator