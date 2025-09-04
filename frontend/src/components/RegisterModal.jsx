import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { setCredentials } from "../store/authSlice";
import { authAPI } from "../utils/api";

export default function RegisterModal({ onClose, onSuccess }) {
    const dispatch = useDispatch();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!email || !password || !confirmPassword) {
            setError("Please fill in all fields");
            return;
        }

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        if (password.length < 6) {
            setError("Password must be at least 6 characters long");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await authAPI.post("/register", { email, password });
            const { access_token, refresh_token, expires_in } = response.data;

            dispatch(setCredentials({
                access_token,
                refresh_token,
                expires_in,
                user: { email }
            }));

            onSuccess(response.data);
        } catch (err) {
            setError("Registration failed: " + (err?.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2 style={{ margin: 0, fontSize: "1.75rem", fontWeight: "700" }}>
                        ✨ Create Account
                    </h2>
                    <button
                        className="btn btn-outline"
                        onClick={onClose}
                        style={{ padding: "0.5rem", minWidth: "auto" }}
                    >
                        ✕
                    </button>
                </div>

                <div className="modal-body">
                    <form onSubmit={handleSubmit}>
                        <div style={{ marginBottom: "var(--space-4)" }}>
                            <label style={{
                                display: "block",
                                marginBottom: "var(--space-2)",
                                fontWeight: "600",
                                color: "var(--gray-700)"
                            }}>
                                📧 Email Address
                            </label>
                            <input
                                type="email"
                                className="input"
                                placeholder="Enter your email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div style={{ marginBottom: "var(--space-4)" }}>
                            <label style={{
                                display: "block",
                                marginBottom: "var(--space-2)",
                                fontWeight: "600",
                                color: "var(--gray-700)"
                            }}>
                                🔒 Password
                            </label>
                            <input
                                type="password"
                                className="input"
                                placeholder="Create a password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <p style={{
                                margin: "var(--space-2) 0 0 0",
                                color: "var(--gray-500)",
                                fontSize: "0.875rem"
                            }}>
                                Must be at least 6 characters long
                            </p>
                        </div>

                        <div style={{ marginBottom: "var(--space-6)" }}>
                            <label style={{
                                display: "block",
                                marginBottom: "var(--space-2)",
                                fontWeight: "600",
                                color: "var(--gray-700)"
                            }}>
                                🔐 Confirm Password
                            </label>
                            <input
                                type="password"
                                className="input"
                                placeholder="Confirm your password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
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
                                className={`btn btn-secondary ${loading ? 'opacity-60' : ''}`}
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
                                        Creating Account...
                                    </>
                                ) : (
                                    '✨ Create Account'
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
        </div>
    );
} 