from json import encoder
from pymongo import MongoClient
import pprint
import os
from bson.json_util import loads, dumps

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

    #returns a cursor with the specific field and values without the id field
    # for more examples of querying in pymongo see https://www.analyticsvidhya.com/blog/2020/08/query-a-mongodb-database-using-pymongo/
    def get_specific_documents(self, collection_name, field, value):
        return self.get_collection(collection_name).find({field : value},{"_id":0})
    # returns a Cursor without the id field
    def get_all_documents(self, collection_name):
        return self.get_collection(collection_name).find({},{"_id":0})
    
    # returns list of dic, each dic holds a json object
    def get_all_documents_in_list(self,collection_name):
        return list(self.get_collection(collection_name).find({},{"_id":0}))
    # returns a dic with the specific field and values without the id field
    def get_find_one(self, collection_name,field,value):
        json_object = None
        results = self.get_collection(collection_name).find_one({field : value})
        if not (results is None):
            json_object = {key : value for key, value in results.items()}
        return json_object
    # returns specific fields of document filtered by query {field : value, ...}, currently _id will always be shown
    # note that when an empty list is given in fields, all fields are going to be in the returning dictionary
    def get_one_filtered_with_fields(self, collection_name, query, fields):
        json_object = None
        # create the next dict: {field1 : 1, field2 : 1, field3 : 1,... fieldN : 1}
        # which means, show each of the fields in fields
        fields_to_show = {field : 1 for field in fields}
        # for some reason, as a default, _id will be shown if not specify different 
        if not '_id' in fields:
            fields_to_show['_id'] = 0
        results = self.get_collection(collection_name).find_one(query,fields_to_show)
        if results is not None:
            json_object = {key : value for key, value in results.items()}
        return json_object
    def get_jsonOBJ(self, collection_name):
        results=self.get_all_documents(collection_name)
        json_obj=[dumps(result, separators=(',', ':')) for result in results]
        return json_obj

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
