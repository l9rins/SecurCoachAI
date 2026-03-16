import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL      = process.env.REACT_APP_SUPABASE_URL || "";
const SUPABASE_ANON_KEY = process.env.REACT_APP_SUPABASE_ANON_KEY || "";
const USERS_TABLE       = process.env.REACT_APP_SUPABASE_USERS_TABLE || "users";

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error(
    "Supabase is not configured. Set REACT_APP_SUPABASE_URL and " +
    "REACT_APP_SUPABASE_ANON_KEY in react-app/.env"
  );
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ── Profile upsert ────────────────────────────────────────────────────────────

async function upsertProfile(userId, email, name, username) {
  const { error } = await supabase
    .from(USERS_TABLE)
    .upsert(
      {
        id:        userId,
        email:     email.trim().toLowerCase(),
        full_name: name.trim(),
        username:  username.trim(),
      },
      { onConflict: "id" }
    );
  if (error) throw new Error(error.message);
}

// ── Sign in ───────────────────────────────────────────────────────────────────

export async function signInUser({ email, password }) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email:    email.trim().toLowerCase(),
    password,
  });
  if (error) throw new Error(error.message);

  const user = data.user;
  const meta = user.user_metadata || {};

  try {
    await upsertProfile(
      user.id,
      user.email,
      meta.name     || meta.full_name || "",
      meta.username || "",
    );
  } catch (profileErr) {
    // Profile save failed but auth succeeded — warn, don't block
    console.warn("Profile upsert failed:", profileErr.message);
  }

  return data;
}

// ── Sign up ───────────────────────────────────────────────────────────────────

export async function signUpUser({ name, username, email, password }) {
  const normalizedEmail = email.trim().toLowerCase();

  const { data, error } = await supabase.auth.signUp({
    email:    normalizedEmail,
    password,
    options: {
      data: {
        name:     name.trim(),
        username: username.trim(),
      },
    },
  });
  if (error) throw new Error(error.message);

  const user = data.user;
  if (user) {
    try {
      await upsertProfile(user.id, normalizedEmail, name, username);
    } catch (profileErr) {
      console.warn(
        `Account created, but profile save deferred due to RLS/email confirmation: ${profileErr.message}`
      );
    }
  }

  return data;
}

// ── Get current session access token ─────────────────────────────────────────

export async function getAccessToken() {
  const { data } = await supabase.auth.getSession();
  return data?.session?.access_token || null;
}
