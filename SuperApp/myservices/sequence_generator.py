from pymongo import MongoClient

class SequenceGenerator:
    def __init__(self, db_name):
        self.client = MongoClient('mongodb://localhost:27017/')  # Update with your MongoDB URI
        self.db = self.client[db_name]
        self.sequence_collection = self.db['sequences']

        # Initialize the collections that will have unique sequences
        self.collections = [
            'action_history_erp',
            'action_history_ngb',
            'mpwz_notifylist_erp',
            'mpwz_notifylist_ngb'
        ]

        # Initialize sequence numbers for each collection
        for collection in self.collections:
            self.initialize_sequence(collection)

    def initialize_sequence(self, collection_name):
        # Ensure the sequence document exists for the collection
        if not self.sequence_collection.find_one({'_id': collection_name}):
            self.sequence_collection.insert_one({'_id': collection_name, 'seq': 0})

    def get_next_sequence(self, collection_name):
        # Get the next sequence number for the specified collection
        result = self.sequence_collection.find_one_and_update(
            {'_id': collection_name},
            {'$inc': {'seq': 1}},
            return_document=True
        )
        return result['seq']

    def close(self):
        self.client.close()