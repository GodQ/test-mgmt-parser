from uuid import uuid4
import json

from elasticsearch_dsl import Document, Keyword, Text
from passlib.apps import custom_app_context as pwd_context
import config.es_connection


class User(Document):
    id = Keyword()
    user_name = Text()
    password_hash = Text()

    class Index:
        name = 'users'

    def init_user_id(self, user_id=None):
        if user_id:
            self.id = user_id
        else:
            self.id = uuid4()

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class BadRequest(Exception):
    pass


class DuplicatedUserName(Exception):
    pass


def list_users():
    users = User.search().execute().hits
    ret = list()
    for user in users:
        d = user.to_dict()
        d['password_hash'] = '******'
        ret.append(d)
    return ret


def create_user(user_name, password):
    if not user_name:
        raise BadRequest('No user_name!!')
    search_result = User.search().filter('term', user_name=user_name).execute()
    if search_result.hits.total.value > 0:
        raise DuplicatedUserName(f'Duplicated user name "{user_name}"')
    user = User(user_name=user_name)
    user.init_user_id(user_name)
    user.hash_password(password)
    user.save()
    return user


def load_user_by_name(user_name):
    if not user_name:
        raise BadRequest('No user_name!!')
    users = User.search().filter('term', user_name=user_name).execute().hits
    if len(users) == 0:
        raise BadRequest(f'There is no user named "{user_name}"')
    if len(users) > 1:
        raise BadRequest(f'There are too many users named "{user_name}"')
    user = users[0]
    return user


def init_user_index():
    User.init()
    create_user('root', 'password')

# init_user_index()
