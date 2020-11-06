from test_result import bp as test_result_bp
from auth import bp as auth_bp
from admin import bp as admin_bp


def register_blueprints(app):
    app.register_blueprint(test_result_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
