"""
Enhanced Worker Service for Event Processing
Processes events from Kafka and handles background tasks
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any
from datetime import datetime

# Add shared components to path
sys.path.append('/app/shared')

from kafka_client import get_kafka_client, EventTypes
from health import setup_default_health_checks
from circuit_breaker import get_circuit_breaker, CircuitBreakerConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventProcessor:
    """Processes events from Kafka"""
    
    def __init__(self):
        self.kafka_client = get_kafka_client()
        self.circuit_breaker = get_circuit_breaker("worker-processing", CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60
        ))
        
    async def process_user_event(self, event: Dict[str, Any], key: str, topic: str, partition: int, offset: int):
        """Process user-related events"""
        try:
            event_type = event.get("event_type")
            user_id = event.get("user_id")
            
            logger.info(f"Processing user event: {event_type} for user {user_id}")
            
            if event_type == EventTypes.USER_REGISTERED:
                await self.handle_user_registration(event)
            elif event_type == EventTypes.USER_LOGIN:
                await self.handle_user_login(event)
            elif event_type == EventTypes.USER_LOGOUT:
                await self.handle_user_logout(event)
            else:
                logger.warning(f"Unknown user event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing user event: {e}")
            raise
    
    async def process_booking_event(self, event: Dict[str, Any], key: str, topic: str, partition: int, offset: int):
        """Process booking-related events"""
        try:
            event_type = event.get("event_type")
            booking_id = event.get("booking_id")
            
            logger.info(f"Processing booking event: {event_type} for booking {booking_id}")
            
            if event_type == EventTypes.BOOKING_CREATED:
                await self.handle_booking_created(event)
            elif event_type == EventTypes.BOOKING_CANCELLED:
                await self.handle_booking_cancelled(event)
            else:
                logger.warning(f"Unknown booking event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing booking event: {e}")
            raise
    
    async def process_payment_event(self, event: Dict[str, Any], key: str, topic: str, partition: int, offset: int):
        """Process payment-related events"""
        try:
            event_type = event.get("event_type")
            payment_id = event.get("payment_id")
            
            logger.info(f"Processing payment event: {event_type} for payment {payment_id}")
            
            if event_type == EventTypes.PAYMENT_COMPLETED:
                await self.handle_payment_completed(event)
            elif event_type == EventTypes.PAYMENT_FAILED:
                await self.handle_payment_failed(event)
            else:
                logger.warning(f"Unknown payment event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing payment event: {e}")
            raise
    
    async def handle_user_registration(self, event: Dict[str, Any]):
        """Handle user registration event"""
        user_id = event.get("user_id")
        email = event.get("email")
        
        logger.info(f"Handling user registration: {email} (ID: {user_id})")
        
        # Send welcome email (simulated)
        await self.send_welcome_email(email)
        
        # Update user analytics
        await self.update_user_analytics("registration", user_id)
        
        # Log audit event
        await self.log_audit_event("user_registered", user_id, {"email": email})
    
    async def handle_user_login(self, event: Dict[str, Any]):
        """Handle user login event"""
        user_id = event.get("user_id")
        email = event.get("email")
        
        logger.info(f"Handling user login: {email} (ID: {user_id})")
        
        # Update last login time
        await self.update_last_login(user_id)
        
        # Update user analytics
        await self.update_user_analytics("login", user_id)
        
        # Log audit event
        await self.log_audit_event("user_login", user_id, {"email": email})
    
    async def handle_user_logout(self, event: Dict[str, Any]):
        """Handle user logout event"""
        user_id = event.get("user_id")
        
        logger.info(f"Handling user logout: {user_id}")
        
        # Update user analytics
        await self.update_user_analytics("logout", user_id)
        
        # Log audit event
        await self.log_audit_event("user_logout", user_id)
    
    async def handle_booking_created(self, event: Dict[str, Any]):
        """Handle booking created event"""
        booking_id = event.get("booking_id")
        user_id = event.get("user_id")
        event_id = event.get("event_id")
        seats = event.get("seats", [])
        
        logger.info(f"Handling booking created: {booking_id} for user {user_id}")
        
        # Send booking confirmation email
        await self.send_booking_confirmation(user_id, booking_id, event_id, seats)
        
        # Update booking analytics
        await self.update_booking_analytics("created", booking_id, user_id)
        
        # Log audit event
        await self.log_audit_event("booking_created", user_id, {
            "booking_id": booking_id,
            "event_id": event_id,
            "seats": seats
        })
    
    async def handle_booking_cancelled(self, event: Dict[str, Any]):
        """Handle booking cancelled event"""
        booking_id = event.get("booking_id")
        user_id = event.get("user_id")
        
        logger.info(f"Handling booking cancelled: {booking_id} for user {user_id}")
        
        # Send cancellation email
        await self.send_booking_cancellation(user_id, booking_id)
        
        # Update booking analytics
        await self.update_booking_analytics("cancelled", booking_id, user_id)
        
        # Log audit event
        await self.log_audit_event("booking_cancelled", user_id, {"booking_id": booking_id})
    
    async def handle_payment_completed(self, event: Dict[str, Any]):
        """Handle payment completed event"""
        payment_id = event.get("payment_id")
        booking_id = event.get("booking_id")
        user_id = event.get("user_id")
        amount = event.get("amount")
        
        logger.info(f"Handling payment completed: {payment_id} for booking {booking_id}")
        
        # Send payment receipt
        await self.send_payment_receipt(user_id, payment_id, amount)
        
        # Update payment analytics
        await self.update_payment_analytics("completed", payment_id, amount)
        
        # Log audit event
        await self.log_audit_event("payment_completed", user_id, {
            "payment_id": payment_id,
            "booking_id": booking_id,
            "amount": amount
        })
    
    async def handle_payment_failed(self, event: Dict[str, Any]):
        """Handle payment failed event"""
        payment_id = event.get("payment_id")
        booking_id = event.get("booking_id")
        user_id = event.get("user_id")
        
        logger.info(f"Handling payment failed: {payment_id} for booking {booking_id}")
        
        # Send payment failure notification
        await self.send_payment_failure_notification(user_id, payment_id)
        
        # Update payment analytics
        await self.update_payment_analytics("failed", payment_id, 0)
        
        # Log audit event
        await self.log_audit_event("payment_failed", user_id, {
            "payment_id": payment_id,
            "booking_id": booking_id
        })
    
    # Helper methods (simulated implementations)
    
    async def send_welcome_email(self, email: str):
        """Send welcome email to new user"""
        logger.info(f"Sending welcome email to {email}")
        # Simulate email sending
        await asyncio.sleep(0.1)
    
    async def send_booking_confirmation(self, user_id: str, booking_id: str, event_id: str, seats: list):
        """Send booking confirmation email"""
        logger.info(f"Sending booking confirmation to user {user_id} for booking {booking_id}")
        # Simulate email sending
        await asyncio.sleep(0.1)
    
    async def send_booking_cancellation(self, user_id: str, booking_id: str):
        """Send booking cancellation email"""
        logger.info(f"Sending booking cancellation to user {user_id} for booking {booking_id}")
        # Simulate email sending
        await asyncio.sleep(0.1)
    
    async def send_payment_receipt(self, user_id: str, payment_id: str, amount: float):
        """Send payment receipt email"""
        logger.info(f"Sending payment receipt to user {user_id} for payment {payment_id}")
        # Simulate email sending
        await asyncio.sleep(0.1)
    
    async def send_payment_failure_notification(self, user_id: str, payment_id: str):
        """Send payment failure notification"""
        logger.info(f"Sending payment failure notification to user {user_id} for payment {payment_id}")
        # Simulate email sending
        await asyncio.sleep(0.1)
    
    async def update_user_analytics(self, action: str, user_id: str):
        """Update user analytics"""
        logger.info(f"Updating user analytics: {action} for user {user_id}")
        # Simulate analytics update
        await asyncio.sleep(0.05)
    
    async def update_booking_analytics(self, action: str, booking_id: str, user_id: str):
        """Update booking analytics"""
        logger.info(f"Updating booking analytics: {action} for booking {booking_id}")
        # Simulate analytics update
        await asyncio.sleep(0.05)
    
    async def update_payment_analytics(self, action: str, payment_id: str, amount: float):
        """Update payment analytics"""
        logger.info(f"Updating payment analytics: {action} for payment {payment_id}")
        # Simulate analytics update
        await asyncio.sleep(0.05)
    
    async def update_last_login(self, user_id: str):
        """Update user's last login time"""
        logger.info(f"Updating last login for user {user_id}")
        # Simulate database update
        await asyncio.sleep(0.05)
    
    async def log_audit_event(self, event_type: str, user_id: str, details: Dict[str, Any] = None):
        """Log audit event"""
        logger.info(f"Logging audit event: {event_type} for user {user_id}")
        # Simulate audit logging
        await asyncio.sleep(0.02)
    
    async def start_consuming(self):
        """Start consuming events from Kafka"""
        logger.info("Starting event consumption...")
        
        # Start consuming user events
        user_task = asyncio.create_task(
            self.kafka_client.consume_events(
                "user-events",
                "worker-service",
                self.process_user_event
            )
        )
        
        # Start consuming booking events
        booking_task = asyncio.create_task(
            self.kafka_client.consume_events(
                "booking-events",
                "worker-service",
                self.process_booking_event
            )
        )
        
        # Start consuming payment events
        payment_task = asyncio.create_task(
            self.kafka_client.consume_events(
                "payment-events",
                "worker-service",
                self.process_payment_event
            )
        )
        
        # Wait for all tasks
        await asyncio.gather(user_task, booking_task, payment_task)

async def main():
    """Main function"""
    logger.info("Starting Enhanced Worker Service...")
    
    # Setup health checks
    health_checker = setup_default_health_checks("worker-service")
    
    # Create event processor
    processor = EventProcessor()
    
    try:
        # Start consuming events
        await processor.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down worker service...")
    except Exception as e:
        logger.error(f"Worker service error: {e}")
    finally:
        # Close Kafka client
        processor.kafka_client.close()

if __name__ == "__main__":
    asyncio.run(main())
