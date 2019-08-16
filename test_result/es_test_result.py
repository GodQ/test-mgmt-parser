from elasticsearch import Elasticsearch

hosts = ["10.110.124.130:9200"]
index = "test-result-vose"
es = Elasticsearch(hosts=hosts)


def search_data(params=None):
    query_body = {"query": {"match_all": {}}}
    res = es.search(index=index, body=query_body)
    data = list()
    print("Got %d Hits:" % res['hits']['total']['value'])
    for hit in res['hits']['hits']:
        data.append(hit["_source"])
    return data


# print(search_data()[0])