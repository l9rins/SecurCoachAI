import { useState } from "react";
import { signInUser, getAccessToken, resetPassword } from "./supabase";
import { validateEmail, validatePassword } from "./validation";
import "./auth.css";

const STREAMLIT_URL =
  process.env.REACT_APP_STREAMLIT_URL || "http://localhost:8501";

export default function LoginLayout({ onSwitchToSignup }) {
  const [form, setForm]       = useState({ email: "", password: "" });
  const [errors, setErrors]   = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);
  const [forgotMode, setForgotMode] = useState(false);
  const [resetSent, setResetSent] = useState(false);

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

  async function handleForgotPassword(evt) {
    evt.preventDefault();
    const emailErr = validateEmail(form.email);
    if (emailErr) {
      setErrors({ email: emailErr });
      return;
    }
    setLoading(true);
    setApiError("");
    try {
      await resetPassword(form.email);
      setResetSent(true);
    } catch (err) {
      setApiError(err.message || "Could not send reset email.");
    } finally {
      setLoading(false);
    }
  }

  // Forgot password: success screen
  if (resetSent) {
    return (
      <div className="auth-root">
        <div className="auth-card">
          <div className="auth-brand">
            <span className="auth-shield">✉️</span>
            <h1 className="auth-title">Check your email</h1>
            <p className="auth-subtitle">
              We sent a password reset link to <strong>{form.email}</strong>.
              Follow the link to reset your password, then come back to sign in.
            </p>
          </div>
          <button
            className="auth-btn"
            onClick={() => { setResetSent(false); setForgotMode(false); }}
          >
            Back to Sign in
          </button>
        </div>
      </div>
    );
  }

  // Forgot password: form
  if (forgotMode) {
    return (
      <div className="auth-root">
        <div className="auth-card">
          <div className="auth-brand">
            <span className="auth-shield">🔑</span>
            <h1 className="auth-title">Reset password</h1>
            <p className="auth-subtitle">Enter your email and we'll send a reset link</p>
          </div>
          <form className="auth-form" onSubmit={handleForgotPassword} noValidate>
            {apiError && (
              <div className="auth-error" role="alert">{apiError}</div>
            )}
            <div className="field-group">
              <label className="field-label" htmlFor="reset-email">Email</label>
              <input
                id="reset-email"
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
            <button className="auth-btn" type="submit" disabled={loading}>
              {loading ? (
                <span className="auth-btn-inner">
                  <span className="spinner" /> Sending…
                </span>
              ) : "Send reset link"}
            </button>
          </form>
          <p className="auth-switch">
            <button className="link-btn" onClick={() => setForgotMode(false)}>
              Back to Sign in
            </button>
          </p>
        </div>
      </div>
    );
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

          <p className="auth-switch" style={{ marginTop: '0.25rem' }}>
            <button className="link-btn" onClick={() => setForgotMode(true)} disabled={loading}>
              Forgot password?
            </button>
          </p>
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
