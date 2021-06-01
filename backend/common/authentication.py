from functools import wraps
from itsdangerous.exc import SignatureExpired, BadSignature
from backend.common.tokenHandler import AccessToken
from flask import request, make_response, render_template, g


def dec_auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token:
            try:
                access_info = AccessToken.load_token(access_token)
                g.name = access_info.get('name')
                res = func(*args, **kwargs)
            except SignatureExpired:
                res = make_response(dict(code=401, status=False, message='token expires')), 401
            except BadSignature:
                res = make_response(dict(code=401, status=False, message='bad token')), 401
        else:
            path = request.path
            if not path.find('api'):
                res = render_template('index.html')
            else:
                res = make_response(dict(code=401, status=False, message='No authentication')), 401
        return res

    return inner
