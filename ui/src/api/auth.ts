import { apiFetch } from "./client.ts";

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export async function signInWithGoogle(credential: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/api/v1/auth/google", {
    method: "POST",
    body: JSON.stringify({ token: credential }),
  });
}

export async function getMe(): Promise<UserProfile> {
  return apiFetch<UserProfile>("/api/v1/auth/me");
}
