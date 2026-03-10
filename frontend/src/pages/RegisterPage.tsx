import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../state/AuthContext";

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await api.post("/auth/register", { name, email, password });
      login(response.data.token, {
        id: response.data.id,
        name: response.data.name,
        email: response.data.email
      });
      navigate("/dashboard");
    } catch (err: any) {
      const message = err?.response?.data?.message ?? "Unable to register with provided data.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const emailInvalid = email.length > 0 && !email.includes("@");
  const passwordInvalid = password.length > 0 && password.length < 6;
  const nameInvalid = name.length > 0 && name.trim().length < 2;

  return (
    <div className="auth-container">
      <h1>Create account</h1>
      <form onSubmit={handleSubmit} className="card">
        <label>
          Name
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={nameInvalid ? "invalid" : ""}
            required
          />
        </label>
        {nameInvalid && <span className="error-text">Name is too short.</span>}

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
          {loading ? "Creating account..." : "Create account"}
        </button>
      </form>
      <p>
        Already registered? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
};

