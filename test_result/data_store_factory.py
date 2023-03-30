from config.config import Config


def load_data_store_cls(data_store_type=None):
    if not data_store_type:
        data_store_type = Config.get_config('data_store_type')
    if data_store_type == 'es':
        from test_result.es.test_result_data_store import ESTestResultDataStore
        data_store_cls = ESTestResultDataStore
    elif data_store_type == 'mongo':
        from test_result.mongo.test_result_data_store import MongoTestResultDataStore
        data_store_cls = MongoTestResultDataStore
    else:
        raise Exception(f'No data store named {data_store_type}')
    return data_store_cls


DataStore = load_data_store_cls()
