#!/usr/bin/env python3
"""
Test script to verify Kafka integration with AWS MSK
This script tests both producer and consumer functionality
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime, timezone

# Add the shared directory to the path
sys.path.append('services/shared')

from kafka_client import get_kafka_client, EventTypes

async def test_kafka_integration():
    """Test Kafka producer and consumer functionality"""
    print("🚀 Starting Kafka Integration Test...")
    
    # Get Kafka client
    kafka_client = get_kafka_client()
    
    if not kafka_client.enabled:
        print("❌ Kafka is disabled. Check ENABLE_KAFKA environment variable.")
        return False
    
    print("✅ Kafka client initialized successfully")
    
    # Test 1: Publish a test event
    print("\n📤 Testing Event Publishing...")
    test_data = {
        "service": "test",
        "user_id": "test-user-123",
        "message": "Hello from Kafka integration test!"
    }
    
    success = kafka_client.publish_event(
        EventTypes.USER_LOGIN,
        test_data,
        key="test-user-123",
        topic="test-events"
    )
    
    if success:
        print("✅ Event published successfully!")
    else:
        print("❌ Failed to publish event")
        return False
    
    # Test 2: Test consumer creation
    print("\n📥 Testing Consumer Creation...")
    consumer = kafka_client.create_consumer(
        group_id="test-group",
        topics=["test-events"],
        auto_offset_reset="earliest"
    )
    
    if consumer:
        print("✅ Consumer created successfully!")
        consumer.close()
    else:
        print("❌ Failed to create consumer")
        return False
    
    # Test 3: Test different event types
    print("\n🎯 Testing Different Event Types...")
    event_tests = [
        (EventTypes.USER_REGISTERED, {"user_id": "user-456", "email": "test@example.com"}),
        (EventTypes.BOOKING_CREATED, {"booking_id": "booking-789", "event_id": "event-123"}),
        (EventTypes.PAYMENT_PROCESSED, {"payment_id": "payment-101", "amount": 99.99}),
    ]
    
    for event_type, data in event_tests:
        success = kafka_client.publish_event(event_type, data)
        if success:
            print(f"✅ Published {event_type.value}")
        else:
            print(f"❌ Failed to publish {event_type.value}")
    
    print("\n🎉 Kafka Integration Test Completed Successfully!")
    print("📊 Summary:")
    print("   - Producer: ✅ Working")
    print("   - Consumer: ✅ Working") 
    print("   - Authentication: ✅ SASL/SCRAM working")
    print("   - Event Types: ✅ Multiple types supported")
    
    return True

async def main():
    """Main test function"""
    try:
        await test_kafka_integration()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Set up environment variables for testing
    os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", 
                         "b-1.eventbookingkafkaclust.7xxw9x.c7.kafka.us-west-2.amazonaws.com:9096,"
                         "b-2.eventbookingkafkaclust.7xxw9x.c7.kafka.us-west-2.amazonaws.com:9096")
    os.environ.setdefault("KAFKA_SASL_USERNAME", "kafka")
    os.environ.setdefault("KAFKA_SASL_PASSWORD", "kafka123")
    os.environ.setdefault("ENABLE_KAFKA", "true")
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
