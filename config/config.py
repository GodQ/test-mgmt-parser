import yaml
import os

PROJECT_BASE = os.path.dirname(os.path.dirname(__file__))
CONFIG_FILE = os.path.join(PROJECT_BASE, 'config', 'config.yaml')


class NoSuchConfig(Exception):
    pass


class Config:
    config = {}

    @classmethod
    def get_config(cls, key):
        if not cls.config:
            with open(CONFIG_FILE, 'r') as fd:
                config_str = fd.read()
                cls.config = yaml.safe_load(config_str)
        value = cls.config.get(key)
        if value:
            return value
        else:
            raise NoSuchConfig(f"No config named {key}")


def test():
    print(Config.get_config('data_store_type'))


if __name__ == '__main__':
    test()