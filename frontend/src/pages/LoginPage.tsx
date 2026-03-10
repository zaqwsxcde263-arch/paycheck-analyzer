import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../state/AuthContext";

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await api.post("/auth/login", { email, password });
      login(response.data.token, response.data.user);
      navigate("/dashboard");
    } catch (err: any) {
      const message =
        err?.response?.data?.message ?? "Unable to login. Please check your credentials.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const emailInvalid = email.length > 0 && !email.includes("@");
  const passwordInvalid = password.length > 0 && password.length < 6;

  return (
    <div className="auth-container">
      <h1>Sign in</h1>
      <form onSubmit={handleSubmit} className="card">
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={emailInvalid ? "invalid" : ""}
            required
          />
        </label>
        {emailInvalid && <span className="error-text">Please enter a valid email.</span>}

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={passwordInvalid ? "invalid" : ""}
            required
          />
        </label>
        {passwordInvalid && (
          <span className="error-text">Password must be at least 6 characters.</span>
        )}

        {error && <div className="error-banner">{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <p>
        New here? <Link to="/register">Create an account</Link>
      </p>
    </div>
  );
};

