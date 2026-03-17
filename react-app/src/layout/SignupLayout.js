import { useState } from "react";
import { signUpUser, getAccessToken } from "./supabase";
import {
  validateEmail,
  validatePassword,
  validatePasswordMatch,
  validateName,
  validateUsername,
} from "./validation";
import "./auth.css";

const STREAMLIT_URL =
  process.env.REACT_APP_STREAMLIT_URL || "http://localhost:8501";

export default function SignupLayout({ onSwitchToLogin }) {
  const [form, setForm] = useState({
    name: "", username: "", email: "", password: "", confirm: "",
  });
  const [errors, setErrors]     = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: null }));
    setApiError("");
  }

  function validate() {
    const e = {};
    const nameErr    = validateName(form.name);
    const userErr    = validateUsername(form.username);
    const emailErr   = validateEmail(form.email);
    const passErr    = validatePassword(form.password);
    const matchErr   = validatePasswordMatch(form.password, form.confirm);
    if (nameErr)  e.name     = nameErr;
    if (userErr)  e.username = userErr;
    if (emailErr) e.email    = emailErr;
    if (passErr)  e.password = passErr;
    if (matchErr) e.confirm  = matchErr;
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(evt) {
    evt.preventDefault();
    if (!validate() || loading) return;
    setLoading(true);
    setApiError("");
    try {
      await signUpUser({
        name:     form.name,
        username: form.username,
        email:    form.email,
        password: form.password,
      });

      // Supabase may require email confirmation — check for session
      const token = await getAccessToken();
      if (token) {
        window.location.href = `${STREAMLIT_URL}?token=${encodeURIComponent(token)}`;
      } else {
        // Email confirmation required
        setSuccess(true);
        setLoading(false);
      }
    } catch (err) {
      setApiError(err.message || "Sign-up failed. Please try again.");
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="auth-root">
        <div className="auth-card">
          <div className="auth-brand">
            <span className="auth-shield">✉️</span>
            <h1 className="auth-title">Check your email</h1>
            <p className="auth-subtitle">
              We sent a confirmation link to <strong>{form.email}</strong>.
              Click it, then come back to sign in.
            </p>
          </div>
          <button className="auth-btn" onClick={onSwitchToLogin}>
            Go to Sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-root">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="auth-shield">🛡️</span>
          <h1 className="auth-title">Create account</h1>
          <p className="auth-subtitle">Start your cybersecurity journey</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {apiError && (
            <div className="auth-error" role="alert">
              {apiError}
            </div>
          )}

          <div className="field-row">
            <div className="field-group">
              <label className="field-label" htmlFor="name">Full name</label>
              <input
                id="name"
                className={`field-input${errors.name ? " field-input--error" : ""}`}
                type="text"
                placeholder="Jane Smith"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                autoComplete="name"
                disabled={loading}
              />
              {errors.name && <span className="field-error">{errors.name}</span>}
            </div>

            <div className="field-group">
              <label className="field-label" htmlFor="username">Username</label>
              <input
                id="username"
                className={`field-input${errors.username ? " field-input--error" : ""}`}
                type="text"
                placeholder="jane_sec"
                value={form.username}
                onChange={(e) => update("username", e.target.value)}
                autoComplete="username"
                disabled={loading}
              />
              {errors.username && <span className="field-error">{errors.username}</span>}
            </div>
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="su-email">Email</label>
            <input
              id="su-email"
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

          <div className="field-row">
            <div className="field-group">
              <label className="field-label" htmlFor="su-password">Password</label>
              <input
                id="su-password"
                className={`field-input${errors.password ? " field-input--error" : ""}`}
                type="password"
                placeholder="8+ characters"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                autoComplete="new-password"
                disabled={loading}
              />
              {errors.password && <span className="field-error">{errors.password}</span>}
            </div>

            <div className="field-group">
              <label className="field-label" htmlFor="confirm">Confirm</label>
              <input
                id="confirm"
                className={`field-input${errors.confirm ? " field-input--error" : ""}`}
                type="password"
                placeholder="Repeat password"
                value={form.confirm}
                onChange={(e) => update("confirm", e.target.value)}
                autoComplete="new-password"
                disabled={loading}
              />
              {errors.confirm && <span className="field-error">{errors.confirm}</span>}
            </div>
          </div>

          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? (
              <span className="auth-btn-inner">
                <span className="spinner" /> Creating account…
              </span>
            ) : (
              "Create account"
            )}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{" "}
          <button className="link-btn" onClick={onSwitchToLogin} disabled={loading}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
