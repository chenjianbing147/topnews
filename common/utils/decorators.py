from functools import wraps

from flask import g

def login_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.userid:
            return f(*args, **kwargs)
        else:
            return {'message': 'Invalid Token', 'data':None}, 401

    return wrapper
