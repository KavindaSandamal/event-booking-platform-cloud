import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { selectToken } from "../store/authSlice";
import { bookingAPI, catalogAPI, paymentAPI } from "../utils/api";
import { generateTicketPDF, generateReceiptPDF } from "../utils/pdfGenerator";

export default function MyBookings() {
    const token = useSelector(selectToken);
    const [bookings, setBookings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [events, setEvents] = useState({});
    const [paymentReceipts, setPaymentReceipts] = useState({});
    const [generatingPDF, setGeneratingPDF] = useState(false);

    useEffect(() => {
        fetchBookings();
        fetchEvents();
    }, []);

    const fetchBookings = async () => {
        try {
            const response = await bookingAPI.get("/my-bookings");
            setBookings(response.data);

            // Fetch payment receipts for each booking
            const paymentPromises = response.data
                .filter(booking => booking.status === "confirmed")
                .map(async (booking) => {
                    try {
                        // First try to get payment info from the booking service
                        const paymentResponse = await bookingAPI.get(`/booking-payment/${booking.id}`);

                        if (paymentResponse.data.payment_id) {
                            // Now fetch the payment receipt using the payment ID
                            const receiptResponse = await paymentAPI.get(`/payment-receipt/${paymentResponse.data.payment_id}`);
                            return {
                                bookingId: booking.id,
                                receipt: receiptResponse.data
                            };
                        }
                    } catch (error) {
                        console.log("No payment receipt found for booking:", booking.id);
                        return null;
                    }
                });

            // Wait for all payment receipt requests to complete
            const paymentResults = await Promise.all(paymentPromises);

            // Update payment receipts state
            const newPaymentReceipts = {};
            paymentResults.forEach(result => {
                if (result && result.receipt) {
                    newPaymentReceipts[result.bookingId] = result.receipt;
                }
            });
            setPaymentReceipts(newPaymentReceipts);
        } catch (error) {
            console.error("Failed to fetch bookings:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchEvents = async () => {
        try {
            const response = await catalogAPI.get("/events");
            const eventsMap = {};
            response.data.forEach(event => {
                eventsMap[event.id] = event;
            });
            setEvents(eventsMap);
        } catch (error) {
            console.error("Failed to fetch events:", error);
        }
    };

    const downloadPaymentReceipt = async (bookingId) => {
        const receipt = paymentReceipts[bookingId];
        const booking = bookings.find(b => b.id === bookingId);
        const event = events[booking.event_id];

        if (!receipt || !booking || !event) {
            alert("Receipt information not available");
            return;
        }

        setGeneratingPDF(true);
        try {
            await generateReceiptPDF(receipt, booking, event);
        } catch (error) {
            console.error("Error generating receipt PDF:", error);
            alert("Failed to generate receipt PDF");
        } finally {
            setGeneratingPDF(false);
        }
    };

    const downloadTicket = async (booking) => {
        const event = events[booking.event_id];
        if (!event) {
            alert("Event information not available");
            return;
        }

        setGeneratingPDF(true);
        try {
            const receipt = paymentReceipts[booking.id];
            await generateTicketPDF(booking, event, receipt);
        } catch (error) {
            console.error("Error generating ticket PDF:", error);
            alert("Failed to generate ticket PDF");
        } finally {
            setGeneratingPDF(false);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                Loading your bookings...
            </div>
        );
    }

    if (bookings.length === 0) {
        return (
            <div className="text-center" style={{ padding: "var(--space-12) 0" }}>
                <div style={{ fontSize: "4rem", marginBottom: "var(--space-4)" }}>📋</div>
                <h3 style={{ marginBottom: "var(--space-2)" }}>No Bookings Yet</h3>
                <p style={{ color: "var(--gray-600)" }}>You haven't made any bookings yet. Start by browsing events!</p>
            </div>
        );
    }

    return (
        <div>
            <div className="header">
                <h1>📋 My Bookings</h1>
                <p style={{ color: "var(--gray-600)", margin: 0 }}>Manage your event tickets and payments</p>
            </div>

            {generatingPDF && (
                <div style={{
                    position: "fixed",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)",
                    backgroundColor: "rgba(0, 0, 0, 0.8)",
                    color: "white",
                    padding: "var(--space-6)",
                    borderRadius: "var(--radius-xl)",
                    zIndex: 1000,
                    backdropFilter: "blur(10px)"
                }}>
                    <div className="flex items-center gap-3">
                        <div style={{
                            width: '20px',
                            height: '20px',
                            border: '2px solid transparent',
                            borderTop: '2px solid white',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite'
                        }}></div>
                        📄 Generating PDF... Please wait
                    </div>
                </div>
            )}

            <div style={{ display: "grid", gap: "var(--space-6)", padding: "var(--space-6)" }}>
                {bookings.map((booking) => {
                    const event = events[booking.event_id];
                    const receipt = paymentReceipts[booking.id];

                    return (
                        <div key={booking.id} className="card">
                            <div className="card-header">
                                <div className="flex justify-between items-center">
                                    <h3 style={{ margin: 0, fontSize: "1.5rem", fontWeight: "700" }}>
                                        {event ? event.title : "Unknown Event"}
                                    </h3>
                                    <span className={`status-badge status-${booking.status}`}>
                                        {booking.status.toUpperCase()}
                                    </span>
                                </div>
                            </div>

                            <div className="card-body">
                                {event && (
                                    <div style={{ marginBottom: "var(--space-4)" }}>
                                        <p style={{ margin: "var(--space-2) 0", color: "var(--gray-600)" }}>
                                            <strong>📍 Venue:</strong> {event.venue || "TBD"}
                                        </p>
                                        <p style={{ margin: "var(--space-2) 0", color: "var(--gray-600)" }}>
                                            <strong>📝 Description:</strong> {event.description || "No description available"}
                                        </p>
                                    </div>
                                )}

                                <div style={{ marginBottom: "var(--space-4)" }}>
                                    <div className="flex justify-between items-center" style={{ marginBottom: "var(--space-3)" }}>
                                        <span style={{ fontWeight: "600" }}>
                                            🪑 Seats: {booking.seats}
                                        </span>
                                        <span style={{ color: "var(--gray-500)", fontSize: "0.875rem" }}>
                                            📅 Booked on: {(() => {
                                                try {
                                                    const date = new Date(booking.created_at);
                                                    if (isNaN(date.getTime())) {
                                                        return "Date not available";
                                                    }
                                                    return date.toLocaleString('en-US', {
                                                        year: 'numeric',
                                                        month: 'long',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    });
                                                } catch (error) {
                                                    return "Date not available";
                                                }
                                            })()}
                                        </span>
                                    </div>

                                    {receipt && (
                                        <div style={{
                                            backgroundColor: "rgba(34, 197, 94, 0.1)",
                                            border: "1px solid rgba(34, 197, 94, 0.2)",
                                            borderRadius: "var(--radius-lg)",
                                            padding: "var(--space-4)",
                                            marginTop: "var(--space-3)"
                                        }}>
                                            <p style={{ margin: "var(--space-1) 0", color: "var(--success-color)", fontWeight: "600" }}>
                                                ✅ Payment Completed: ${receipt.amount}
                                            </p>
                                            <p style={{ margin: "var(--space-1) 0", color: "var(--gray-600)", fontSize: "0.875rem" }}>
                                                Payment ID: {receipt.payment_id}
                                            </p>
                                        </div>
                                    )}
                                </div>

                                <div className="flex gap-3" style={{ flexWrap: "wrap" }}>
                                    <button
                                        onClick={() => downloadTicket(booking)}
                                        disabled={generatingPDF}
                                        className="btn btn-primary"
                                        style={{ opacity: generatingPDF ? 0.6 : 1 }}
                                    >
                                        🎫 Download Ticket PDF
                                    </button>

                                    {receipt && (
                                        <button
                                            onClick={() => downloadPaymentReceipt(booking.id)}
                                            disabled={generatingPDF}
                                            className="btn btn-secondary"
                                            style={{ opacity: generatingPDF ? 0.6 : 1 }}
                                        >
                                            📄 Download Receipt PDF
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
} 