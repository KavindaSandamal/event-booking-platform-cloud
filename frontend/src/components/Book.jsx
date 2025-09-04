import React, { useState } from "react";
import { bookingAPI } from "../utils/api";
import PaymentModal from "./PaymentModal";

export default function Book({ event, token, onClose, onBooked }) {
  const [seats, setSeats] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [booking, setBooking] = useState(null);

  const doBook = async () => {
    if (seats < 1 || seats > event.capacity) {
      setError("Please select a valid number of seats");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await bookingAPI.post("/book", { event_id: event.id, seats });
      setBooking(res.data);
    } catch (e) {
      setError("Booking failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = () => {
    // Close the payment modal and call onBooked to refresh the parent component
    if (onBooked) {
      onBooked();
    }
    // Close the booking modal
    onClose();
  };

  if (booking) {
    return (
      <PaymentModal
        booking={booking}
        onClose={onClose}
        onSuccess={handlePaymentSuccess}
        token={token}
      />
    );
  }

  return (
    <div>
      <div className="card-header">
        <h2 style={{ margin: 0, fontSize: "1.75rem", fontWeight: "700" }}>
          Book Event: {event.title}
        </h2>
      </div>

      <div className="card-body">
        <div style={{ marginBottom: "var(--space-6)" }}>
          <div style={{
            background: "linear-gradient(135deg, var(--primary-color), var(--primary-dark))",
            color: "white",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-lg)",
            marginBottom: "var(--space-4)"
          }}>
            <h3 style={{ margin: "0 0 var(--space-2) 0", fontSize: "1.25rem" }}>
              Event Details
            </h3>
            <p style={{ margin: "var(--space-1) 0", opacity: 0.9 }}>
              <strong>📍 Venue:</strong> {event.venue || "TBD"}
            </p>
            <p style={{ margin: "var(--space-1) 0", opacity: 0.9 }}>
              <strong>📝 Description:</strong> {event.description || "No description available"}
            </p>
            <p style={{ margin: "var(--space-1) 0", opacity: 0.9 }}>
              <strong>🎫 Available Seats:</strong> {event.capacity}
            </p>
          </div>
        </div>

        <div style={{ marginBottom: "var(--space-6)" }}>
          <label style={{
            display: "block",
            marginBottom: "var(--space-2)",
            fontWeight: "600",
            color: "var(--gray-700)"
          }}>
            Number of Seats
          </label>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
            <button
              className="btn btn-outline"
              onClick={() => setSeats(Math.max(1, seats - 1))}
              disabled={seats <= 1}
              style={{ padding: "var(--space-2) var(--space-3)", minWidth: "auto" }}
            >
              -
            </button>
            <input
              type="number"
              className="input"
              value={seats}
              onChange={(e) => setSeats(parseInt(e.target.value) || 1)}
              min="1"
              max={event.capacity}
              style={{ textAlign: "center", maxWidth: "100px" }}
            />
            <button
              className="btn btn-outline"
              onClick={() => setSeats(Math.min(event.capacity, seats + 1))}
              disabled={seats >= event.capacity}
              style={{ padding: "var(--space-2) var(--space-3)", minWidth: "auto" }}
            >
              +
            </button>
          </div>
          <p style={{
            margin: "var(--space-2) 0 0 0",
            color: "var(--gray-500)",
            fontSize: "0.875rem"
          }}>
            Select between 1 and {event.capacity} seats
          </p>
        </div>

        {error && (
          <div style={{
            color: "var(--danger-color)",
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-3)",
            marginBottom: "var(--space-4)",
            fontSize: "0.875rem"
          }}>
            ⚠️ {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            className="btn btn-primary"
            onClick={doBook}
            disabled={loading}
            style={{ flex: 1 }}
          >
            {loading ? (
              <>
                <div style={{
                  width: "16px",
                  height: "16px",
                  border: "2px solid transparent",
                  borderTop: "2px solid white",
                  borderRadius: "50%",
                  animation: "spin 1s linear infinite"
                }}></div>
                Booking...
              </>
            ) : (
              `🎫 Book ${seats} Seat${seats > 1 ? 's' : ''}`
            )}
          </button>

          <button
            className="btn btn-outline"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
