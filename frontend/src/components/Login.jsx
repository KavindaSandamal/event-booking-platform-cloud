import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { setCredentials } from "../store/authSlice";
import { authAPI } from "../utils/api";
import RegisterModal from "./RegisterModal";

export default function Login() {
  const dispatch = useDispatch();
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [showRegister, setShowRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function login() {
    if (!email || !pass) {
      setError("Please fill in all fields");
      return;
    }
    setLoading(true);
    setError("");

    try {
      const r = await authAPI.post("/login", { email, password: pass });
      const { access_token, refresh_token, expires_in } = r.data;

      dispatch(setCredentials({
        access_token,
        refresh_token,
        expires_in,
        user: { email }
      }));
    } catch (e) {
      setError("Login failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  }

  const handleRegisterSuccess = (response) => {
    setShowRegister(false);
    const { access_token, refresh_token, expires_in } = response;
    dispatch(setCredentials({
      access_token,
      refresh_token,
      expires_in,
      user: { email }
    }));
  };

  return (
    <div className="card" style={{ maxWidth: "400px", margin: "0 auto" }}>
      <div className="card-header text-center">
        <h2 style={{
          fontSize: '2rem',
          fontWeight: '700',
          marginBottom: 'var(--space-2)',
          background: 'linear-gradient(135deg, var(--primary-color), var(--primary-dark))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          Welcome Back
        </h2>
        <p style={{ color: 'var(--gray-600)' }}>Sign in to your account</p>
      </div>

      <div className="card-body">
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label style={{
            display: 'block',
            marginBottom: 'var(--space-2)',
            fontWeight: '600',
            color: 'var(--gray-700)'
          }}>
            Email Address
          </label>
          <input
            type="email"
            className="input"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: 'var(--space-6)' }}>
          <label style={{
            display: 'block',
            marginBottom: 'var(--space-2)',
            fontWeight: '600',
            color: 'var(--gray-700)'
          }}>
            Password
          </label>
          <input
            type="password"
            className="input"
            placeholder="Enter your password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
          />
        </div>

        {error && (
          <div style={{
            color: 'var(--danger-color)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-3)',
            marginBottom: 'var(--space-4)',
            fontSize: '0.875rem'
          }}>
            ⚠️ {error}
          </div>
        )}

        <button
          className={`btn btn-primary ${loading ? 'opacity-60' : ''}`}
          onClick={login}
          disabled={loading}
          style={{ width: '100%', marginBottom: 'var(--space-4)' }}
        >
          {loading ? (
            <>
              <div style={{
                width: '16px',
                height: '16px',
                border: '2px solid transparent',
                borderTop: '2px solid white',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
              Signing In...
            </>
          ) : (
            '🔐 Sign In'
          )}
        </button>

        <div className="text-center">
          <p style={{
            margin: '0 0 var(--space-3) 0',
            color: 'var(--gray-500)',
            fontSize: '0.875rem'
          }}>
            Don't have an account?
          </p>
          <button
            className="btn btn-secondary"
            onClick={() => setShowRegister(true)}
          >
            ✨ Create Account
          </button>
        </div>
      </div>

      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSuccess={handleRegisterSuccess}
        />
      )}
    </div>
  );
}
