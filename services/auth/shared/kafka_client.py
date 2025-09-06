"""
Kafka Client for Event Booking Platform
Handles Kafka operations for scaling and event streaming with AWS MSK (SASL/SCRAM over TLS)
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from enum import Enum
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventTypes(Enum):
    """Event types for the booking platform"""
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    BOOKING_CREATED = "booking.created"
    BOOKING_CANCELLED = "booking.cancelled"
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_COMPLETED = "payment.completed"
    NOTIFICATION_SENT = "notification.sent"

class KafkaClient:
    """Kafka client for publishing and consuming events with AWS MSK SASL/SCRAM support"""

    def __init__(self):
        # AWS MSK Configuration
        self.bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "b-1.eventbookingkafkaclust.7xxw9x.c7.kafka.us-west-2.amazonaws.com:9096,"
            "b-2.eventbookingkafkaclust.7xxw9x.c7.kafka.us-west-2.amazonaws.com:9096"
        )
        self.enabled = os.getenv("ENABLE_KAFKA", "true").lower() == "true"

        # SASL/SCRAM Configuration
        self.sasl_username = os.getenv("KAFKA_SASL_USERNAME", "")
        self.sasl_password = os.getenv("KAFKA_SASL_PASSWORD", "")

        self.producer = None
        self.consumer = None

        if self.enabled:
            try:
                from confluent_kafka import Producer, Consumer
                
                # SASL/SCRAM Configuration for AWS MSK
                producer_config = {
                    'bootstrap.servers': self.bootstrap_servers,
                    'security.protocol': 'SASL_SSL',
                    'sasl.mechanism': 'SCRAM-SHA-512',
                    'sasl.username': self.sasl_username,
                    'sasl.password': self.sasl_password,
                    'client.id': 'event-booking-platform',
                    'retries': 5,
                    'retry.backoff.ms': 1000,
                    'request.timeout.ms': 30000,
                    'metadata.max.age.ms': 300000,
                    'connections.max.idle.ms': 540000,
                }

                self.producer = Producer(producer_config)
                logger.info(f"Kafka producer initialized with servers: {self.bootstrap_servers}")
                logger.info("Kafka client using SASL_SSL with SCRAM-SHA-512")

            except ImportError:
                logger.warning("confluent-kafka not installed. Kafka features disabled.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Kafka client: {e}")
                self.enabled = False
        else:
            logger.info("Kafka is disabled via ENABLE_KAFKA environment variable")

    def publish_event(self, event_type: EventTypes, data: Dict[str, Any],
                      key: Optional[str] = None, topic: Optional[str] = None) -> bool:
        """Publish an event to Kafka"""
        if not self.enabled or not self.producer:
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            logger.debug(f"Kafka disabled, skipping event: {event_type_str}")
            return False

        try:
            # Handle both enum and string event_type
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            topic = topic or f"event-booking-{event_type_str.replace('.', '-')}"
            event_data = {
                "event_type": event_type_str,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data,
                "service": data.get("service", "unknown"),
                "version": "1.0",
            }

            # Use confluent-kafka producer
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=json.dumps(event_data).encode('utf-8'),
                callback=self._delivery_callback
            )
            self.producer.flush(timeout=10)
            logger.info(f"Event published: {event_type_str} → {topic}")
            return True

        except Exception as e:
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            logger.error(f"Failed to publish event {event_type_str}: {e}")
            # Note: Topics will be auto-created when first message is published
            return False

    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation"""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

    def create_consumer(self, group_id: str, topics: list,
                        auto_offset_reset: str = "earliest"):
        """Create a Kafka consumer for the specified topics"""
        if not self.enabled:
            logger.debug("Kafka disabled, cannot create consumer")
            return None

        try:
            from confluent_kafka import Consumer
            
            consumer_config = {
                'bootstrap.servers': self.bootstrap_servers,
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'SCRAM-SHA-512',
                'sasl.username': self.sasl_username,
                'sasl.password': self.sasl_password,
                'group.id': group_id,
                'auto.offset.reset': auto_offset_reset,
                'enable.auto.commit': True,
                'client.id': f'event-booking-platform-{group_id}',
                'session.timeout.ms': 30000,
                'heartbeat.interval.ms': 10000,
                'metadata.max.age.ms': 300000,
            }

            consumer = Consumer(consumer_config)
            consumer.subscribe(topics)
            
            logger.info(f"Kafka consumer created for topics {topics}, group {group_id}")
            return consumer

        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            return None

    async def consume_events(self, topic: str, group_id: str, handler: Callable) -> None:
        """Consume events from a Kafka topic asynchronously"""
        if not self.enabled:
            logger.debug("Kafka disabled, cannot consume events")
            return

        consumer = self.create_consumer(group_id, [topic])
        if not consumer:
            return

        try:
            logger.info(f"Consuming events from topic: {topic}")
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                try:
                    # Parse message data
                    value = json.loads(msg.value().decode('utf-8')) if msg.value() else None
                    key = msg.key().decode('utf-8') if msg.key() else None
                    
                    await handler(value, key, msg.topic(), msg.partition(), msg.offset())
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    continue
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            consumer.close()
            logger.info("Kafka consumer closed")

    def close(self):
        """Close the Kafka client"""
        if self.producer:
            self.producer.flush()
            # confluent-kafka Producer doesn't have a close method
            logger.info("Kafka producer flushed")
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")

# Global Kafka client instance
_kafka_client = None

def get_kafka_client() -> KafkaClient:
    """Get the global Kafka client instance"""
    global _kafka_client
    if _kafka_client is None:
        _kafka_client = KafkaClient()
    return _kafka_client

# Convenience publishing functions
def publish_user_event(event_type: EventTypes, user_id: str, **data) -> bool:
    return get_kafka_client().publish_event(event_type, {"user_id": user_id, "service": "auth", **data},
                                            key=user_id, topic="user-events")

def publish_booking_event(event_type: EventTypes, booking_id: str, **data) -> bool:
    return get_kafka_client().publish_event(event_type, {"booking_id": booking_id, "service": "booking", **data},
                                            key=booking_id, topic="booking-events")

def publish_payment_event(event_type: EventTypes, payment_id: str, **data) -> bool:
    return get_kafka_client().publish_event(event_type, {"payment_id": payment_id, "service": "payment", **data},
                                            key=payment_id, topic="payment-events")

def publish_event_event(event_type: EventTypes, event_id: str, **data) -> bool:
    return get_kafka_client().publish_event(event_type, {"event_id": event_id, "service": "catalog", **data},
                                            key=event_id, topic="event-events")