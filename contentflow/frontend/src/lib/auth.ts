import { api } from "./api";

interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export async function register(email: string, password: string): Promise<void> {
  const data = await api.fetch<TokenResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
}

export async function login(email: string, password: string): Promise<void> {
  const data = await api.fetch<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export function isLoggedIn(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem("access_token");
}
