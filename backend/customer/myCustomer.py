import uuid
import traceback
from flask import request, g
from functools import wraps
from backend.myException.myExecption import *
# from flask.views import MethodView
from flask.views import View
from flask._compat import with_metaclass
# from flask.sessions import *
# from backend.common.redisHandler import rds
from backend.customer.paramCheck import ParamCheckBase
from backend.common.loghandler import RequestLog, ServiceLog

# from flask.globals import request as g_request

# class MyRedisSessionInterface(SessionInterface):
#     """The default session interface that stores sessions in signed cookies
#     through the :mod:`itsdangerous` module.
#     """
#
#     #: the salt that should be applied on top of the secret key for the
#     #: signing of cookie based sessions.
#     salt = "cookie-session"
#     #: the hash function to use for the signature.  The default is sha1
#     digest_method = staticmethod(hashlib.sha1)
#     #: the name of the itsdangerous supported key derivation.  The default
#     #: is hmac.
#     key_derivation = "hmac"
#     #: A python serializer for the payload.  The default is a compact
#     #: JSON derived serializer with support for some extra Python types
#     #: such as datetime objects or tuples.
#     serializer = session_json_serializer
#     session_class = SecureCookieSession
#
#     def get_signing_serializer(self, app):
#         if not app.secret_key:
#             return None
#         signer_kwargs = dict(
#             key_derivation=self.key_derivation, digest_method=self.digest_method
#         )
#         return URLSafeTimedSerializer(
#             app.secret_key,
#             salt=self.salt,
#             serializer=self.serializer,
#             signer_kwargs=signer_kwargs,
#         )
#
#     def open_session(self, app, _request):
#         s = self.get_signing_serializer(app)
#         if s is None:
#             return None
#         # val = request.cookies.get(app.session_cookie_name)
#         sid = _request.cookies.get(app.session_cookie_name)
#         if not sid:
#             return self.session_class()
#         max_age = total_seconds(app.permanent_session_lifetime)
#
#         val = rds.get(sid) if rds.get(sid) else dict()
#         try:
#             data = s.loads(val, max_age=max_age)
#             return self.session_class(data)
#         except BadSignature:
#             return self.session_class()
#
#     def save_session(self, app, session, response):
#         sid = request.cookies.get(app.session_cookie_name, str(uuid.uuid4().hex))
#         domain = self.get_cookie_domain(app)
#         path = self.get_cookie_path(app)
#
#         # If the session is modified to be empty, remove the cookie.
#         # If the session is empty, return without setting the cookie.
#         if not session:
#             if session.modified:
#                 response.delete_cookie(
#                     app.session_cookie_name, domain=domain, path=path
#                 )
#                 rds.delete(sid)
#
#             return
#
#         # Add a "Vary: Cookie" header if the session was accessed at all.
#         if session.accessed:
#             response.vary.add("Cookie")
#
#         if not self.should_set_cookie(app, session):
#             return
#
#         if not session.modified:
#             return
#         httponly = self.get_cookie_httponly(app)
#         secure = self.get_cookie_secure(app)
#         samesite = self.get_cookie_samesite(app)
#         expires = self.get_expiration_time(app, session)
#         val = self.get_signing_serializer(app).dumps(dict(session))
#         rds.set(sid, val, ex=expires)
#         response.set_cookie(
#             app.session_cookie_name,
#             sid,
#             expires=expires,
#             httponly=httponly,
#             domain=domain,
#             path=path,
#             secure=secure,
#             samesite=samesite,
#         )


http_method_funcs = frozenset(
    ["get", "post", "head", "options", "delete", "put", "trace", "patch"]
)


class MethodViewType(type):
    """Metaclass for :class:`MethodView` that determines what methods the view
    defines.
    """

    def __new__(mcs, *args, **kwargs):
        name, base, attrs = args
        check_cls = attrs.get('check_cls')
        if check_cls:
            assert isinstance(check_cls(), ParamCheckBase), 'check_cls must based on ParamCheckBase'
            for method in http_method_funcs:
                if method in attrs:
                    check_func = getattr(check_cls, method, None)
                    if check_func:
                        attrs[method] = mcs.check_dec(attrs[method], check_func)
        _args = (name, base, attrs)
        return type.__new__(mcs, *_args, **kwargs)

    def __init__(cls, name, bases, d):
        super(MethodViewType, cls).__init__(name, bases, d)

        if "methods" not in d:
            methods = set()

            for base in bases:
                if getattr(base, "methods", None):
                    methods.update(base.methods)

            for key in http_method_funcs:
                if hasattr(cls, key):
                    methods.add(key.upper())

            # If we have no method at all in there we don't want to add a
            # method list. This is for instance the case for the base class
            # or another subclass of a base method view that does not introduce
            # new methods.
            if methods:
                cls.methods = methods

    @classmethod
    def check_dec(mcs, view_method, check_method):
        @wraps(view_method)
        @wraps(check_method)
        def inner(*args, **kwargs):
            check_method(*args, **kwargs)
            return view_method(*args, **kwargs)

        return inner


class MethodView(with_metaclass(MethodViewType, View)):
    """A class-based view that dispatches request methods to the corresponding
    class methods. For example, if you implement a ``get`` method, it will be
    used to handle ``GET`` requests. ::

        class CounterAPI(MethodView):
            def get(self):
                return session.get('counter', 0)

            def post(self):
                session['counter'] = session.get('counter', 0) + 1
                return 'OK'

        app.add_url_rule('/counter', view_func=CounterAPI.as_view('counter'))
    """

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        assert meth is not None, "Unimplemented method %r" % request.method
        return meth(*args, **kwargs)


class APiMethodView(MethodView):
    check_cls = ParamCheckBase

    def dispatch_request(self, *args, **kwargs):
        request_id = str(uuid.uuid4().hex)
        g.r_id = request_id
        _msg = 'success'
        try:
            self.request = request
            meth = getattr(self, request.method.lower(), None)
            # If the request method is HEAD and we don't have a handler for it
            # retry with GET.
            if meth is None and request.method == "HEAD":
                meth = getattr(self, "get", None)
            assert meth is not None, "Unimplemented method %r" % request.method
            # assert meth is not None, Exception('xxxx')
            res = meth(*args, **kwargs)
            return res
        except NotImplementedError:
            code = 405
            return dict(code=405, status=False, message='Unimplemented method'), code
        except MyParamCheckError as e:
            code = 400
            return dict(code=code, status=False, message=e.msg), code
        except MyRuntimeError as e:
            _msg = e.msg
            code = e.code
            return dict(code=code, status=False, message=_msg), code
        except MyError as e:
            _msg = e.msg
            return dict(code=503, status=False, message=_msg), 503
        except Exception:
            _msg = traceback.format_exc()
            ServiceLog.error('%s - %s' % (g.r_id, _msg))
            code = 500
            return dict(code=500, status=False), code
        finally:
            RequestLog.info('%s - %s - %s - %s' % (g.r_id, request.host, request.url, request.method))

    def get(self, *args, **kwargs):
        raise NotImplementedError()

    def post(self, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, *args, **kwargs):
        raise NotImplementedError()

    def put(self, *args, **kwargs):
        raise NotImplementedError()
