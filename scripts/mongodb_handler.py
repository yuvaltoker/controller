from pymongo import MongoClient
import os

class MongodbHandler:
    def __init__(self):
        # Get environment variables
        self.user = os.getenv('MONGO_INITDB_ROOT_USERNAME')
        self.password = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
        self.db_name = os.getenv('DB_NAME')
        self.port = '27017'
        self.connection = MongoClient('mongodb://root:example@mongodb:27017/')
        self.db = self.connection[self.db_name]
        #self.client = MongoClient('mongodb://%s:%s@%s:%d/' %(user, password, 'mongodb', port))
        # creating db
        self.connection[self.db_name]

    def is_collection_exist(self, collection_name):
        if collection_name in self.db.list_collection_names():
            return True, self.db[collection_name]
        return False, None

    def get_database(self, db_name):
        # getting a database
        return self.connection[db_name]

    def get_collection(self, collection_name):
        is_exist, collection = self.is_collection_exist(collection_name)
        if is_exist:
            return collection
        return None

    def insert_document(self, collection_name, document):
        collection = self.db[collection_name]
        collection.insert_one(document)

    def insert_documents(self, collection_name, documents):
        collection = self.db[collection_name]
        collection.insert_many(documents)