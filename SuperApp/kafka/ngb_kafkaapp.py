from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from .ngb_kafka_service import KafkaConsumerService
import logging

# Create the Kafka Blueprint
kafka_blueprint = Blueprint('kafka', __name__)

# Kafka configurations (adjust according to your setup)
KAFKA_CONFIG = {
    'bootstrap.servers': 'your-kafka-server', 
    'group.id': 'flask-consumer-group',  
    'auto.offset.reset': 'earliest' 
}

TOPIC = 'your-topic'  

# Initialize Kafka Consumer Service
kafka_consumer_service = KafkaConsumerService(KAFKA_CONFIG, TOPIC)

# Route to start Kafka consumer
@kafka_blueprint.before_app_first_request
def start_kafka_consumer():
    """ Start Kafka consumer when the first request is received. """
    logging.info("Starting Kafka consumer...")
    kafka_consumer_service.start()

# Route to stop Kafka consumer 
@kafka_blueprint.route('/stop', methods=['POST'])
@jwt_required()
def stop_kafka():
    """ Gracefully stop the Kafka consumer. """
    logging.info("Stopping Kafka consumer...")
    kafka_consumer_service.stop()
    return jsonify({"msg": "Kafka consumer stopped."}), 200

# A simple status route to check if the Kafka consumer is active
@kafka_blueprint.route('/status', methods=['GET'])
@jwt_required()
def status():
    """ Endpoint to check Kafka consumer status """
    return jsonify({"status": "Kafka consumer is active."}), 200
