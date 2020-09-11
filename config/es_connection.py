from elasticsearch_dsl import Document, Nested, Date, Integer, Keyword, Text, connections
from config.config import Config

# Define a default Elasticsearch client
connections.create_connection(hosts=Config.get_config('es_hosts'))
