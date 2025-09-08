from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import json
from datetime import datetime, timezone
from .models import Base, Payment
from .schemas import PaymentRequest, PaymentResponse
import httpx
import uuid

DATABASE_URL = os.getenv("DATABASE_URL")
AUTH_URL = os.getenv("AUTH_URL")
BOOKING_URL = os.getenv("BOOKING_SERVICE_URL")

# Initialize database connection lazily
engine = None
SessionLocal = None

app = FastAPI(title="Payment Service")
from prometheus_fastapi_instrumentator import Instrumentator
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
    global engine, SessionLocal
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        print("WARNING: DATABASE_URL not set, database operations will fail")
    
    # Debug: Print registered routes
    print("DEBUG: Registered routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"  {route.methods} {route.path}")

def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple auth: expect Authorization: Bearer <token>
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing auth")
    token = authorization.split(" ")[1]
    
    # Verify token via auth service
    if not AUTH_URL:
        raise HTTPException(503, "Auth service not configured")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{AUTH_URL}/verify", json={"token": token}, timeout=5.0)
            if resp.status_code == 200:
                return resp.json()["user_id"]
        except Exception as e:
            print(f"Auth verification failed: {e}")
            pass
    
    raise HTTPException(401, "Invalid token")

@app.post("/process", response_model=PaymentResponse)
async def process_payment_simple(payment_data: dict, authorization: str = Header(None), db: Session = Depends(get_db)):
    """Simple payment processing endpoint for frontend"""
    try:
        # Extract payment data
        event_id = payment_data.get("event_id")
        seats = payment_data.get("seats", 1)
        amount = payment_data.get("amount")
        payment_method = payment_data.get("payment_method", {})
        
        # For demo purposes, we'll create a simple payment record
        payment = Payment(
            user_id="demo_user",  # In real app, get from JWT token
            booking_id=str(uuid.uuid4()),
            amount=amount,
            phone_number=payment_method.get("name", "Demo User"),
            status="completed"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return PaymentResponse(
            payment_id=str(payment.id),
            message="Payment processed successfully",
            requires_verification=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")

@app.post("/process-payment", response_model=PaymentResponse)
async def process_payment(payment_req: PaymentRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    print("DEBUG: /process-payment endpoint called")
    user_id = await get_current_user(authorization)
    
    # Create payment record
    payment = Payment(
        user_id=user_id,
        booking_id=payment_req.booking_id,
        amount=payment_req.amount,
        phone_number=payment_req.phone_number,
        status="completed"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Update booking status to confirmed
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(f"{BOOKING_URL}/confirm-booking/{payment_req.booking_id}")
            if resp.status_code != 200:
                print(f"Failed to confirm booking: {resp.text}")
    except Exception as e:
        print(f"Error confirming booking: {e}")
    
    return PaymentResponse(
        payment_id=str(payment.id),
        message="Payment processed successfully",
        requires_verification=False
    )

@app.get("/payment-receipt/{payment_id}")
async def get_payment_receipt(payment_id: str, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = await get_current_user(authorization)
    
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user_id
    ).first()
    
    if not payment:
        raise HTTPException(404, "Payment not found")
    
    return {
        "payment_id": str(payment.id),
        "amount": payment.amount,
        "status": payment.status,
        "created_at": payment.created_at,
        "phone_number": payment.phone_number
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe - checks if service can accept traffic"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        return {"status": "ready", "checks": {"database": "ok"}}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@app.get("/health/live")
def liveness_check():
    """Liveness probe - checks if service is alive"""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/payment-by-booking/{booking_id}")
async def get_payment_by_booking(booking_id: str, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = await get_current_user(authorization)
    
    payment = db.query(Payment).filter(
        Payment.booking_id == booking_id,
        Payment.user_id == user_id
    ).first()
    
    if not payment:
        raise HTTPException(404, "Payment not found for this booking")
    
    return {
        "payment_id": str(payment.id),
        "amount": payment.amount,
        "status": payment.status,
        "created_at": payment.created_at,
        "phone_number": payment.phone_number
    } 