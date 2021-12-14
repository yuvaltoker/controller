from rabbitmq_handler import RabbitmqHandler
from mongodb_handler import MongodbHandler
from json import dumps, loads
# from pymongo import MongoClient
# for more convenient storing dictionaries
from pandas import DataFrame

def rabbitmq_send_msg_example():
    print('im the rabbitmq example')
    rmq_handler = RabbitmqHandler()
    print(rmq_handler.request_pdf())

def mongodb_tests():
    print('im the mongodb example')
    mdb_handler = MongodbHandler()
    json_document_string = dumps('{"_id" : "U2IT00001", "item_name" : "AA","max_discount" : "10%","batch_number" : "AAAAA","price" : "900","category" : "kitchen appliance"}')
    mdb_handler.insert_document('example_colleciton', loads(json_document_string))
    #collection = mdb_handler.get_collection('example_collection')
    #print(dumps(collection))
    
    #items_list = collection_name.find()

if __name__ == '__main__':
    mongodb_tests()