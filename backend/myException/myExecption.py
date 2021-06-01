class MyError(Exception):
    msg = None

    def __init__(self, *args, **kwargs):
        pass


class MyRuntimeError(MyError):

    def __init__(self, msg, code):
        self.msg = msg
        self.code = code


# this cls is used to param check error's defining
class MyParamCheckError(MyError):

    def __init__(self, msg):
        self.msg = msg


class MyKeyError(MyParamCheckError):

    def __init__(self, key):
        self.msg = 'key %s is necessary' % key


class MyTypeError(MyParamCheckError):

    def __init__(self, key):
        self.msg = "the type of key %s value is wrong" % key


class MyDataConsistencyError(MyError):

    def __init__(self, msg):
        self.msg = msg


class MySSHError(MyError):

    def __init__(self, msg='unexpected exception'):
        self.msg = '%s, unable to connect the remote host by ssh tunnel' % msg
        self.code = 503


if __name__ == '__main__':
    pass
