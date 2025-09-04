# Event Booking Platform Architecture

## Overview

This platform is a microservices-based event ticket booking system designed for scalability, high availability, and extensibility. It is deployed on a single VM with 8GB RAM and 25GB storage.

- **Microservices**: Each service runs independently and can be scaled horizontally by running multiple containers of bottleneck services (e.g., booking, payment).
- **Stateless Services**: Services are stateless; session and cache data are stored in Redis, allowing easy scaling and failover.
- **Resource Limits**: Docker Compose can set CPU and memory limits for each service to optimize resource usage on the VM.
- **Load Balancing**: For production, a reverse proxy (e.g., Nginx, HAProxy) can distribute traffic across service instances. On a single VM, this can help balance requests between containers.
- **Database Connection Pooling**: Use connection pooling in PostgreSQL and Redis to handle concurrent requests efficiently.
- **Asynchronous Processing**: RabbitMQ and the worker service allow background processing, reducing load on main services during peak times.
- **Monitoring**: Add monitoring tools (Prometheus, Grafana) to track resource usage and scale services as needed.

## System Architecture

### Microservices

- **Auth Service**: Handles JWT authentication and user management.
- **Catalog Service**: Manages event listings and details.
- **Booking Service**: Manages bookings, seat reservations, and booking history.
- **Payment Service**: Handles payment processing and receipts.
- **Worker Service**: Processes background tasks (e.g., notifications) via RabbitMQ.
- **Frontend**: React SPA for user interaction.

### Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React 18 + Vite
- **Database**: PostgreSQL
- **Cache**: Redis
- **Message Queue**: RabbitMQ
- **Containerization**: Docker & Docker Compose

## Deployment Plan

- All services are containerized using Docker.
- Docker Compose orchestrates the services on a single VM.
- PostgreSQL and Redis run as containers for persistence and caching.
- RabbitMQ is used for asynchronous communication and background tasks.
- The frontend React app is served via its own container.
- Environment variables are managed via `.env` files.
- Access points:
  - Frontend: http://localhost:3000
  - Auth Service: http://localhost:8001
  - Catalog Service: http://localhost:8002
  - Booking Service: http://localhost:8003
  - Payment Service: http://localhost:8004

## Resource Allocation

## High Availability & Health Checks

While running on a single VM, the platform uses several strategies to maximize uptime and reliability:

- **Service Redundancy**: Critical services can run multiple containers (if resources allow) to reduce downtime risk. On a single VM, this is limited by available RAM/CPU.
- **Database Reliability**: PostgreSQL and Redis can be configured with persistence and backups. For production, enable WAL archiving and regular backups for PostgreSQL.
- **Health Checks**: Docker Compose supports health checks for containers. FastAPI services can expose `/health` endpoints for readiness and liveness probes.
- **Automatic Restarts**: Docker Compose can restart failed containers automatically (`restart: always`).
- **Monitoring**: Use monitoring tools to detect failures and alert administrators.

### Example Health Check Endpoint (FastAPI)

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

### Docker Compose Health Check Example

```yaml
services:
  booking:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Future Cloud Migration

In cloud environments, use Kubernetes readiness/liveness probes and multi-zone deployments for true high availability.

Next steps will cover scalability improvements.

## Communication Between Services

### Synchronous Communication (REST API)

Services communicate directly using HTTP REST APIs. For example, the Booking service calls the Catalog service to check event capacity:

```python
# In Booking Service
import httpx

async with httpx.AsyncClient() as client:
  resp = await client.get(f"{CATALOG_URL}/events/{event_id}")
  event = resp.json()
```

### Asynchronous Communication (RabbitMQ)

RabbitMQ is used for background tasks and decoupled event processing. For example, the Booking service publishes a message to RabbitMQ when a booking is created, and the Worker service consumes it:

**Publishing a message (Booking Service):**

```python
import aio_pika
import json

connection = await aio_pika.connect_robust(RABBITMQ_URL)
async with connection:
  channel = await connection.channel()
  queue = await channel.declare_queue("booking_queue", durable=True)
  payload = {"booking_id": str(booking.id), "user_id": user_id, "event_id": str(event_id), "seats": seats}
  await channel.default_exchange.publish(
    aio_pika.Message(body=json.dumps(payload).encode()),
    routing_key="booking_queue"
  )
```

**Consuming a message (Worker Service):**

```python
import aio_pika
import asyncio

async def main():
  connection = await aio_pika.connect_robust(RABBITMQ_URL)
  channel = await connection.channel()
  queue = await channel.declare_queue("booking_queue", durable=True)

  async with queue.iterator() as queue_iter:
    async for message in queue_iter:
      async with message.process():
        data = json.loads(message.body)
        # Process booking event (e.g., send notification)

asyncio.run(main())
```

This approach allows services to communicate efficiently and reliably, supporting both real-time and background workflows.
