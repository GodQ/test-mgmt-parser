from app_init import app
from blueprints import register_blueprints
from config.config import Config

register_blueprints(app)

print()
print(app.url_map)
print()

if __name__ == '__main__':
    port = Config.get_config('port')
    app.run(host="0.0.0.0", port=port, debug=False)
