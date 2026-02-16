const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export function getToken(): string | null {
  return localStorage.getItem("token");
}
export function setToken(t: string) {
  localStorage.setItem("token", t);
}
export function clearToken() {
  localStorage.removeItem("token");
}

async function req(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

export async function register(email: string, password: string) {
  return req("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return req("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export async function me() {
  return req("/users/me");
}

export async function uploadPdf(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return req("/files/upload", { method: "POST", body: fd });
}

export async function listConversions() {
  return req("/conversions/");
}

export async function getConversion(id: number) {
  return req(`/conversions/${id}`);
}

export function downloadCsvUrl(id: number) {
  return `${API_BASE}/conversions/${id}/download/csv`;
}

export function downloadJsonUrl(id: number) {
  return `${API_BASE}/conversions/${id}/download/json`;
}
