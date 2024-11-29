from pymongo import MongoClient
from pymongo.errors import PyMongoError

class SequenceGenerator:
    def __init__(self, db_name):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.sequence_collection = self.db['mpwz_sequences']
        self.collections_id_collection = self.db['mpwz_collections_id']        
      
        self.collections = [
            'mpwz_collections_id',
            'mpwz_integrated_app',
            'mpwz_notify_status',
            "mpwz_notifylist",
            "mpwz_user_action_history",
            "mpwz_users",
            "mpwz_users_credentials",
            "mpwz_users_logs"
        ]
      
        for collection in self.collections:
            self.initialize_sequence(collection)

    def initialize_sequence(self, collection_name):
        if not self.sequence_collection.find_one({'_id': collection_name}):
            self.sequence_collection.insert_one({'_id': collection_name, 'seq': 0})

    def get_next_sequence(self, collection_name):
        try:
            result = self.sequence_collection.find_one_and_update(
                {'_id': collection_name},
                {'$inc': {'seq': 1}},  
                return_document=True
            )
            
            if not result:
                raise ValueError(f"Sequence for {collection_name} not found.")

            new_sequence_number = result['seq']
            self.collections_id_collection.insert_one({
                'collection_name': collection_name,
                'sequence_number': new_sequence_number
            })

            return new_sequence_number

        except PyMongoError as e:
            print(f"Error while getting sequence for {collection_name}: {e}")
            self.reset_sequence(collection_name)
            return self.get_next_sequence(collection_name)  

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None  
    
    def reset_sequence(self, collection_name):
        try:
            self.sequence_collection.update_one(
                {'_id': collection_name},
                {'$set': {'seq': 0}}
            )
            print(f"Sequence for {collection_name} reset successfully.")
        except PyMongoError as e:
            print(f"Error resetting sequence for {collection_name}: {e}")

    def close(self):
        self.client.close()
