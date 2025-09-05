"""
Kafka Client for Event Streaming
Provides producer and consumer functionality for event-driven architecture
"""

import json
import asyncio
import logging
from typing import Dict, Any, Callable, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import os

logger = logging.getLogger(__name__)

class KafkaClient:
    """Kafka client for publishing and consuming events"""
    
    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS', 
            'localhost:9092'
        )
        self.producer = None
        self.consumers = {}
        
    def _get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer"""
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                retry_backoff_ms=100,
                request_timeout_ms=30000,
                max_block_ms=5000
            )
        return self.producer
    
    async def publish_event(self, topic: str, event: Dict[str, Any], key: str = None) -> bool:
        """Publish an event to a Kafka topic"""
        try:
            producer = self._get_producer()
            
            # Add metadata to event
            event_with_metadata = {
                **event,
                'timestamp': asyncio.get_event_loop().time(),
                'source': os.getenv('SERVICE_NAME', 'unknown')
            }
            
            future = producer.send(
                topic, 
                value=event_with_metadata,
                key=key
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.info(f"Event published to topic {topic}, partition {record_metadata.partition}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to publish event to topic {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {e}")
            return False
    
    def create_consumer(self, topic: str, group_id: str, auto_offset_reset: str = 'latest') -> KafkaConsumer:
        """Create a Kafka consumer for a topic"""
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000
        )
        
        self.consumers[f"{topic}_{group_id}"] = consumer
        return consumer
    
    async def consume_events(self, topic: str, group_id: str, handler: Callable, auto_offset_reset: str = 'latest'):
        """Consume events from a topic with a handler function"""
        consumer = self.create_consumer(topic, group_id, auto_offset_reset)
        
        try:
            logger.info(f"Starting to consume events from topic {topic} with group {group_id}")
            
            for message in consumer:
                try:
                    # Process message in async context
                    await handler(message.value, message.key, message.topic, message.partition, message.offset)
                except Exception as e:
                    logger.error(f"Error processing message from topic {topic}: {e}")
                    # Continue processing other messages
                    continue
                    
        except KeyboardInterrupt:
            logger.info(f"Stopping consumer for topic {topic}")
        except Exception as e:
            logger.error(f"Consumer error for topic {topic}: {e}")
        finally:
            consumer.close()
    
    def close(self):
        """Close all connections"""
        if self.producer:
            self.producer.close()
        
        for consumer in self.consumers.values():
            consumer.close()
        
        logger.info("Kafka client connections closed")

# Event types and schemas
class EventTypes:
    """Standard event types for the platform"""
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    BOOKING_CREATED = "booking.created"
    BOOKING_CANCELLED = "booking.cancelled"
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    NOTIFICATION_SENT = "notification.sent"

class EventSchemas:
    """Event schemas for validation"""
    
    @staticmethod
    def user_registered(user_id: str, email: str, **kwargs) -> Dict[str, Any]:
        return {
            "event_type": EventTypes.USER_REGISTERED,
            "user_id": user_id,
            "email": email,
            "metadata": kwargs
        }
    
    @staticmethod
    def booking_created(booking_id: str, user_id: str, event_id: str, seats: list, **kwargs) -> Dict[str, Any]:
        return {
            "event_type": EventTypes.BOOKING_CREATED,
            "booking_id": booking_id,
            "user_id": user_id,
            "event_id": event_id,
            "seats": seats,
            "metadata": kwargs
        }
    
    @staticmethod
    def payment_completed(payment_id: str, booking_id: str, user_id: str, amount: float, **kwargs) -> Dict[str, Any]:
        return {
            "event_type": EventTypes.PAYMENT_COMPLETED,
            "payment_id": payment_id,
            "booking_id": booking_id,
            "user_id": user_id,
            "amount": amount,
            "metadata": kwargs
        }

# Global Kafka client instance
kafka_client = None

def get_kafka_client() -> KafkaClient:
    """Get global Kafka client instance"""
    global kafka_client
    if kafka_client is None:
        kafka_client = KafkaClient()
    return kafka_client

async def publish_user_event(event_type: str, user_id: str, **data):
    """Publish user-related events"""
    client = get_kafka_client()
    event = {
        "event_type": event_type,
        "user_id": user_id,
        **data
    }
    await client.publish_event("user-events", event, key=user_id)

async def publish_booking_event(event_type: str, booking_id: str, **data):
    """Publish booking-related events"""
    client = get_kafka_client()
    event = {
        "event_type": event_type,
        "booking_id": booking_id,
        **data
    }
    await client.publish_event("booking-events", event, key=booking_id)

async def publish_payment_event(event_type: str, payment_id: str, **data):
    """Publish payment-related events"""
    client = get_kafka_client()
    event = {
        "event_type": event_type,
        "payment_id": payment_id,
        **data
    }
    await client.publish_event("payment-events", event, key=payment_id)
