from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask import g
from common.user_model import User, BadRequest, DuplicatedUserName, load_user_by_name
from config.config import Config
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature

basic_auth = HTTPBasicAuth(scheme='NoAction')
token_auth = HTTPTokenAuth(scheme='Bearer')
auth = MultiAuth(basic_auth, token_auth)


def generate_auth_token(user: User, expiration=24 * 60 * 60):
    s = Serializer(Config.get_config('SECRET_KEY'), expires_in=expiration)
    return s.dumps({'user_name': user.user_name})


def get_user(token):
    user = verify_auth_token(token)
    return user


def get_user_role(auth):
    role = g.user.role
    print(role)
    return role


@basic_auth.get_user_roles
def get_user_roles_cb(auth):
    return get_user_role(auth)


@token_auth.get_user_roles
def get_user_roles_cb(auth):
    return get_user_role(auth)


def verify_auth_password(user_name, password):
    try:
        user = load_user_by_name(user_name)
        if user.verify_password(password):
            return user
        else:
            return None
    except Exception as e:
        return None


def verify_auth_token(token):
    s = Serializer(Config.get_config('SECRET_KEY'))
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None  # valid token, but expired
    except BadSignature:
        return None  # invalid token
    try:
        user = load_user_by_name(data['user_name'])
        return user
    except Exception as e:
        return None


@basic_auth.verify_password
def verify_password_cb(user_name, password):
    try:

        user = verify_auth_password(user_name, password)
        if not user:
            return False
        print(user)
        g.user = user
        return True
    except Exception as e:
        print(e)
        return False


@token_auth.verify_token
def verify_token_cb(token):
    try:
        user = verify_auth_token(token)
        if not user:
            return False
        print(user)
        g.user = user
        return True
    except Exception as e:
        print(e)
        return False

