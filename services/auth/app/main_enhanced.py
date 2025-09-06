"""
Enhanced Auth Service with Kafka, Circuit Breaker, and Health Checks
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from .utils import JWT_SECRET, JWT_ALGORITHM, verify_token, is_token_expired
import os
from .models import Base, User
from .schemas import UserCreate, Token, RefreshToken
from .utils import hash_password, verify_password, create_access_token, create_refresh_token
from pydantic import BaseModel
from datetime import datetime, timezone

# Import shared components
import sys
sys.path.append('/app/shared')

# Try to import Kafka client, fallback if not available
try:
    from kafka_client import get_kafka_client, EventTypes, publish_user_event
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("Kafka client not available, continuing without Kafka features")

# Try to import circuit breaker, fallback if not available
try:
    from circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    print("Circuit breaker not available, continuing without circuit breaker features")
# Try to import health module, fallback if not available
try:
    from health import setup_default_health_checks, get_health_checker
    HEALTH_AVAILABLE = True
except ImportError:
    HEALTH_AVAILABLE = False
    print("Health module not available, continuing without health checks")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Enhanced Auth Service", version="2.0.0")

# Add Prometheus instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Setup health checks
# Initialize health checker if available
if HEALTH_AVAILABLE:
    health_checker = setup_default_health_checks("auth-service")
else:
    health_checker = None

# Setup circuit breakers
db_circuit_breaker = get_circuit_breaker("auth-db", CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=30
))

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
    return {"status": "healthy", "service": "auth-service"}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all dependencies"""
    if health_checker:
        return await health_checker.check_all()
    else:
        return {"status": "healthy", "message": "Health checks not available"}

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    if health_checker:
        health_status = await health_checker.check_all()
    else:
        health_status = {"status": "healthy", "message": "Health checks not available"}
    if health_status["status"] == "healthy":
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")

# Enhanced user registration with event publishing
@app.post("/register", response_model=Token)
async def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new user with event publishing"""
    try:
        print(f"Registration attempt for email: {user.email}")
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        print(f"Existing user check completed")
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        print(f"Hashing password for user: {user.email}")
        hashed_password = hash_password(user.password)
        print(f"Password hashed successfully")
        
        db_user = User(
            email=user.email,
            password_hash=hashed_password
        )
        print(f"User object created")
        
        db.add(db_user)
        print(f"User added to session")
        db.commit()
        print(f"Database commit successful")
        db.refresh(db_user)
        print(f"User refresh successful, user ID: {db_user.id}")
        
        # Create tokens
        access_token = create_access_token(subject=str(db_user.id))
        refresh_token = create_refresh_token(subject=str(db_user.id))
        
        # Publish user registered event
        if KAFKA_AVAILABLE:
            background_tasks.add_task(
                publish_user_event,
                EventTypes.USER_REGISTERED,
                str(db_user.id),
                email=user.email
            )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# Enhanced login with event publishing
@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Login user with event publishing"""
    try:
        # Verify user credentials
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        # Create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        # Publish user login event
        if KAFKA_AVAILABLE and background_tasks:
            background_tasks.add_task(
                publish_user_event,
                EventTypes.USER_LOGIN,
                str(user.id),
                email=user.email
            )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

# Enhanced token refresh
@app.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Refresh access token with circuit breaker protection"""
    try:
        # Use circuit breaker for database operations
        async def refresh_token_operation():
            try:
                payload = jwt.decode(refresh_data.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("sub")
                if user_id is None:
                    raise HTTPException(status_code=401, detail="Invalid token")
                
                # Verify user exists
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")
                
                # Create new access token
                access_token = create_access_token(subject=str(user.id))
                
                return Token(
                    access_token=access_token,
                    refresh_token=refresh_data.refresh_token,
                    token_type="bearer",
                    expires_in=1800
                )
                
            except JWTError:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        result = await db_circuit_breaker.call(refresh_token_operation)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

# Enhanced token verification
@app.post("/verify")
async def verify_token_endpoint(token_data: dict, db: Session = Depends(get_db)):
    """Verify token with circuit breaker protection"""
    try:
        async def verify_token_operation():
            token = token_data.get("token")
            if not token:
                raise HTTPException(status_code=400, detail="Token required")
            
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("sub")
                
                if user_id is None:
                    raise HTTPException(status_code=401, detail="Invalid token")
                
                # Verify user exists
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")
                
                return {"valid": True, "user_id": user_id, "email": user.email}
                
            except JWTError:
                raise HTTPException(status_code=401, detail="Invalid token")
        
        result = await db_circuit_breaker.call(verify_token_operation)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token verification failed: {str(e)}")

# Circuit breaker metrics endpoint
@app.get("/metrics/circuit-breakers")
async def circuit_breaker_metrics():
    """Get circuit breaker metrics"""
    from circuit_breaker import get_all_circuit_breakers
    
    breakers = get_all_circuit_breakers()
    return {
        "circuit_breakers": {
            name: breaker.get_metrics() 
            for name, breaker in breakers.items()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
