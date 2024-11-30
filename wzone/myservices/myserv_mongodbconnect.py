from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class myserv_mongodbconnect:
    def __init__(self):
        self.uri = "mongodb://localhost:27017/"
        self.db_name = "admin"
        self.client = None
        self.db = None

    def get_connection(self):
        if self.client is None:
            try:
                self.client = MongoClient(self.uri)
                self.db = self.client[self.db_name]
                print("MongoDB connection established.")
            except ConnectionFailure as e:
                print(f"Could not connect to MongoDB: {e}")
        return self.db

    def close_connection(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None
            print("MongoDB connection closed.")
