from flask import request
from backend.customer.paramCheck import ParamCheckBase
from backend.myException.myExecption import MyKeyError


class SignCheck(ParamCheckBase):

    def post(self, *args, **kwargs):
        body = request.get_json()
        try:
            body['password']
            body['name']
        except KeyError as key:
            raise MyKeyError(key)


class RefreshCheck(ParamCheckBase):

    def post(self, *args, **kwargs):
        body = request.get_json()
        try:
            body['refresh_token']
        except KeyError as key:
            raise MyKeyError(key)


class LogoutCheck(ParamCheckBase):

    def post(self, *args, **kwargs):
        body = request.get_json()
        try:
            body['refresh_token']
        except KeyError as key:
            raise MyKeyError(key)


class LoginCheck(ParamCheckBase):

    def post(self, *args, **kwargs):
        body = request.get_json()
        try:
            body['password']
            body['name']
        except KeyError as key:
            raise MyKeyError(key)
