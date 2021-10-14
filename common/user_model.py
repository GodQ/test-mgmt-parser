from uuid import uuid4
import json
from config.config import Config
from app_init import db

from elasticsearch_dsl import Document, Keyword, Text
from passlib.apps import custom_app_context as pwd_context
import config.es_connection

default_role = 'developer'
role_set = ['admin', 'developer', 'viewer']


class User(db.Model):
    id = db.Column(db.Integer, unique=True)
    user_name = db.Column(db.String(80), primary_key=True)
    password_hash = db.Column(db.String(800))
    role = db.Column(db.String(80))

    def __init__(self, user_name):
        self.user_name = user_name
        self.set_role(default_role)

    def to_dict(self):
        t = {
            'id': self.id,
            'user_name': self.user_name,
            'role': self.role,
        }
        return t

    def set_user_id(self, user_id=None):
        if user_id:
            self.id = user_id
        else:
            self.id = uuid4()

    def set_role(self, role=None):
        if role not in role_set:
            raise Exception(f"role must be in {role_set}")
        self.role = role

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class BadRequest(Exception):
    pass


class DuplicatedUserName(Exception):
    pass


class NotExistUserName(Exception):
    pass


def list_users():
    users = User.query.all()
    ret = list()
    for user in users:
        d = user.to_dict()
        d['password_hash'] = '******'
        ret.append(d)
    return ret


def add_user(user_name, password, role=None):
    if not user_name:
        raise BadRequest('No user_name!!')
    search_result = User.query.filter_by(user_name=user_name).first()
    if search_result:
        raise DuplicatedUserName(f'Duplicated user name "{user_name}"')
    user = User(user_name=user_name)
    user.set_user_id(user_name)
    user.set_role(role)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def delete_user(user_name):
    if not user_name:
        raise BadRequest('No user_name!!')
    search_result = User.query.filter_by(user_name=user_name).delete()
    db.session.commit()
    return search_result


def load_user_by_name(user_name):
    if not user_name:
        raise BadRequest('No user_name!!')
    user = User.query.filter_by(user_name=user_name).first()
    if not user:
        raise BadRequest(f'There is no user named "{user_name}"')
    return user

