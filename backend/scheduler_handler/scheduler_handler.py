import os
from apscheduler.events import EVENT_ALL
from backend.common.loghandler import SchedulerLog
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler


class MyBackgroundScheduler(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, )
        return cls._instance

    def __init__(self):
        jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///localDatabase/ericic/jobs.sqlite'), }
        executors = {'default': ThreadPoolExecutor(20), }
        job_defaults = {'coalesce': False, 'max_instances': 1}
        self.scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults,
                                             timezone='Asia/Shanghai')
        self.scheduler.add_listener(self.my_listener, EVENT_ALL)

    def my_listener(self, event):
        pid = os.getpid()
        code = event.code
        # print(dir(event))
        if code == 2 ** 0:  # scheduler start
            SchedulerLog.info('pid: %s # scheduler start' % pid)
        elif code == 2 ** 1:  # scheduler shutdown
            SchedulerLog.info('pid: %s # scheduler shutdown' % pid)
        elif code == 2 ** 2:  # scheduler paused
            SchedulerLog.info('pid: %s # scheduler paused' % pid)
        elif code == 2 ** 3:  # scheduler resumed
            SchedulerLog.info('pid: %s # scheduler resumed' % pid)
        elif code == 2 ** 4:  # executor added
            SchedulerLog.info('pid: %s # executor added' % pid)
        elif code == 2 ** 5:  # executor removed
            SchedulerLog.info('pid: %s # executor removed' % pid)
        elif code == 2 ** 6:  # job store added
            SchedulerLog.info('pid: %s # job store added' % pid)
        elif code == 2 ** 7:  # job store removed
            SchedulerLog.info('pid: %s # job store removed' % pid)
        elif code == 2 ** 8:  # all job removed
            SchedulerLog.info('pid: %s # all job removed' % pid)
        elif code == 2 ** 9:  # job added
            SchedulerLog.info('pid: %s #  job added --> %s' % (pid, event.job_id))
        elif code == 2 ** 10:  # job removed
            SchedulerLog.info('pid: %s # job removed --> %s' % (pid, event.job_id))
        elif code == 2 ** 11:  # job modified
            SchedulerLog.info('pid: %s # job modified --> %s' % (pid, event.job_id))
        elif code == 2 ** 12:  # job executed
            SchedulerLog.info('pid: %s # job executed --> %s' % (pid, event.job_id))
        elif code == 2 ** 13:  # job error
            SchedulerLog.info('pid: %s # ' % pid + event.exception + ' --> %s' % event.job_id)
        elif code == 2 ** 14:  # job missed
            SchedulerLog.info('pid: %s # job missed --> %s' % (pid, event.job_id))
        elif code == 2 ** 15:  # job submitted
            SchedulerLog.info('pid: %s # job submitted' % pid)
        elif code == 2 ** 16:  # job max instances
            SchedulerLog.info('pid: %s # job max instances')

    # the scheduler's job trigger is only support interval for now
    def add_distributed_job(self, job_func, task_id, seconds, args):
        pass

    def _task_lock(self, func):

        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        return inner


SCHEDULER = MyBackgroundScheduler()
