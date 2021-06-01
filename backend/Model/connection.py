import time
import pymysql
import traceback
from flask import g
from sqlalchemy.exc import IntegrityError
from backend.common.loghandler import BDLog
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_NAME, MYSQL_PASS
from sqlalchemy import create_engine, or_, and_
from sqlalchemy import Column, String, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.myException.myExecption import MyRuntimeError

pymysql.install_as_MySQLdb()

con_uri = 'mysql://%s:%s@%s:%s/%s?charset=utf8' % (MYSQL_NAME, MYSQL_PASS, MYSQL_HOST, MYSQL_PORT, MYSQL_DB)

engine = create_engine(con_uri, pool_recycle=3600, pool_pre_ping=True, echo=False)

BASE = declarative_base()
SESSION = sessionmaker(bind=engine, autoflush=True)
NO_FLUSH_SESSION = sessionmaker(bind=engine, autoflush=False)

# todo : the following architect should write a request scope db session
# db_session = SESSION()


class BaseView(BASE):
    __abstract__ = True

    timestamp = Column(Integer(), nullable=False, onupdate=func.now())

    @classmethod
    def count(cls):
        db_session = SESSION()
        try:
            res = db_session.query(cls).count()
        finally:
            db_session.close()
        return res

    @classmethod
    def select_all(cls):
        db_session = SESSION()
        try:
            res = db_session.query(cls).all()
        finally:
            db_session.close()
        return res

    @classmethod
    def _gen_query_entity(cls, query_dict, ):
        and_entity_list = list()
        for k, v in query_dict.items():
            filter_attr = getattr(cls, k, None)
            if not filter_attr:
                continue
            or_entity_list = list()
            if type(v) == list:
                for query_like in v:
                    filter_entity = filter_attr.like('%{query}%'.format(query=query_like))
                    or_entity_list.append(filter_entity)
            elif type(v) == tuple:
                for query_is in v:
                    filter_entity = (filter_attr == query_is)
                    or_entity_list.append(filter_entity)
            or_entity = or_(*or_entity_list)
            and_entity_list.append(or_entity)
        filter_args = and_(*and_entity_list)
        return filter_args

    @classmethod
    def split_data_by_query(cls, column_list, query_dict, offset, limit, sort_list, order):
        db_session = SESSION()
        column_args = list()
        for column in column_list:
            entity = getattr(cls, column, None)
            if not entity:
                continue
            column_args.append(entity)
        filter_args = cls._gen_query_entity(query_dict, )
        sort_entity_list = [getattr(cls, sort) if getattr(cls, sort, None) else cls.timestamp for sort in sort_list]
        order_entities = [sen.asc() if order == 'asc' else sen.desc() for sen in sort_entity_list]
        try:
            res = db_session.query(cls).with_entities(*column_args).filter(filter_args).order_by(
                *order_entities).offset(offset).limit(limit).all()
        finally:
            db_session.close()
        return res

    @classmethod
    def count_data_by_query(cls, query_dict):
        db_session = SESSION()
        filter_args = cls._gen_query_entity(query_dict, )
        try:
            res = db_session.query(cls).filter(filter_args).count()
        finally:
            db_session.close()
        return res


class MyBase(BaseView):
    __abstract__ = True
    id = Column(String(40), primary_key=True, )
    timestamp = Column(Integer(), nullable=False, onupdate=func.now())
    version = Column(Integer(), nullable=False, default=0)

    def add(self):
        db_session = SESSION()
        try:
            db_session.add(self)
            db_session.commit()
        except IntegrityError as e:
            db_session.rollback()
            raise e
        except Exception:
            db_session.rollback()
            e = traceback.format_exc()
            BDLog.info('%s - %s' % (g.r_id, e))
            raise MyRuntimeError('service error', 503)
        finally:
            db_session.close()

    @classmethod
    def delete_by_id(cls, _id):
        db_session = SESSION()
        try:
            db_session.query(cls).filter(cls.id == _id).delete()
            db_session.commit()
        except Exception:
            db_session.rollback()
            e = traceback.format_exc()
            BDLog.info('%s - %s' % (g.r_id, e))
            raise MyRuntimeError('service error', 503)
        finally:
            db_session.close()

    @classmethod
    def update_by_id(cls, _id, **kwargs):
        _update = {}
        db_session = SESSION()
        try:
            this = db_session.query(cls).filter(cls.id == _id).one_or_none()
            if this:
                for k, v in kwargs.items():
                    if k == 'id' or k == 'version':
                        continue
                    _update[getattr(cls, k)] = v
                _update[cls.version] = this.version + 1
                _update[cls.timestamp] = int(time.time())
                _query = and_(cls.id == _id, cls.version == this.version)
                try:
                    res = db_session.query(cls).filter(_query).update(_update)
                    db_session.commit()
                    if not res:
                        cls.update_by_id(_id, **kwargs)
                except Exception:
                    db_session.rollback()
                    e = traceback.format_exc()
                    BDLog.info('%s - %s' % (g.r_id, e))
                    raise MyRuntimeError('service error', 503)
                return True
            else:
                return False
        finally:
            db_session.close()

    @classmethod
    def get_one_by_id(cls, _id):
        db_session = SESSION()
        try:
            res = db_session.query(cls).filter(cls.id == _id).one_or_none()
        finally:
            db_session.close()
        return res
