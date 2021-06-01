#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @File  : scheduler_task.py
# @Author: gaofzhan
# @Email: gaofeng.a.zhang@ericssoin.com
# @Date  : 2020/12/10 14:40
# @Desc  :
import os
import time
import uuid
import datetime
import redis_lock
from celeryFolder.celery_app import celery_app
from backend.Model.connection import SESSION
from backend.common.redisHandler import LOCK_RDS
from backend.common.loghandler import SchedulerLog
from backend.myException.myExecption import MyError
from backend.scheduler_handler.scheduler_handler import SCHEDULER
from backend.myBluePrint.ericic_v2.model.data_center_table import DataCenterModel
from backend.myBluePrint.ericic_v2.model.refresh_task_history_table import RefreshTaskHistoryModel
from backend.myBluePrint.ericic_v2.model.db_refresh_task import DBRefreshTaskModel


class SchedulerTask:

    @classmethod
    def db_refresh_job(cls, dc_id, job_name, data_init=False):
        job_id = '%s:%s' % (dc_id, uuid.uuid4().hex)

        def _inner(_dc_id, _job_id, _job_name, _dc_entity, _db_session, expire):
            task_history = RefreshTaskHistoryModel(_job_id, _job_name, _dc_id, _dc_entity.name, 'waiting', None,
                                                   int(time.time()))
            _db_session.add(task_history)
            try:
                expire = int(expire)
                celery_app.send_task(_job_name.replace(':', '.'), task_id=_job_id, args=(_dc_id,), expires=expire)
            except Exception as e:
                _db_session.query(RefreshTaskHistoryModel).filter(RefreshTaskHistoryModel.id == _job_id).update(
                    {'status': 'error', 'error_info': str(e)}
                )

        db_session = SESSION()
        try:
            task_id = '%s:%s' % (dc_id, job_name)
            dc_entity = db_session.query(DataCenterModel).filter(DataCenterModel.id == dc_id).one_or_none()
            task_entity = db_session.query(DBRefreshTaskModel).filter(DBRefreshTaskModel.id == task_id).one_or_none()
            if dc_entity and task_entity:
                start, end = task_entity.start, task_entity.end
                # interval = task_entity.interval
                job_entity = SCHEDULER.scheduler.get_job(task_id)
                # if the mission is not init function and can not find the job_entity as well,
                # it's means that the job may be stopped by the user, so the data refresh job will not exec
                if not job_entity and not data_init:
                    raise MyError('this job should be passed')
                next_run_time = 'init' if data_init else str(job_entity.next_run_time)
                now = datetime.datetime.now()
                hour, minute, second = now.hour, now.minute, now.second
                now_int = int(hour) * 3600 + int(minute) * 60 + int(second)
                if ((start <= now_int) and (now_int <= end)) or data_init:
                    lock_key = '{dc_id}:{func_name}:{nr_time}'.format(dc_id=dc_id, func_name=job_name,
                                                                      nr_time=next_run_time)
                    SchedulerLog.info('pid: %s # try to get lock --> %s' % (os.getpid(), lock_key))
                    lock = redis_lock.Lock(LOCK_RDS, lock_key, expire=task_entity.interval)
                    try:
                        if lock.acquire(blocking=False):
                            SchedulerLog.info('pid: %s # successfully get lock --> %s' % (os.getpid(), lock_key))
                            try:
                                _inner(dc_id, job_id, job_name, dc_entity, db_session, task_entity.interval * (3 / 4))
                                db_session.commit()
                            except Exception as e:
                                db_session.rollback()
                                raise e
                            finally:
                                # !!! the lock should be released by the expire time, can not release by itself
                                # lock.release()
                                pass
                        else:
                            SchedulerLog.info('pid: %s # Failed to get the lock --> %s' % (os.getpid(), lock_key))
                    finally:
                        LOCK_RDS.close()
                else:
                    SchedulerLog.info('pid: %s # this job is not in the runtime range' % os.getpid())
        except MyError:
            SchedulerLog.info('pid: %s # this job should be passed' % os.getpid())
        finally:
            db_session.close()
