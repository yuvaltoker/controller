from pymongo import MongoClient
import os

class Rabbitmq_handler:
    def __init__(self):
        # Get environment variables
        self.user = os.getenv('MONGO_INITDB_ROOT_USERNAME')
        self.password = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
        self.port = '27017'

def get_database(db_name):
    #client = MongoClient('mongodb://%s:%s@%s:%d/' %(user, password, 'mongodb', port))
    client = MongoClient('mongodb://root:example@mongodb:27017/')
    return client[db_name] # creating a new data base in mongo

def database_insert(collection_name, items):
    collection_name.insert_many(items)