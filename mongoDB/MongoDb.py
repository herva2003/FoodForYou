from pymongo import MongoClient

client_mongo = MongoClient(
    'mongodb+srv://user:senha@cluster0.b4m0rm3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')


db = client_mongo['PI5']
users = db['users']
ingredientes = db['ingredientes']