#!/usr/bin/env python3
import requests
import json

# Try to get database info through the services
services = [
    "http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/auth/health/detailed",
    "http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/catalog/health/detailed", 
    "http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/booking/health/detailed",
    "http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/payment/health/detailed"
]

print("=== CHECKING SERVICE HEALTH AND DATABASE CONNECTIONS ===\n")

for service_url in services:
    try:
        response = requests.get(service_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            service_name = service_url.split('/')[-2]
            print(f"--- {service_name.upper()} SERVICE ---")
            print(f"Status: {data.get('status', 'unknown')}")
            
            if 'dependencies' in data:
                print("Dependencies:")
                for dep_name, dep_info in data['dependencies'].items():
                    status = dep_info.get('status', 'unknown')
                    print(f"  {dep_name}: {status}")
                    if 'error' in dep_info:
                        print(f"    Error: {dep_info['error']}")
            print()
        else:
            print(f"Service {service_url} returned status {response.status_code}")
    except Exception as e:
        print(f"Error checking {service_url}: {e}")

# Try to get events to see what the catalog service returns
print("=== TESTING CATALOG SERVICE EVENTS ENDPOINT ===")
try:
    response = requests.get("http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/catalog/events", timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        events = response.json()
        print(f"Events returned: {len(events)}")
        if events:
            print("Sample event structure:")
            print(json.dumps(events[0], indent=2, default=str))
    else:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
