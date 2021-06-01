import uuid
import sqlite3
from config import *
from flask import make_response
from backend.Model.UserModel import User
from sqlalchemy.exc import IntegrityError
from backend.common.tokenHandler import AccessToken, RefreshToken
from itsdangerous.exc import SignatureExpired, BadSignature


class LoginService:

    @classmethod
    def authentication(cls, name, password):
        judge_status = User.authentication(name, password)
        if judge_status:
            info = dict(name=name)
            access_token = AccessToken.gen_token(info)
            refresh_token = RefreshToken.gen_refresh_token(info)
            res = {
                'status': True,
                'data': {
                    'access_token': access_token,
                    'expires_in': ACCESS_TIME,
                    'refresh_token': refresh_token,
                    'time': REFRESH_TIME
                },
                'code': 200
            }
        else:
            res = dict(status=False, code=401)
        return res


class RefreshService:

    @classmethod
    def refresh_access_token(cls, refresh_token):
        try:
            access_token = RefreshToken.refresh_authentication(refresh_token)
            res = dict(status=True, data=dict(access_token=access_token, expires_in=ACCESS_TIME), code=200)
        except SignatureExpired:
            res = make_response(dict(status=False, code=401, message='token expired')), 401
        except BadSignature:
            res = make_response(dict(status=False, code=401, message='bad token')), 401
        return res


class SignService:

    @classmethod
    def sign_func(cls, name, password):
        user = User(uuid.uuid4().hex, name, password)
        try:
            user.add()
            res = make_response(dict(status=True, code=201)), 201
        except IntegrityError:
            res = make_response(dict(status=False, code=400, message='Duplicate name')), 400
        return res


class LogoutService:

    @classmethod
    def logout_func(cls, refresh_token):
        try:
            token_info = RefreshToken.load_token(refresh_token)
        except SignatureExpired:
            return make_response(dict(status=True, code=200)), 200
        except BadSignature:
            return make_response(dict(status=False, code=400, message='bad token')), 400
        refresh_id = token_info['token_id']
        con = sqlite3.connect('localDatabase/refresh_token.db', check_same_thread=False)
        try:
            cur = con.cursor()
            cur.execute('delete from refresh where id = "%s"' % refresh_id)
            con.commit()
        except Exception:
            con.rollback()
        finally:
            con.close()
        return make_response(dict(status=True, code=200)), 200
