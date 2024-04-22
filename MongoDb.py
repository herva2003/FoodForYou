from pymongo import MongoClient

client = MongoClient(
    'mongodb+srv://gvghervatin:123456qwerty@cluster0.b4m0rm3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0 ')
db = client['PI5']
ingredientes = db['ingredientes']