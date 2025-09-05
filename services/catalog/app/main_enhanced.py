"""
Enhanced Catalog Service with Kafka, Circuit Breaker, and Health Checks
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Event
from .schemas import EventIn, EventOut
import os
from datetime import datetime

# Import shared components
import sys
sys.path.append('/app/shared')
# Try to import Kafka client, fallback if not available
try:
    from kafka_client import get_kafka_client, publish_event, EventTypes
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

app = FastAPI(title="Enhanced Catalog Service", version="2.0.0")

# Add Prometheus instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Setup health checks
# Initialize health checker if available
if HEALTH_AVAILABLE:
    health_checker = setup_default_health_checks("catalog-service")
else:
    health_checker = None

# Setup circuit breakers
db_circuit_breaker = get_circuit_breaker("catalog-db", CircuitBreakerConfig(
    failure_threshold=3,
    success_threshold=2,
    timeout=30
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
    return {"status": "healthy", "service": "catalog-service"}

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

# Enhanced event creation with event publishing
@app.post("/events", response_model=EventOut)
async def create_event(
    event: EventIn, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new event with event publishing"""
    try:
        async def create_event_record():
            db_event = Event(
                title=event.title,
                description=event.description,
                date=event.date,
                location=event.location,
                capacity=event.capacity,
                price=event.price,
                created_at=datetime.utcnow()
            )
            
            db.add(db_event)
            db.commit()
            db.refresh(db_event)
            return db_event
        
        db_event = await db_circuit_breaker.call(create_event_record)
        
        # Publish event created event
        background_tasks.add_task(
            publish_event,
            EventTypes.EVENT_CREATED,
            str(db_event.id),
            title=event.title,
            location=event.location,
            capacity=event.capacity
        )
        
        return EventOut(
            id=str(db_event.id),
            title=db_event.title,
            description=db_event.description,
            date=db_event.date,
            location=db_event.location,
            capacity=db_event.capacity,
            price=db_event.price,
            created_at=db_event.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event creation failed: {str(e)}")

# Enhanced event update with event publishing
@app.put("/events/{event_id}", response_model=EventOut)
async def update_event(
    event_id: str,
    event: EventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update an event with event publishing"""
    try:
        async def update_event_record():
            db_event = db.query(Event).filter(Event.id == event_id).first()
            if not db_event:
                raise HTTPException(status_code=404, detail="Event not found")
            
            db_event.title = event.title
            db_event.description = event.description
            db_event.date = event.date
            db_event.location = event.location
            db_event.capacity = event.capacity
            db_event.price = event.price
            db_event.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_event)
            return db_event
        
        db_event = await db_circuit_breaker.call(update_event_record)
        
        # Publish event updated event
        background_tasks.add_task(
            publish_event,
            EventTypes.EVENT_UPDATED,
            str(db_event.id),
            title=event.title,
            location=event.location,
            capacity=event.capacity
        )
        
        return EventOut(
            id=str(db_event.id),
            title=db_event.title,
            description=db_event.description,
            date=db_event.date,
            location=db_event.location,
            capacity=db_event.capacity,
            price=db_event.price,
            created_at=db_event.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event update failed: {str(e)}")

# Enhanced event deletion with event publishing
@app.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Delete an event with event publishing"""
    try:
        async def delete_event_record():
            db_event = db.query(Event).filter(Event.id == event_id).first()
            if not db_event:
                raise HTTPException(status_code=404, detail="Event not found")
            
            # Store event data for event publishing
            event_data = {
                "title": db_event.title,
                "location": db_event.location,
                "capacity": db_event.capacity
            }
            
            db.delete(db_event)
            db.commit()
            
            return event_data
        
        event_data = await db_circuit_breaker.call(delete_event_record)
        
        # Publish event deleted event
        background_tasks.add_task(
            publish_event,
            EventTypes.EVENT_DELETED,
            event_id,
            title=event_data["title"],
            location=event_data["location"],
            capacity=event_data["capacity"]
        )
        
        return {"message": "Event deleted successfully", "event_id": event_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event deletion failed: {str(e)}")

# Get all events
@app.get("/events")
async def get_events(db: Session = Depends(get_db)):
    """Get all events"""
    try:
        async def get_events_from_db():
            events = db.query(Event).all()
            return [
                EventOut(
                    id=str(event.id),
                    title=event.title,
                    description=event.description,
                    date=event.date,
                    location=event.location,
                    capacity=event.capacity,
                    price=event.price,
                    created_at=event.created_at
                )
                for event in events
            ]
        
        events = await db_circuit_breaker.call(get_events_from_db)
        return {"events": events}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")

# Get single event
@app.get("/events/{event_id}")
async def get_event(event_id: str, db: Session = Depends(get_db)):
    """Get a single event"""
    try:
        async def get_event_from_db():
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                raise HTTPException(status_code=404, detail="Event not found")
            
            return EventOut(
                id=str(event.id),
                title=event.title,
                description=event.description,
                date=event.date,
                location=event.location,
                capacity=event.capacity,
                price=event.price,
                created_at=event.created_at
            )
        
        event = await db_circuit_breaker.call(get_event_from_db)
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event: {str(e)}")

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
    uvicorn.run(app, host="0.0.0.0", port=8001)
