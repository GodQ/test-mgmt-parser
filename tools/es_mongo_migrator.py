import pymongo
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl import connections

import time
from pprint import pprint
from config.config import Config


MONGO_URL = Config.get_config('mongo_url')
MONGO_DB = Config.get_config('mongo_db')
ES_HOSTS = Config.get_config('es_hosts')
connections.create_connection(hosts=ES_HOSTS, timeout=30)


class Migrator:
    def __init__(self):
        self.mongo_client = pymongo.MongoClient(MONGO_URL)
        self.mongo = self.mongo_client[MONGO_DB]
        self.es = Elasticsearch(hosts=ES_HOSTS)

    def load_from_es(self, index, from_=0, to_=None, batch_size=2):
        if not to_:
            to_ = 9999999999999
        query = {'track_total_hits': True}
        search_obj = Search.from_dict(query)
        search_obj = search_obj.index(index)
        start = from_
        while start < to_:
            end = start + batch_size
            if end > to_:
                end = to_
            print(f'load docs from es, [{start}, {end-1}]')
            search_obj = search_obj[start: end]
            res = search_obj.execute()
            if res.hits.total.value < to_:
                to_ = res.hits.total.value
            ret = []
            for hit in res.hits.hits:
                d = hit['_source'].to_dict()
                ret.append(d)
            yield ret
            start += batch_size

    def load_from_es_scroll(self, index, from_=0, to_=None, batch_size=2):
        from elasticsearch.helpers import scan
        if not to_:
            to_ = 9999999999999

        count = 0
        t = 0
        query = {'query': {'match_all': {}}}
        iterator = scan(self.es, index=index, query=query,
                        scroll="5m", size=batch_size, from_=from_)
        res = []
        for doc in iterator:
            count += 1
            t += 1
            print(t, count)
            res.append(doc['_source'])
            if count >= to_:
                yield res
                break
            if t >= batch_size:
                yield res
                res = []
                t = 0

    def dump_to_mongo(self, collection, data: list):
        r = self.mongo[collection].insert_many(documents=data, ordered=False)
        print(f'{len(r.inserted_ids)} docs writen to mongo')
        return r

    def migrate(self, es_index, mongo_collection, from_=0, to_=None, interval=2):
        a = time.time()
        y = self.load_from_es(es_index, from_, to_, interval)
        for docs in y:
            m.dump_to_mongo(mongo_collection, docs)
        b = time.time()
        print(f'Cost {b-a} s')


m = Migrator()
# m.migrate(es_index='alp-saas', mongo_collection='alp-saas', interval=100)
# m.migrate(es_index='alp-onprem', mongo_collection='alp-onprem', interval=100)

r = m.load_from_es_scroll(index='alp-saas', batch_size=100)
for docs in r:
    print(len(docs))
