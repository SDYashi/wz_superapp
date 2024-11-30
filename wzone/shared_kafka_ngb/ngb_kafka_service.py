import logging
import threading
from confluent_kafka import Consumer, KafkaException, KafkaError

class KafkaConsumerService:
    def __init__(self, kafka_config, topic):
        self.kafka_config = kafka_config
        self.topic = topic
        self.consumer = Consumer(self.kafka_config)
        self.running = False

    def consume_messages(self):
        try:
            self.consumer.subscribe([self.topic])
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                elif msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        raise KafkaException(msg.error())
                else:
                    self.process_message(msg.value().decode('utf-8'))
        except Exception as e:
           print(f"Error consuming Kafka messages: {e}")
        finally:
            self.consumer.close()

    def process_message(self, message):     
        print(f"Received message: {message}")

    def start(self):      
        self.running = True
        consumer_thread = threading.Thread(target=self.consume_messages)
        consumer_thread.daemon = True 
        consumer_thread.start()

    def stop(self):       
        self.running = False
