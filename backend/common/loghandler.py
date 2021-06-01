import os
import logging
from flask import g
from logging.handlers import RotatingFileHandler


#
# logger = logging.getLogger('app')
# logger.setLevel(level=logging.INFO)
# # 定义一个RotatingFileHandler，最多备份3个日志文件，每个日志文件最大1K
# rHandler = RotatingFileHandler("logs.log", maxBytes=1 * 1024 * 1024, backupCount=3)
# rHandler.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# rHandler.setFormatter(formatter)
#
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# console.setFormatter(formatter)
#
# logger.addHandler(rHandler)
# logger.addHandler(console)


class LogHandler(object):
    dir_name = 'logs'

    def __new__(cls, *args, **kwargs):
        cls.check_dir_existed()
        return object.__new__(cls)

    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level=logging.INFO)
        self.rHandler = RotatingFileHandler("%s/%s.log" % (self.dir_name, name), maxBytes=1 * 1024 * 1024,
                                            backupCount=3)
        self.rHandler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.rHandler.setFormatter(formatter)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        self.logger.addHandler(self.rHandler)
        self.logger.addHandler(console)

    def info(self, info):
        try:
            rid = g.r_id
        except:
            rid = 'fail_trace_rid'
        self.logger.info('%s - %s' % (rid, info))

    def debug(self, info):
        try:
            rid = g.r_id
        except:
            rid = 'fail_trace_rid'
        self.logger.debug('%s - %s' % (rid, info))

    def error(self, info):
        try:
            rid = g.r_id
        except:
            rid = 'fail_trace_rid'
        self.logger.error('%s - %s' % (rid, info))

    @classmethod
    def check_dir_existed(cls):
        if not os.path.exists(cls.dir_name):
            os.mkdir(cls.dir_name)


#
# logger.info("Start print logs")
# logger.debug("Do something")
# logger.warning("Something maybe fail.")
# logger.info("Finish")

RequestLog = LogHandler('api')
BDLog = LogHandler('db')
ServiceLog = LogHandler('service')
RedisLog = LogHandler('redis')
LockLog = LogHandler('lock')
SchedulerLog = LogHandler('scheduler')
