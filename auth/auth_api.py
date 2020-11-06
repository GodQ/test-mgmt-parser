from . import bp
from flask import jsonify, request, make_response, abort, g
import json
import traceback

from auth.auth import auth, generate_auth_token

# curl -v -X POST 127.0.0.1:5000/api/token -u root:password
# curl -v -X GET 127.0.0.1:5000/api/summary -H "Authorization: Bearer <token>"


@bp.route('/current_user', methods=['GET'])
@auth.login_required
def get_current_user():
    user = g.user
    return user.to_dict()


@bp.route('/token', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = generate_auth_token(g.user)
    return jsonify({'token': token.decode('ascii')}), 201


