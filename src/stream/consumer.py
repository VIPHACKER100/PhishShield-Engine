"""
Kafka / RabbitMQ Stream Consumer (Phase 38)
Provides architectural framework to listen for and process massive live email streams.

Configuration (via environment variables):
    KAFKA_BROKER_URL  — Kafka bootstrap server address (default: localhost:9092 for dev only)
    KAFKA_TOPIC       — Topic to consume from (default: email_ingest)
"""

import os
from src.utils.logger import logger
from src.models.predict import predict_email

# Read broker configuration from environment — never hardcode in source
_DEFAULT_BROKER = (
    "localhost:9092"  # Dev fallback only; override via KAFKA_BROKER_URL in prod
)
_DEFAULT_TOPIC = "email_ingest"


class EmailStreamConsumer:
    def __init__(
        self,
        broker_url: str = None,
        topic: str = None,
    ):
        self.broker_url = broker_url or os.environ.get(
            "KAFKA_BROKER_URL", _DEFAULT_BROKER
        )
        self.topic = topic or os.environ.get("KAFKA_TOPIC", _DEFAULT_TOPIC)

        if self.broker_url == _DEFAULT_BROKER:
            logger.warning(
                "KAFKA_BROKER_URL is not set — using insecure dev default '%s'. "
                "Set KAFKA_BROKER_URL in your environment for production.",
                _DEFAULT_BROKER,
            )

        logger.info(
            "Initialized stream consumer for topic %s at %s",
            self.topic,
            self.broker_url,
        )

    def listen(self):
        """Simulate consuming from a high-throughput message queue."""
        logger.info("Listening for streaming messages...")
        # In actual deployment, instantiate a KafkaConsumer here.
        # e.g. consumer = KafkaConsumer(self.topic, bootstrap_servers=[self.broker_url])
        # for msg in consumer:
        #    process(msg.value)
        pass

    def process(self, email_text: str):
        """Invoke classification inference on stream ingestion."""
        res = predict_email(email_text)
        if res["prediction"] == "spam":
            logger.warning(
                "[STREAM] Intercepted SPAM email! Risk: %d",
                res.get("security_risk_score", 0),
            )


if __name__ == "__main__":
    consumer = EmailStreamConsumer()
    # consumer.listen()
