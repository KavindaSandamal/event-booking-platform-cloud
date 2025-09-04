import React, { useState, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { setCredentials, logout, selectIsAuthenticated, selectToken } from "./store/authSlice";
import Events from "./components/Events";
import Login from "./components/Login";
import MyBookings from "./components/MyBookings";
import SessionManager from "./components/SessionManager";

export default function App() {
  const dispatch = useDispatch();
  const { isAuthenticated, token } = useSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState("events");
  const [refreshBookings, setRefreshBookings] = useState(0);

  // Check for existing token on app load and validate it
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedRefreshToken = localStorage.getItem('refreshToken');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedRefreshToken) {
      const user = storedUser ? JSON.parse(storedUser) : null;
      dispatch(setCredentials({
        access_token: storedToken,
        refresh_token: storedRefreshToken,
        expires_in: 30 * 60, // 30 minutes
        user
      }));
    }
  }, [dispatch]);

  const handleBookingComplete = () => {
    setRefreshBookings(prev => prev + 1);
    // Automatically switch to bookings tab after successful payment
    setActiveTab("bookings");
  };

  const handleLogout = () => {
    dispatch(logout());
  };

  if (!isAuthenticated) {
    return (
      <div className="main-content">
        <div className="container">
          <div className="text-center" style={{ padding: 'var(--space-20) 0' }}>
            <h1 style={{
              fontSize: '3rem',
              fontWeight: '800',
              marginBottom: 'var(--space-6)',
              background: 'linear-gradient(135deg, var(--primary-color), var(--primary-dark))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              🎫 Event Booking Platform
            </h1>
            <p style={{
              fontSize: '1.25rem',
              color: 'var(--gray-600)',
              marginBottom: 'var(--space-8)'
            }}>
              Secure, modern, and reliable event ticketing
            </p>
            <Login />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <SessionManager />

      <div className="header">
        <div className="flex items-center gap-4">
          <h1>🎫 Event Booking Platform</h1>
          <span style={{
            background: 'var(--success-color)',
            color: 'white',
            padding: '0.25rem 0.75rem',
            borderRadius: 'var(--radius-lg)',
            fontSize: '0.875rem',
            fontWeight: '600'
          }}>
            Live
          </span>
        </div>

        <button
          className="btn btn-outline"
          onClick={handleLogout}
        >
          👋 Logout
        </button>
      </div>

      <div className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === "events" ? "active" : ""}`}
          onClick={() => setActiveTab("events")}
        >
          🎭 Browse Events
        </button>
        <button
          className={`nav-tab ${activeTab === "bookings" ? "active" : ""}`}
          onClick={() => setActiveTab("bookings")}
        >
          📋 My Bookings
        </button>
      </div>

      <div className="container">
        {activeTab === "events" && <Events onBookingComplete={handleBookingComplete} />}
        {activeTab === "bookings" && <MyBookings key={refreshBookings} />}
      </div>
    </div>
  );
}
