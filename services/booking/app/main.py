from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from .models import Base, Booking
from .schemas import BookingRequest, BookingOut
import redis
import uuid
import json
import aio_pika
import asyncio
import httpx
from typing import List
from prometheus_fastapi_instrumentator import Instrumentator
import sys
import os
from datetime import datetime, timezone
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from circuit_breaker import CircuitBreaker, retry_async, RetryConfig

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
CATALOG_URL = os.getenv("CATALOG_URL")
AUTH_URL = os.getenv("AUTH_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

r = redis.from_url(REDIS_URL, decode_responses=True)

# Circuit breakers for external service calls
catalog_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
auth_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

app = FastAPI(title="Booking Service")
Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enhanced auth with circuit breaker and retry
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing auth")
    token = authorization.split(" ")[1]
    
    async def verify_token_with_auth_service():
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{AUTH_URL}/verify", json={"token": token}, timeout=5.0)
            if resp.status_code == 200:
                return resp.json()["user_id"]
            else:
                raise HTTPException(401, "Token verification failed")
    
    try:
        # Use circuit breaker and retry for auth service call
        user_id = await auth_circuit_breaker.call(
            retry_async,
            verify_token_with_auth_service,
            config=RetryConfig(max_attempts=3, base_delay=1.0)
        )
        return user_id
    except Exception:
        # Fallback for demo purposes
        try:
            uid = uuid.UUID(token)
            return str(uid)
        except:
            raise HTTPException(401, "Invalid token")

@app.post("/book", response_model=BookingOut)
async def create_booking(req: BookingRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = await get_current_user(authorization)
    event_key = f"event:{req.event_id}:capacity"
    lock_key = f"lock:{req.event_id}:{user_id}"
    
    # Get event capacity from catalog service with circuit breaker
    async def get_event_from_catalog():
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{CATALOG_URL}/events/{req.event_id}", timeout=5.0)
            if resp.status_code != 200:
                raise HTTPException(400, "Event not found")
            return resp.json()
    
    try:
        event = await catalog_circuit_breaker.call(
            retry_async,
            get_event_from_catalog,
            config=RetryConfig(max_attempts=3, base_delay=1.0)
        )
        capacity = event.get("capacity", 0)
    except Exception as e:
        raise HTTPException(503, f"Catalog service unavailable: {str(e)}")

    # Basic lock using Redis setnx
    # We'll store 'reserved' count per event in redis
    reserved = r.get(event_key)
    if reserved is None:
        r.set(event_key, 0)
        reserved = 0
    reserved = int(reserved)

    if reserved + req.seats > capacity:
        raise HTTPException(400, "Not enough seats available")

    # create tentative booking (pending) in DB
    booking = Booking(user_id=user_id, event_id=str(req.event_id), seats=req.seats, status="pending")
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # increment reserved atomically
    new_reserved = r.incrby(event_key, req.seats)

    # Update event capacity in catalog service
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(f"{CATALOG_URL}/events/{req.event_id}/capacity?seats={req.seats}")
            if resp.status_code != 200:
                print(f"Failed to update event capacity: {resp.text}")
    except Exception as e:
        print(f"Error updating event capacity: {e}")

    # publish to RabbitMQ for asynchronous processing (e.g., payment & notification)
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("booking_queue", durable=True)
            payload = {"booking_id": str(booking.id), "user_id": user_id, "event_id": str(req.event_id), "seats": req.seats}
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(payload).encode()),
                routing_key="booking_queue"
            )
    except Exception as e:
        print(f"Failed to publish to RabbitMQ: {e}")
        # In production, you might want to handle this differently

    return booking

@app.get("/my-bookings", response_model=List[BookingOut])
async def get_user_bookings(authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = await get_current_user(authorization)
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    return bookings

@app.put("/confirm-booking/{booking_id}")
async def confirm_booking(booking_id: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    booking.status = "confirmed"
    db.commit()
    db.refresh(booking)
    return {"message": "Booking confirmed successfully", "booking": booking}

@app.get("/booking-payment/{booking_id}")
async def get_booking_payment(booking_id: str, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = await get_current_user(authorization)
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == user_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Try to find payment info from payment service
    try:
        async with httpx.AsyncClient() as client:
            # Query payment service to find payment by booking_id
            payment_url = os.getenv("PAYMENT_URL", "http://payment:8000")
            resp = await client.get(f"{payment_url}/payment-by-booking/{booking_id}")
            if resp.status_code == 200:
                payment_data = resp.json()
                return {"payment_id": payment_data.get("payment_id"), "status": booking.status}
            else:
                return {"payment_id": None, "status": booking.status}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe - checks if service can accept traffic"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        # Check Redis connection
        r.ping()
        return {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@app.get("/health/live")
def liveness_check():
    """Liveness probe - checks if service is alive"""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
