from json import encoder
from pymongo import MongoClient
import pprint
import os

class MongodbHandler:
    def __init__(self):
        # Get environment variables
        self.user = os.getenv('MONGO_INITDB_ROOT_USERNAME')
        self.password = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
        self.db_name = os.getenv('DB_NAME')
        self.port = '27017'
        #self.connection = MongoClient('mongodb://root:example@mongodb:27017/')
        self.connection = MongoClient('mongodb://%s:%s@%s:%s/' %(self.user, self.password, 'mongodb', self.port))
        self.db = self.connection[self.db_name]
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

    # returns documents by given field and value
    # for more examples of querying in pymongo see https://www.analyticsvidhya.com/blog/2020/08/query-a-mongodb-database-using-pymongo/
    def get_documents(self, collection_name, field, value):
        return self.get_collection(collection_name).find({field : value})

    def get_all_documents(self, collection_name):
        return self.get_collection(collection_name).find()

    # function gets documents from get_documents or get_all_documents
    def print_documents(self, documents):
        for document in documents: 
            MyPrettyPrinter().pprint(document)

    def insert_document(self, collection_name, document):
        collection = self.db[collection_name]
        uid = collection.insert_one(document)
        return uid.inserted_id
        

    def insert_documents(self, collection_name, documents):
        collection = self.db[collection_name]
        collection.insert_many(documents)


class MyPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, unicode):
            return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)
