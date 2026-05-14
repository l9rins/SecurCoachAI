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
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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
            <div className="brand-logo"><i className="ph ph-envelope"></i></div>
            <div className="brand-text">
              <span className="brand-name" style={{ fontSize: '18px' }}>Check your email</span>
            </div>
          </div>
          <div className="auth-divider"></div>
          <p className="auth-subtitle">
            We sent a confirmation link to <strong>{form.email}</strong>.
            Click it to verify your email, then come back to sign in.
          </p>
          <button className="auth-btn" onClick={onSwitchToLogin} aria-label="Return to login">
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
          <div className="brand-logo"><i className="ph ph-shield"></i></div>
          <div className="brand-text">
            <span className="brand-name">SecurCoach AI</span>
            <span className="brand-tagline">Cybersecurity Training</span>
          </div>
        </div>
        <div className="auth-divider"></div>
        <h1 className="auth-title">Create account</h1>
        <p className="auth-subtitle">Start your cybersecurity journey</p>

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
                aria-describedby={errors.name ? "name-error" : undefined}
              />
              {errors.name && <span id="name-error" className="field-error">{errors.name}</span>}
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
                aria-describedby={errors.username ? "username-error" : undefined}
              />
              {errors.username && <span id="username-error" className="field-error">{errors.username}</span>}
            </div>
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="su-email">Email Address</label>
            <input
              id="su-email"
              className={`field-input${errors.email ? " field-input--error" : ""}`}
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              autoComplete="email"
              disabled={loading}
              aria-describedby={errors.email ? "email-error" : undefined}
            />
            {errors.email && <span id="email-error" className="field-error">{errors.email}</span>}
          </div>

            <div className="field-row">
              <div className="field-group">
                <label className="field-label" htmlFor="su-password">Password</label>
                <div className="password-input-wrapper" style={{ position: "relative" }}>
                  <input
                    id="su-password"
                    className={`field-input${errors.password ? " field-input--error" : ""}`}
                    type={showPassword ? "text" : "password"}
                    placeholder="8+ characters"
                    value={form.password}
                    onChange={(e) => update("password", e.target.value)}
                    autoComplete="new-password"
                    disabled={loading}
                    aria-describedby={errors.password ? "password-error password-hint-su" : "password-hint-su"}
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
                {errors.password && <div id="password-error" className="field-error">{errors.password}</div>}
              </div>

              <div className="field-group">
                <label className="field-label" htmlFor="su-confirmPassword">Confirm</label>
                <div className="password-input-wrapper" style={{ position: "relative" }}>
                  <input
                    id="su-confirmPassword"
                    className={`field-input${errors.confirm ? " field-input--error" : ""}`}
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Repeat password"
                    value={form.confirm}
                    onChange={(e) => update("confirm", e.target.value)}
                    autoComplete="new-password"
                    disabled={loading}
                    aria-describedby={errors.confirm ? "confirm-error" : undefined}
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  >
                    <i className={showConfirmPassword ? "ph ph-eye-slash" : "ph ph-eye"}></i>
                  </button>
                </div>
                {errors.confirm && <div id="confirm-error" className="field-error">{errors.confirm}</div>}
              </div>
            </div>

          <button className="auth-btn" type="submit" disabled={loading} aria-label="Create new account">
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
          <button className="link-btn" onClick={onSwitchToLogin} disabled={loading} aria-label="Switch to login">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
