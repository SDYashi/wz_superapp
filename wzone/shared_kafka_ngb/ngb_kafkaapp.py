from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from .ngb_kafka_service import KafkaConsumerService
import logging

# Create the Kafka Blueprint
kafka_blueprint = Blueprint('kafka', __name__)

# Kafka configurations (adjust according to your setup)
kafka_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my_group',
    'auto.offset.reset': 'earliest',
}

topic = 'my_topic'
app_name = 'SuperApp'
consumer_service = KafkaConsumerService(kafka_config, topic)
consumer_service.start()

# Route to start Kafka consumer
@kafka_blueprint.before_app_first_request
def start_kafka_consumer():  
    logging.info("Starting Kafka consumer...")
    consumer_service.start()

# Route to stop Kafka consumer 
@kafka_blueprint.route('/stop', methods=['POST'])
@jwt_required()
def stop_kafka():  
    logging.info("Stopping Kafka consumer...")
    consumer_service.stop()
    return jsonify({"msg": "Kafka consumer stopped."}), 200

# A simple status route to check if the Kafka consumer is active
@kafka_blueprint.route('/status', methods=['GET'])
@jwt_required()
def status(): 
    return jsonify({"status": "Kafka consumer is active."}), 200
