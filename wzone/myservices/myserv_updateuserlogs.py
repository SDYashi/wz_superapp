import datetime
from urllib import request
from pymongo import MongoClient

class myserv_updateuserlogs:
    def __init__(self):
        # Set up MongoDB client and database
        self.client = MongoClient('mongodb://localhost:27017') 
        self.db = self.client['admin'] 
        self.collection = self.db['mpwz_users_logs']  
        self.api_call_history = []  
    def log_api_call(self, request_data, response_data):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "request": request_data,
            "response": response_data
        }
        self.collection.insert_one(log_entry)
        self.api_call_history.append(log_entry)
        print("API Calling:",log_entry,"\n")

    def get_current_datetime(self):
        now =  datetime.datetime.now().isoformat()
        return now    

