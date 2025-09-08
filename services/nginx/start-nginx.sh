#!/bin/sh

# Wait for services to be available
echo "Waiting for services to be available..."

# Function to check if a service is available by testing the port
check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=60
    local attempt=1
    
    echo "Checking $service_name:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $service_name $port 2>/dev/null; then
            echo "$service_name is available"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "Warning: $service_name not available after $max_attempts attempts"
    return 1
}

# Check all services on localhost
check_service "localhost" "8000"
check_service "localhost" "8001"
check_service "localhost" "8002"
check_service "localhost" "8003"
check_service "localhost" "3000"

echo "All services are available, starting nginx..."
exec nginx -g "daemon off;"
