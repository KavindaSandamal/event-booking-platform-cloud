from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
from .utils import JWT_SECRET, JWT_ALGORITHM, verify_token, is_token_expired
import os
import sys
from .models import Base, User
from .schemas import UserCreate, Token, RefreshToken
from .utils import hash_password, verify_password, create_access_token, create_refresh_token
from pydantic import BaseModel
from datetime import datetime, timezone

# Add shared directory to path for Kafka client
sys.path.append('/app/shared')
from kafka_client import get_kafka_client, EventTypes

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Auth Service")
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
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Hash password before storing
    user = User(email=user_in.email, password_hash=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Publish user registration event to Kafka
    try:
        kafka_client = get_kafka_client()
        kafka_client.publish_event(
            EventTypes.USER_REGISTERED,
            {
                "user_id": str(user.id),
                "email": user.email,
                "service": "auth"
            },
            key=str(user.id),
            topic="user-events"
        )
    except Exception as e:
        # Log error but don't fail the registration
        print(f"Failed to publish user registration event: {e}")

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutes in seconds
    }

class LoginModel(BaseModel):
    email: str
    password: str

@app.post("/login", response_model=Token)
def login(credentials: LoginModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    # Verify password using hash
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutes in seconds
    }

@app.post("/refresh", response_model=Token)
def refresh_token(refresh_token_req: RefreshToken, db: Session = Depends(get_db)):
    # Verify refresh token
    payload = verify_token(refresh_token_req.refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Check if user still exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new tokens
    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))
    
    return {
        "access_token": new_access_token, 
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutes in seconds
    }

@app.post("/verify")
def verify_token_endpoint(payload: dict):
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    # Check if token is expired
    if is_token_expired(token):
        raise HTTPException(status_code=401, detail="Token has expired")
    
    # Verify token
    token_payload = verify_token(token, "access")
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "user_id": token_payload.get("sub"),
        "exp": token_payload.get("exp"),
        "iat": token_payload.get("iat")
    }

@app.post("/logout")
def logout():
    # In a real application, you might want to blacklist the token
    # For now, we'll just return success
    return {"message": "Successfully logged out"}

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


