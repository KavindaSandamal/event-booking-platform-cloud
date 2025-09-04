from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from .models import Base, Event
from .schemas import EventIn, EventOut
from typing import List
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Catalog Service")
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # seed events if empty
    db = SessionLocal()
    try:
        count = db.query(Event).count()
        if count == 0:
            events = [
                Event(
                    title="Jazz Night", 
                    description="An enchanting evening of smooth jazz melodies featuring local and international artists. Perfect for a romantic date night or relaxing with friends.", 
                    capacity=50, 
                    venue="Blue Note Jazz Club"
                ),
                Event(
                    title="Tech Talk: AI", 
                    description="Join industry experts for an insightful discussion on the future of artificial intelligence, machine learning, and their impact on society.", 
                    capacity=100, 
                    venue="Tech Innovation Center"
                ),
                Event(
                    title="Rock Concert", 
                    description="An electrifying rock concert featuring multiple bands with high-energy performances and amazing stage effects.", 
                    capacity=200, 
                    venue="Metro Arena"
                ),
                Event(
                    title="Classical Music", 
                    description="Experience the timeless beauty of classical music performed by a full orchestra in an elegant setting.", 
                    capacity=150, 
                    venue="Symphony Hall"
                ),
                Event(
                    title="Comedy Show", 
                    description="Laugh the night away with top comedians delivering hilarious stand-up performances and witty humor.", 
                    capacity=80, 
                    venue="Comedy Club Downtown"
                ),
                Event(
                    title="Dance Performance", 
                    description="A mesmerizing contemporary dance performance showcasing innovative choreography and artistic expression.", 
                    capacity=120, 
                    venue="Modern Dance Theater"
                ),
                Event(
                    title="Theater Play", 
                    description="A compelling theatrical production featuring talented actors in an intimate theater setting.", 
                    capacity=90, 
                    venue="Community Theater"
                ),
                Event(
                    title="Poetry Reading", 
                    description="An inspiring evening of poetry readings by established and emerging poets in a cozy literary atmosphere.", 
                    capacity=60, 
                    venue="Bookstore Cafe"
                )
            ]
            db.add_all(events)
            db.commit()
            print(f"Seeded {len(events)} events successfully!")
    finally:
        db.close()

@app.get("/events", response_model=List[EventOut])
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return events

@app.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Not found")
    return event

@app.post("/events", response_model=EventOut)
def create_event(payload: EventIn, db: Session = Depends(get_db)):
    event = Event(**payload.dict())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@app.put("/events/{event_id}/capacity")
def update_event_capacity(event_id: str, seats: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    
    if event.capacity < seats:
        raise HTTPException(400, "Not enough capacity available")
    
    event.capacity -= seats
    db.commit()
    db.refresh(event)
    return {"message": "Capacity updated successfully", "remaining_capacity": event.capacity}


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
