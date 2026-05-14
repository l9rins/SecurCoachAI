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
  const [showPassword, setShowPassword] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: null }));
    setApiError("");
  }

  function validate() {
    const e = {};
    const emailErr = validateEmail(form.email);
    if (emailErr) e.email = emailErr;
    if (!form.password) e.password = "Password is required.";
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
            <div className="brand-logo"><i className="ph ph-envelope"></i></div>
            <div className="brand-text">
              <span className="brand-name" style={{ fontSize: '18px' }}>Check your email</span>
            </div>
          </div>
          <div className="auth-divider"></div>
          <p className="auth-subtitle">
            We sent a password reset link to <strong>{form.email}</strong>.
            Follow the link to reset your password, then come back to sign in.
          </p>
          <button
            className="auth-btn"
            onClick={() => { setResetSent(false); setForgotMode(false); }}
            aria-label="Return to login"
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
            <div className="brand-logo"><i className="ph ph-shield"></i></div>
            <div className="brand-text">
              <span className="brand-name">SecurCoach AI</span>
              <span className="brand-tagline">Cybersecurity Training</span>
            </div>
          </div>
          <div className="auth-divider"></div>
          <h1 className="auth-title">Reset Password</h1>
          <p className="auth-subtitle">Enter your email and we'll send a reset link</p>
          <form className="auth-form" onSubmit={handleForgotPassword} noValidate>
            {apiError && (
              <div className="auth-error" role="alert">{apiError}</div>
            )}
            <div className="field-group">
              <label className="field-label" htmlFor="reset-email">Email Address</label>
              <input
                id="reset-email"
                className={`field-input${errors.email ? " field-input--error" : ""}`}
                type="email"
                placeholder="name@company.com"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                autoComplete="email"
                disabled={loading}
                aria-describedby={errors.email ? "reset-email-error" : undefined}
              />
              {errors.email && <span id="reset-email-error" className="field-error">{errors.email}</span>}
            </div>
            <button className="auth-btn" type="submit" disabled={loading} aria-label="Send password reset link">
              {loading ? (
                <span className="auth-btn-inner">
                  <span className="spinner" /> Sending…
                </span>
              ) : "Send reset link"}
            </button>
          </form>
          <p className="auth-switch">
            <button className="link-btn" onClick={() => setForgotMode(false)} aria-label="Return to login">
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
          <div className="brand-logo"><i className="ph ph-shield"></i></div>
          <div className="brand-text">
            <span className="brand-name">SecurCoach AI</span>
            <span className="brand-tagline">Cybersecurity Training</span>
          </div>
        </div>
        <div className="auth-divider"></div>

        {apiError && <div className="auth-error" role="alert">{apiError}</div>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="field-group">
            <label className="field-label" htmlFor="login-email">Email Address</label>
            <input
              id="login-email"
              className={`field-input ${errors.email ? "field-input--error" : ""}`}
              type="email"
              placeholder="name@company.com"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              disabled={loading}
              autoComplete="email"
              autoFocus
              aria-describedby={errors.email ? "email-error" : undefined}
            />
            {errors.email && <div id="email-error" className="field-error">{errors.email}</div>}
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="login-password">Password</label>
            <div className="password-input-wrapper" style={{ position: "relative" }}>
              <input
                id="login-password"
                className={`field-input ${errors.password ? "field-input--error" : ""}`}
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                disabled={loading}
                autoComplete="current-password"
                aria-describedby={errors.password ? "password-error password-hint" : "password-hint"}
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                <i className={showPassword ? "ph ph-eye-slash" : "ph ph-eye"}></i>
              </button>
            </div>
            <div id="password-hint" className="field-hint" style={{ fontSize: "11px", color: "var(--color-text-muted)", marginTop: "4px" }}>8+ characters</div>
            {errors.password && <div id="password-error" className="field-error">{errors.password}</div>}
          </div>

          <button className="auth-btn" type="submit" disabled={loading} aria-label="Sign in to SecurCoach AI">
            {loading ? (
              <span className="auth-btn-inner">
                <span className="spinner"></span> Signing in…
              </span>
            ) : "Sign in"}
          </button>
          
          <div style={{ textAlign: "center", marginTop: "12px" }}>
            <button type="button" className="link-btn secondary" onClick={() => setForgotMode(true)} aria-label="Forgot your password?" style={{ fontSize: "12px" }}>
              Forgot password?
            </button>
          </div>
        </form>

        <div className="auth-footer" style={{ flexDirection: "column", gap: "8px", marginTop: "24px" }}>
          <div style={{ fontSize: "13px", color: "var(--color-text-muted)" }}>
            New here? <button className="link-btn" onClick={onSwitchToSignup} aria-label="Create a new account">Create an account</button>
          </div>
        </div>

        <div className="security-badge">
          <div className="dot"></div>
          <span>TLS 1.3 ENCRYPTED</span>
        </div>
      </div>
    </div>
  );
}
