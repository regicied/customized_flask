import os
import time
from flask import g
from config import *
from functools import wraps
from multiprocessing import Event
from multiprocessing import Process
from redis import Redis, ConnectionPool

# Reference:  http://redis.io/topics/distlock
# Section Correct implementation with a single instance


TOKEN_POOL = ConnectionPool(host=REDIS_HOST, password=REDIS_PASS, port=REDIS_PORT, decode_responses=True, db=0)
TOKEN_RDS = Redis(connection_pool=TOKEN_POOL)

CACHE_POOL = ConnectionPool(host=REDIS_HOST, password=REDIS_PASS, port=REDIS_PORT, decode_responses=True, db=1)
CACHE_RDS = Redis(connection_pool=CACHE_POOL)

LOCK_POOL = ConnectionPool(host=REDIS_HOST, password=REDIS_PASS, port=REDIS_PORT, decode_responses=True, db=2)
LOCK_RDS = Redis(connection_pool=LOCK_POOL)



JOB_ID_KEY = "excel_cache:"


class LockHandler:
    lock_expire = 5
    lock_names = dict()

    RELEASE_LUA_SCRIPT = """
        if redis.call("get",KEYS[1]) == ARGV[1] then
            return redis.call("del",KEYS[1])
        else
            return 0
        end
    """

    @classmethod
    def func_lock(cls, func):
        @wraps(func)
        def inner(*args, **kwargs):

            func_name = func.__name__
            try:
                request_id = g.r_id
            except Exception:
                request_id = os.getpid()
            loop = 0
            while not LOCK_RDS.set(func_name, request_id, nx=True, ex=cls.lock_expire):
                pending_time = cls.lock_expire / 2 - (loop / 10) * cls.lock_expire
                if pending_time >= (cls.lock_expire / 3):
                    pending_time = pending_time
                else:
                    pending_time = cls.lock_expire / 3
                time.sleep(pending_time)
            lock_event = Event()
            p = Process(target=cls.lock_watcher, args=(lock_event, func_name))
            p.daemon = True
            p.start()
            res = func(*args, **kwargs)
            if LOCK_RDS.get(func_name) == str(request_id):
                LOCK_RDS.delete(func_name)
            return res

        return inner

    @classmethod
    def lock_watcher(cls, lock_event, key):
        while not lock_event.is_set():
            time.sleep(3 * cls.lock_expire / 4)
            LOCK_RDS.expire(key, cls.lock_expire)

    @classmethod
    def distribute_transaction(cls, lock_key, call_back=None):
        def func_acceptor(func):
            @wraps(func)
            def inner(*args, **kwargs):

                func_name = func.__name__
                try:
                    request_id = g.r_id
                except Exception:
                    request_id = os.getpid()
                loop = 0
                while not LOCK_RDS.set(func_name, request_id, nx=True, ex=cls.lock_expire):
                    pending_time = cls.lock_expire / 2 - (loop / 10) * cls.lock_expire
                    if pending_time >= (cls.lock_expire / 3):
                        pending_time = pending_time
                    else:
                        pending_time = cls.lock_expire / 3
                    time.sleep(pending_time)
                lock_event = Event()
                p = Process(target=cls.lock_watcher, args=(lock_event, func_name))
                p.daemon = True
                p.start()
                res = func(*args, **kwargs)
                del_script = LOCK_RDS.register_script(cls.RELEASE_LUA_SCRIPT)
                if del_script(keys=[func_name, ], args=[request_id, ]):
                    pass
                return res

            return inner

        return func_acceptor
