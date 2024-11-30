from pymongo.errors import PyMongoError

class myserv_getmpwz_id:
    def __init__(self):
        from myservices.myserv_mongodbconnect import myserv_mongodbconnect        
        mongo_db = myserv_mongodbconnect()  
        dbconnect = mongo_db.get_connection()        
        self.sequence_collection = dbconnect['mpwz_sequences']
        self.collections_id_collection = dbconnect['mpwz_collections_id']
        
        # List of collections for which sequences will be initialized
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
        
        # Initialize sequence for each collection
        for collection in self.collections:
            self.initialize_sequence(collection)

    def initialize_sequence(self, collection_name):
        # Check if the sequence entry exists, if not, create it
        if not self.sequence_collection.find_one({'_id': collection_name}):
            self.sequence_collection.insert_one({'_id': collection_name, 'seq': 0})

    def get_next_sequence(self, collection_name):
        try:
            # Increment sequence for the collection
            result = self.sequence_collection.find_one_and_update(
                {'_id': collection_name},
                {'$inc': {'seq': 1}},  
                return_document=True
            )
            if not result:
                raise ValueError(f"Sequence for {collection_name} not found.")
            
            new_sequence_number = result['seq']
            # Insert the sequence number into the collections_id collection
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
            # Reset the sequence for the given collection
            self.sequence_collection.update_one(
                {'_id': collection_name},
                {'$set': {'seq': 0}}
            )
            print(f"Sequence for {collection_name} reset successfully.")
        except PyMongoError as e:
            print(f"Error resetting sequence for {collection_name}: {e}")
