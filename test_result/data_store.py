from test_result.es.data_store import ElasticSearchDataStore
from config.config import Config

data_store_mapping = {
    'es': ElasticSearchDataStore
}


def load_data_store_cls(data_store_type=None):
    if not data_store_type:
        data_store_type = Config.get_config('data_store_type')
    data_store_cls = data_store_mapping.get(data_store_type)
    if not data_store_cls:
        raise Exception(f'No data store named {data_store_type}')
    return data_store_cls


DataStore = load_data_store_cls()
