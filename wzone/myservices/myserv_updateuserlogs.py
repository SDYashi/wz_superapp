import datetime
from urllib import request
from pymongo import MongoClient
from myserv_mongodbconnect import myserv_mongodbconnect 

class myserv_updateuserlogs:
    def __init__(self):  
        mongo_db = myserv_mongodbconnect()  
        dbconnect = mongo_db.get_connection() 
        self.collection = dbconnect['mpwz_users_logs']  
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

