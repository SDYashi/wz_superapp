from .ngb_kafkaapp import kafka_blueprint

def init_kafka_app(app):
    app.register_blueprint(kafka_blueprint, url_prefix='/kafka')
