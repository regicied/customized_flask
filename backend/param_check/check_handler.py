from backend.customer.myCustomer import ParamCheckBase


class LoginCheck(ParamCheckBase):

    def post(self, *args, **kwargs):
        print('login check test')
