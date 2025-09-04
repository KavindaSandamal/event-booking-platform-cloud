import React, { useState } from "react";
import { paymentAPI } from "../utils/api";

export default function PaymentModal({ booking, onClose, onSuccess, token }) {
    const [phoneNumber, setPhoneNumber] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const calculateAmount = () => {
        return booking.seats * 10; // $10 per seat
    };

    const handlePayment = async (e) => {
        e.preventDefault();

        if (!phoneNumber.trim()) {
            setError("Please enter a phone number");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await paymentAPI.post("/process-payment", {
                booking_id: booking.id,
                amount: calculateAmount(),
                phone_number: phoneNumber
            });

            // Check if payment was successful
            if (response.data && response.data.payment_id) {
                // Payment successful - call onSuccess to close modal and navigate
                onSuccess();
            } else {
                setError("Payment failed: Unexpected response format");
            }
        } catch (err) {
            setError("Payment failed: " + (err?.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="card-header">
                <h2 style={{ margin: 0, fontSize: "1.75rem", fontWeight: "700" }}>
                    💳 Complete Payment
                </h2>
            </div>

            <div className="card-body">
                <div style={{ marginBottom: "var(--space-6)" }}>
                    <div style={{
                        background: "linear-gradient(135deg, var(--secondary-color), #059669)",
                        color: "white",
                        padding: "var(--space-4)",
                        borderRadius: "var(--radius-lg)",
                        marginBottom: "var(--space-4)"
                    }}>
                        <h3 style={{ margin: "0 0 var(--space-2) 0", fontSize: "1.25rem" }}>
                            Booking Summary
                        </h3>
                        <p style={{ margin: "var(--space-1) 0", opacity: 0.9 }}>
                            <strong>🎫 Seats:</strong> {booking.seats}
                        </p>
                        <p style={{ margin: "var(--space-1) 0", opacity: 0.9 }}>
                            <strong>💰 Total Amount:</strong> ${calculateAmount()}
                        </p>
                        <p style={{ margin: "var(--space-1) 0", opacity: 0.9 }}>
                            <strong>🆔 Booking ID:</strong> {booking.id}
                        </p>
                    </div>
                </div>

                <form onSubmit={handlePayment}>
                    <div style={{ marginBottom: "var(--space-6)" }}>
                        <label style={{
                            display: "block",
                            marginBottom: "var(--space-2)",
                            fontWeight: "600",
                            color: "var(--gray-700)"
                        }}>
                            📱 Phone Number
                        </label>
                        <input
                            type="tel"
                            className="input"
                            placeholder="Enter your phone number"
                            value={phoneNumber}
                            onChange={(e) => setPhoneNumber(e.target.value)}
                            required
                        />
                        <p style={{
                            margin: "var(--space-2) 0 0 0",
                            color: "var(--gray-500)",
                            fontSize: "0.875rem"
                        }}>
                            We'll send payment confirmation to this number
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
                            type="submit"
                            className="btn btn-secondary"
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
                                    Processing Payment...
                                </>
                            ) : (
                                `💳 Pay $${calculateAmount()}`
                            )}
                        </button>

                        <button
                            type="button"
                            className="btn btn-outline"
                            onClick={onClose}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
} 