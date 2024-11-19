from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import threading
import time

class MongoDBTrigger:
    def __init__(self, uri, db_name, collection_name,erp_collection_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.erp_collection = self.db[erp_collection_name]
        self.is_running = True 

    def process_change_notifylist(self, change):

        if change['operationType'] == 'insert':
            new_document = change['fullDocument']
            action_history_collection = self.db['action_history_erp']
            action_history_document = {
                'mpwz_id': new_document['mpwz_id'],
                'erp_app_id': new_document['erp_app_id'],
                'erp_notify_refsys_id': new_document['erp_notify_refsys_id'],
                'erp_action_datetime': new_document.get('erp_action_datetime', None),
                'erp_notify_details': "New notification created.",
                'erp_notify_remark': "Pending action."
            }
            action_history_collection.insert_one(action_history_document)
            print('Action history updated:', action_history_document)

    def process_change_ngb(self, change):

        if change['operationType'] == 'update':
            updated_fields = change['updateDescription']['updatedFields']
            if 'ngb_notify_status' in updated_fields:
                updated_document = change['fullDocument']
                
                print('ngb_notify_status updated:', updated_document)

    def watch_changes(self):
        try:
            change_stream = self.collection.watch()
            print("Listening for changes in mpwz_notifylist_erp...")
            for change in change_stream:
                if not self.is_running:
                    break
                self.process_change_notifylist(change)
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def watch_ngb_changes(self):
        try:
            ngb_change_stream = self.erp_collection.watch()
            print("Listening for changes in mpwz_notifylist_ngb...")
            for change in ngb_change_stream:
                if not self.is_running:
                    break
                self.process_change_ngb(change)
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def start_watching(self):
        # Start the change streams in separate threads
        thread1 = threading.Thread(target=self.watch_changes)
        thread2 = threading.Thread(target=self.watch_ngb_changes)
        thread1.start()
        thread2.start()

    def stop_watching(self):
        self.is_running = False