import time
import uuid
import sqlite3
import itsdangerous
from config import *
from itsdangerous.exc import BadSignature, SignatureExpired
from backend.common.redisHandler import TOKEN_RDS


class TokenHandler:
    salt = None
    expires = None
    ids = itsdangerous.TimedJSONWebSignatureSerializer(salt, expires_in=expires)

    @classmethod
    def gen_token(cls, info):
        info['token_id'] = info['token_id'] if info.get('token_id') else str(uuid.uuid4().hex)
        info['expires_in'] = cls.expires if info.get('expires_in') else cls.expires
        return cls.ids.dumps(info).decode()

    @classmethod
    def load_token(cls, token):
        info = cls.ids.loads(token)
        return info


class AccessToken(TokenHandler):
    salt = ACCESS_SALT
    expires = ACCESS_TIME
    ids = itsdangerous.TimedJSONWebSignatureSerializer(salt, expires_in=expires)


class RefreshToken(TokenHandler):
    salt = REFRESH_SALT
    expires = REFRESH_TIME
    ids = itsdangerous.TimedJSONWebSignatureSerializer(salt, expires_in=expires)
    base_db = REFRESH_BASE

    @classmethod
    def refresh_authentication(cls, refresh):
        refresh_info = cls.load_token(refresh)
        refresh_id = refresh_info.get('token_id')
        # name = refresh_info.get('name')
        if cls.base_db == 'sqlite':
            con = sqlite3.connect('localDatabase/refresh_token.db', check_same_thread=False)
            try:
                cur = con.cursor()
                res = cur.execute("select * from refresh where id = '%s'" % refresh_id).fetchone()
                if res:
                    rid, name, expires = res
                    now = int(time.time())
                    if now > expires:
                        try:
                            cur.execute('delete from refresh where id = "%s"' % refresh_id)
                            con.commit()
                        except:
                            con.rollback()
                        raise SignatureExpired('token expires')
                    else:
                        info = {'name': refresh_info.get('name')}
                        access_token = AccessToken.gen_token(info)
                else:
                    raise BadSignature('no refresh token in server')
            finally:
                con.close()
        else:
            try:
                # todo: implement the logic base on redis
                # raise NotImplemented()
                res = TOKEN_RDS.get(name='ref_%s' % refresh_id)
                if res:
                    info = {'name': refresh_info.get('name')}
                    access_token = AccessToken.gen_token(info)
                else:
                    raise BadSignature('no refresh token in server')
            finally:
                TOKEN_RDS.close()
        return access_token

    @classmethod
    def gen_refresh_token(cls, info):
        refresh_id = str(uuid.uuid4().hex)
        expires = cls.expires + int(time.time())
        name = info['name']
        info['expires_in'] = expires
        info['token_id'] = refresh_id
        refresh_token = cls.gen_token(info)
        if cls.base_db == 'sqlite':
            con = sqlite3.connect('localDatabase/refresh_token.db', check_same_thread=False)
            try:
                cur = con.cursor()
                cur.execute('insert into refresh values ("%s", "%s", %s)' % (refresh_id, name, expires))
                con.commit()
            except Exception:
                con.rollback()
                raise
            finally:
                con.close()
        else:
            TOKEN_RDS.set(name='ref_%s' % refresh_id, value=name, ex=cls.expires)
            # raise NotImplemented()
        return refresh_token
