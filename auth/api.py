from . import bp
from flask import jsonify, request, make_response, abort, g
import json
import traceback


from auth.model import User, create_user, verify_auth, list_users
from auth.auth import auth


@auth.verify_password
def verify_password(user_name, password):
    # try:
    #     user = verify_auth(user_name, password)
    # except Exception as e:
    #     print(e)
    #     return False
    # print(user)
    # if not user:
    #     return False
    # g.user = user
    return True


@bp.route('/users', methods=['POST'])
@auth.login_required
def post_user():
    user_name = request.json.get('user_name')
    password = request.json.get('password')
    if user_name is None or password is None:
        abort(400)  # missing arguments
    try:
        user = create_user(user_name=user_name, password=password)
        return {'user_name': user.username, 'id': user.id}
    except Exception as e:
        msg = str(e)
        abort(400, msg)


@bp.route('/users', methods=['GET'])
@auth.login_required
def get_all_users():
    users = list_users()
    return {'items': users}
