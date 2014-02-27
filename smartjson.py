#from http://flask.pocoo.org/mailinglist/archive/2011/3/27/extending-jsonify/#091b3eeebb8460390614ac4fae81d972
from flask import Response
import datetime

try:
    import json
except ImportError:
    import simplejson as json

try:
    from bson.objectid import ObjectId
except:
    pass

class APIEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.ctime()
        elif isinstance(obj, datetime.time):
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def smart_jsonify(data):
    return Response(json.dumps(data, cls=APIEncoder),
mimetype='application/json')

# from http://flask.pocoo.org/snippets/45/
def request_wants_json(request):
    
    # If the request sends JSON, assume it wants JSON in the response 
    if request.get_json() is not None:
        return True
    
    # check the Accept header
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']