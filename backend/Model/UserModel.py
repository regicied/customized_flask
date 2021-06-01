import traceback
from flask import g
from backend.Model.connection import BASE, SESSION
from backend.common.loghandler import BDLog
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, String, Integer
from werkzeug.security import generate_password_hash, check_password_hash


class User(BASE):
    __tablename__ = 'user'

    id = Column(String(40), primary_key=True, )
    name = Column(String(20), nullable=False, unique=True)
    password = Column(String(20), nullable=False)
    version = Column(Integer(), nullable=False, default=0)

    def __init__(self, _id, name, password):
        self.id = _id
        self.name = name
        self.password = generate_password_hash(password)

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
            raise Exception('DB error')
        finally:
            db_session.close()

    @classmethod
    def authentication(cls, name, password):
        db_session = SESSION()
        try:
            user = db_session.query(User).filter(User.name == name).one_or_none()
            if user:
                return check_password_hash(user.password, password)
            else:
                return False
        finally:
            db_session.close()
