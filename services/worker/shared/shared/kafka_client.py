"""
Kafka Client for Event Booking Platform
Handles Kafka operations for scaling and event streaming
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventTypes(Enum):
    """Event types for the booking platform"""
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    BOOKING_CREATED = "booking.created"
    BOOKING_CANCELLED = "booking.cancelled"
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"
    NOTIFICATION_SENT = "notification.sent"

class KafkaClient:
    """Kafka client for publishing events"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.enabled = os.getenv("ENABLE_KAFKA", "false").lower() == "true"
        self.client = None
        
        if self.enabled:
            try:
                from kafka import KafkaProducer
                self.client = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    retries=3,
                    retry_backoff_ms=1000,
                    request_timeout_ms=30000
                )
                logger.info(f"Kafka client initialized with servers: {self.bootstrap_servers}")
            except ImportError:
                logger.warning("Kafka library not installed. Kafka features disabled.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Kafka client: {e}")
                self.enabled = False
        else:
            logger.info("Kafka is disabled via ENABLE_KAFKA environment variable")

    def publish_event(self, event_type: EventTypes, data: Dict[str, Any], key: Optional[str] = None) -> bool:
        """Publish an event to Kafka"""
        if not self.enabled or not self.client:
            logger.debug(f"Kafka disabled, skipping event: {event_type.value}")
            return False
        
        try:
            event_data = {
                "event_type": event_type.value,
                "timestamp": data.get("timestamp"),
                "data": data,
                "service": data.get("service", "unknown")
            }
            
            future = self.client.send(
                topic=f"event-booking-{event_type.value.replace('.', '-')}",
                value=event_data,
                key=key
            )
            
            # Wait for the message to be sent
            record_metadata = future.get(timeout=10)
            logger.info(f"Event published: {event_type.value} to partition {record_metadata.partition}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type.value}: {e}")
            return False

    def close(self):
        """Close the Kafka client"""
        if self.client:
            self.client.close()
            logger.info("Kafka client closed")

# Global Kafka client instance
_kafka_client = None

def get_kafka_client() -> KafkaClient:
    """Get the global Kafka client instance"""
    global _kafka_client
    if _kafka_client is None:
        _kafka_client = KafkaClient()
    return _kafka_client

def publish_user_event(event_type: EventTypes, user_id: str, data: Dict[str, Any]) -> bool:
    """Publish a user-related event"""
    client = get_kafka_client()
    event_data = {
        "user_id": user_id,
        "timestamp": data.get("timestamp"),
        "service": data.get("service", "auth"),
        **data
    }
    return client.publish_event(event_type, event_data, key=user_id)

def publish_booking_event(event_type: EventTypes, booking_id: str, data: Dict[str, Any]) -> bool:
    """Publish a booking-related event"""
    client = get_kafka_client()
    event_data = {
        "booking_id": booking_id,
        "timestamp": data.get("timestamp"),
        "service": data.get("service", "booking"),
        **data
    }
    return client.publish_event(event_type, event_data, key=booking_id)

def publish_payment_event(event_type: EventTypes, payment_id: str, data: Dict[str, Any]) -> bool:
    """Publish a payment-related event"""
    client = get_kafka_client()
    event_data = {
        "payment_id": payment_id,
        "timestamp": data.get("timestamp"),
        "service": data.get("service", "payment"),
        **data
    }
    return client.publish_event(event_type, event_data, key=payment_id)

def publish_event_event(event_type: EventTypes, event_id: str, data: Dict[str, Any]) -> bool:
    """Publish an event-related event"""
    client = get_kafka_client()
    event_data = {
        "event_id": event_id,
        "timestamp": data.get("timestamp"),
        "service": data.get("service", "catalog"),
        **data
    }
    return client.publish_event(event_type, event_data, key=event_id)