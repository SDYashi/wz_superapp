from pymongo import MongoClient

class SequenceGenerator:
    def __init__(self, db_name):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.sequence_collection = self.db['sequences']
        self.collections_id_collection = self.db['mpwz_collections_id']        
      
        self.collections = [
            'action_history_erp',
            'action_history_ngb',
            'mpwz_notifylist_erp',
            'mpwz_notifylist_ngb',
            'mpwz_users_logs',
            "mpwz_notify_status",
            "mpwz_integrated_app",
            "mpwz_user_action_history"
        ]
      
        for collection in self.collections:
            self.initialize_sequence(collection)

    def initialize_sequence(self, collection_name):
        if not self.sequence_collection.find_one({'_id': collection_name}):
           self.sequence_collection.insert_one({'_id': collection_name, 'seq': 0})

    def get_next_sequence(self, collection_name):

        result = self.sequence_collection.find_one_and_update(
            {'_id': collection_name},
            {'$inc': {'seq': 1}},
            return_document=True
        )       
      
        new_sequence_number = result['seq']
        
        self.collections_id_collection.insert_one({
            'collection_name': collection_name,
            'sequence_number': new_sequence_number
        })
        
        return new_sequence_number

    def close(self):
        self.client.close()

