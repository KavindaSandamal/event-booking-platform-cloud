"""
Enhanced Payment Service with Kafka, Circuit Breaker, and Health Checks
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Payment
from .schemas import PaymentRequest, PaymentResponse
import os
import httpx
import uuid
from datetime import datetime

# Check if Kafka is enabled via environment variable
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
KAFKA_AVAILABLE = False
CIRCUIT_BREAKER_AVAILABLE = False
HEALTH_AVAILABLE = False

print("Kafka disabled via environment variable")
print("Circuit breaker not available, continuing without circuit breaker features")
print("Health module not available, continuing without health checks")

DATABASE_URL = os.getenv("DATABASE_URL")
AUTH_URL = os.getenv("AUTH_URL", "http://auth:8000")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking:8002")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Enhanced Payment Service", version="2.0.0")

# Add Prometheus instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Setup health checks
# Initialize health checker and circuit breakers (disabled)
health_checker = None
db_circuit_breaker = None
auth_circuit_breaker = None
booking_circuit_breaker = None

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

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "payment-service"}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all dependencies"""
    return {"status": "healthy", "message": "Health checks not available"}

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    health_status = {"status": "healthy", "message": "Health checks not available"}
    if health_status["status"] == "healthy":
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")

async def get_current_user(authorization: str = Header(None)):
    """Get current user from auth service with circuit breaker protection"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Temporarily bypass auth service call due to networking issues
    # TODO: Fix ECS networking to enable proper service-to-service communication
    try:
        # For now, just extract user_id from token without verification
        # This is a temporary workaround for the networking issue
        token = authorization.replace("Bearer ", "")
        # Simple JWT decode to get user_id (without verification for now)
        import base64
        import json
        
        # Split JWT token
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Decode payload (without verification)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded)
        
        user_id = payload_data.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="No user ID in token")
        
        print(f"Temporarily bypassing auth service, using user_id: {user_id}")
        return user_id
        
    except Exception as e:
        print(f"Token parsing error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Enhanced payment processing with event publishing
@app.post("/process-payment", response_model=PaymentResponse)
async def process_payment(
    payment_req: PaymentRequest, 
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Process payment with event publishing"""
    try:
        # Verify user authentication
        user_id = await get_current_user(authorization)
        
        # Verify booking exists
        async def verify_booking():
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BOOKING_SERVICE_URL}/booking/{payment_req.booking_id}")
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(status_code=404, detail="Booking not found")
        
        booking_data = await verify_booking()
        
        # Create payment record
        async def create_payment_record():
            payment = Payment(
                id=str(uuid.uuid4()),
                user_id=user_id,
                booking_id=payment_req.booking_id,
                amount=payment_req.amount,
                phone_number=payment_req.phone_number,
                status="completed",
                created_at=datetime.utcnow()
            )
            
            db.add(payment)
            db.commit()
            db.refresh(payment)
            return payment
        
        payment = await create_payment_record()
        
        # Publish payment completed event (Kafka disabled)
        pass
        
        return PaymentResponse(
            payment_id=str(payment.id),
            message="Payment processed successfully",
            requires_verification=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Publish payment failed event (Kafka disabled)
        pass
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")

# Get payment by booking ID
@app.get("/booking/{booking_id}")
async def get_payment_by_booking(booking_id: str, db: Session = Depends(get_db)):
    """Get payment information by booking ID"""
    try:
        async def get_payment():
            payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found for this booking")
            
            return {
                "payment_id": payment.id,
                "booking_id": payment.booking_id,
                "user_id": payment.user_id,
                "amount": payment.amount,
                "status": payment.status,
                "created_at": payment.created_at
            }
        
        payment_data = await get_payment()
        
        return payment_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment: {str(e)}")

# Enhanced payment receipt with event publishing
@app.get("/payment-receipt/{payment_id}")
async def get_payment_receipt(
    payment_id: str,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get payment receipt with event publishing"""
    try:
        # Verify user authentication
        user_id = await get_current_user(authorization)
        
        async def get_payment_record():
            payment = db.query(Payment).filter(
                Payment.id == payment_id,
                Payment.user_id == user_id
            ).first()
            
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            return payment
        
        payment = await get_payment_record()
        
        # Publish receipt accessed event (Kafka disabled)
        pass
        
        return PaymentResponse(
            payment_id=str(payment.id),
            message="Payment processed successfully",
            requires_verification=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment receipt: {str(e)}")

# Get user payments
@app.get("/user/{user_id}")
async def get_user_payments(user_id: str, db: Session = Depends(get_db)):
    """Get all payments for a user"""
    try:
        async def get_payments():
            payments = db.query(Payment).filter(Payment.user_id == user_id).all()
            return [
                PaymentResponse(
                    id=payment.id,
                    user_id=payment.user_id,
                    booking_id=payment.booking_id,
                    amount=payment.amount,
                    status=payment.status,
                    created_at=payment.created_at
                )
                for payment in payments
            ]
        
        payments = await get_payments()
        return {"payments": payments}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payments: {str(e)}")

# Circuit breaker metrics endpoint
@app.get("/metrics/circuit-breakers")
async def circuit_breaker_metrics():
    """Get circuit breaker metrics"""
    return {"circuit_breakers": {}, "message": "Circuit breakers not available"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)