from test_result import bp as test_result_bp


def register_blueprints(app):
    app.register_blueprint(test_result_bp)
