import { apiErrorMessage } from "./errors";

const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "";
let csrfToken: string | null = null;
export type Identity = {
  user: { id: number; name: string; email: string };
  organization: { id: number; name: string };
  csrf_token: string;
};

export async function authMe(): Promise<Identity | null> {
  const response = await fetch(`${base}/api/auth/me`, {
    credentials: "same-origin",
  });
  if (response.status === 401) {
    csrfToken = null;
    return null;
  }
  const payload = await response.json();
  if (!response.ok)
    throw new Error(apiErrorMessage(payload, "Could not load session"));
  csrfToken = payload.csrf_token;
  return payload;
}

async function getCsrf() {
  if (!csrfToken) {
    const response = await fetch(`${base}/api/auth/csrf`, {
      credentials: "same-origin",
    });
    const payload = await response.json();
    if (!response.ok) throw new Error("Could not initialize session security");
    csrfToken = payload.csrf_token;
  }
  return csrfToken!;
}

export async function recruiterFetch(url: string, init: RequestInit = {}) {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (!["GET", "HEAD", "OPTIONS"].includes(method))
    headers.set("X-CSRF-Token", await getCsrf());
  return fetch(url, { ...init, headers, credentials: "same-origin" });
}

export async function login(
  email: string,
  password: string,
): Promise<Identity> {
  const response = await recruiterFetch(`${base}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(apiErrorMessage(payload, "Sign in failed"));
  csrfToken = payload.csrf_token;
  return payload;
}

export async function logout() {
  const response = await recruiterFetch(`${base}/api/auth/logout`, {
    method: "POST",
  });
  if (!response.ok)
    throw new Error(apiErrorMessage(await response.json(), "Sign out failed"));
  csrfToken = null;
}
