import { useState } from "react";
import { signInUser, getAccessToken } from "./supabase";
import { validateEmail, validatePassword } from "./validation";
import "./auth.css";

const STREAMLIT_URL =
  process.env.REACT_APP_STREAMLIT_URL || "http://localhost:8501";

export default function LoginLayout({ onSwitchToSignup }) {
  const [form, setForm]       = useState({ email: "", password: "" });
  const [errors, setErrors]   = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: null }));
    setApiError("");
  }

  function validate() {
    const e = {};
    const emailErr = validateEmail(form.email);
    const passErr  = validatePassword(form.password);
    if (emailErr) e.email    = emailErr;
    if (passErr)  e.password = passErr;
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(evt) {
    evt.preventDefault();
    if (!validate() || loading) return;
    setLoading(true);
    setApiError("");
    try {
      await signInUser({ email: form.email, password: form.password });
      // Get the JWT and pass it securely via query param
      const token = await getAccessToken();
      if (!token) throw new Error("Could not retrieve session token.");
      window.location.href = `${STREAMLIT_URL}?token=${encodeURIComponent(token)}`;
    } catch (err) {
      setApiError(err.message || "Login failed. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div className="auth-root">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="auth-shield">🛡️</span>
          <h1 className="auth-title">SecurCoach AI</h1>
          <p className="auth-subtitle">Your cybersecurity training companion</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {apiError && (
            <div className="auth-error" role="alert">
              {apiError}
            </div>
          )}

          <div className="field-group">
            <label className="field-label" htmlFor="email">Email</label>
            <input
              id="email"
              className={`field-input${errors.email ? " field-input--error" : ""}`}
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              autoComplete="email"
              disabled={loading}
            />
            {errors.email && <span className="field-error">{errors.email}</span>}
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="password">Password</label>
            <input
              id="password"
              className={`field-input${errors.password ? " field-input--error" : ""}`}
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              autoComplete="current-password"
              disabled={loading}
            />
            {errors.password && <span className="field-error">{errors.password}</span>}
          </div>

          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? (
              <span className="auth-btn-inner">
                <span className="spinner" /> Signing in…
              </span>
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account?{" "}
          <button className="link-btn" onClick={onSwitchToSignup} disabled={loading}>
            Sign up
          </button>
        </p>
      </div>
    </div>
  );
}
