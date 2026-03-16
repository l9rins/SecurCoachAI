// validation.js — shared form validation helpers

export function validateEmail(email) {
  if (!email.trim()) return "Email is required.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()))
    return "Enter a valid email address.";
  return null;
}

export function validatePassword(password) {
  if (!password) return "Password is required.";
  if (password.length < 8) return "Password must be at least 8 characters.";
  return null;
}

export function validatePasswordMatch(password, confirm) {
  if (!confirm) return "Please confirm your password.";
  if (password !== confirm) return "Passwords do not match.";
  return null;
}

export function validateName(name) {
  if (!name.trim()) return "Full name is required.";
  if (name.trim().length < 2) return "Name must be at least 2 characters.";
  return null;
}

export function validateUsername(username) {
  if (!username.trim()) return "Username is required.";
  if (!/^[a-zA-Z0-9_]{3,30}$/.test(username.trim()))
    return "Username must be 3-30 characters: letters, numbers, underscores only.";
  return null;
}
