import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { selectToken } from "../store/authSlice";
import { catalogAPI } from "../utils/api";
import Book from "./Book";

// Event image mapping - you can replace these with actual event images
const getEventImage = (eventTitle) => {
  const images = {
    'Jazz Night': 'https://images.unsplash.com/photo-1511192336575-5a79af67a629?w=400&h=200&fit=crop',
    'Tech Talk: AI': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=200&fit=crop',
    'Rock Concert': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=200&fit=crop',
    'Classical Music': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=200&fit=crop',
    'Comedy Show': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=200&fit=crop',
    'Dance Performance': 'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4?w=400&h=200&fit=crop',
    'Theater Play': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=200&fit=crop',
    'Poetry Reading': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=200&fit=crop'
  };

  // Return specific image or default gradient
  return images[eventTitle] || null;
};

export default function Events({ onBookingComplete }) {
  const token = useSelector(selectToken);
  const [events, setEvents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const response = await catalogAPI.get("/events");
        setEvents(response.data);
      } catch (error) {
        console.error("Failed to fetch events:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const handleBookingComplete = () => {
    setSelected(null);
    if (onBookingComplete) {
      onBookingComplete();
    }
  };

  if (loading) {
    return (
      <div className="loading">
        Loading events...
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header">
        <h1>🎭 Available Events</h1>
        <p className="text-gray-600">Discover amazing events and book your tickets</p>
      </div>

      <div className="events-grid">
        {events.map((event) => {
          const eventImage = getEventImage(event.title);

          return (
            <div key={event.id} className="event-card">
              <div className="event-image">
                {eventImage ? (
                  <img
                    src={eventImage}
                    alt={event.title}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover'
                    }}
                  />
                ) : (
                  <div style={{
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '2rem'
                  }}>
                    🎫
                  </div>
                )}
                <div style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  background: 'rgba(0, 0, 0, 0.7)',
                  color: 'white',
                  padding: '0.5rem 1rem',
                  borderRadius: 'var(--radius-lg)',
                  fontSize: '0.875rem',
                  fontWeight: '600'
                }}>
                  {event.capacity} seats left
                </div>
              </div>

              <div className="event-content">
                <h2 className="event-title">{event.title}</h2>

                <div className="event-meta">
                  <span className="event-venue">📍 {event.venue || 'Venue TBD'}</span>
                  <span className="event-capacity">{event.capacity} available</span>
                </div>

                <p className="event-description">
                  {event.description || 'An exciting event you won\'t want to miss!'}
                </p>

                <div style={{
                  display: 'flex',
                  gap: 'var(--space-3)',
                  marginTop: 'var(--space-4)'
                }}>
                  <button
                    className="btn btn-primary"
                    onClick={() => setSelected(event)}
                    style={{ flex: 1 }}
                  >
                    🎫 Book Now
                  </button>

                  <button
                    className="btn btn-outline"
                    onClick={() => {
                      // Show event details
                      alert(`${event.title}\n\n${event.description || 'No description available'}\n\nVenue: ${event.venue || 'TBD'}\nCapacity: ${event.capacity} seats`);
                    }}
                  >
                    ℹ️ Details
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Book Event</h2>
              <button
                className="btn btn-outline"
                onClick={() => setSelected(null)}
                style={{ padding: '0.5rem', minWidth: 'auto' }}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <Book
                event={selected}
                token={token}
                onClose={handleBookingComplete}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
