/**
 * frontend/lib/api/auth.ts
 * ------------------------
 * Typed API client for Gokul Text Print authentication, session,
 * and RBAC-ready user operations.
 */

import { apiFetch, apiGet, apiPost } from "./client";

export type UserRole = "CEO" | "Manager" | "Employee" | "Admin";

export interface User {
  id: number;
  username: string;
  role: UserRole;
  email: string;
}

export interface LoginRequest {
  username?: string;
  email?: string;
  password?: string;
}

export interface LoginResponse {
  success: boolean;
  message?: string;
  error?: string;
  user: User;
}

export interface CurrentUserResponse {
  authenticated: boolean;
  user: User | null;
}

export interface ForgotPasswordRequest {
  username?: string;
  email?: string;
}

export interface ForgotPasswordResponse {
  success: boolean;
  message: string;
  reset_token?: string;
  reset_url?: string;
  expires_in?: string;
  error?: string;
}

export interface VerifyResetTokenResponse {
  valid: boolean;
  username?: string;
  error?: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
}

export interface ResetPasswordResponse {
  success: boolean;
  message: string;
  error?: string;
}

export interface ProfileUpdateRequest {
  email?: string;
  password?: string;
}

export interface ProfileUpdateResponse {
  success: boolean;
  message: string;
  user: User;
  error?: string;
}

// ---------------------------------------------------------------------------
// API methods
// ---------------------------------------------------------------------------

/**
 * Authenticate against Flask /api/auth/login.
 */
export async function loginUser(credentials: LoginRequest): Promise<LoginResponse> {
  return apiPost<LoginResponse>("/api/auth/login", credentials);
}

/**
 * Terminate the active Flask session.
 */
export async function logoutUser(): Promise<{ success: boolean; message?: string }> {
  return apiPost<{ success: boolean; message?: string }>("/api/auth/logout", {});
}

/**
 * Retrieve the current authenticated user session.
 */
export async function getCurrentUser(): Promise<CurrentUserResponse> {
  try {
    return await apiGet<CurrentUserResponse>("/api/auth/me");
  } catch {
    return { authenticated: false, user: null };
  }
}

/**
 * Request a password reset link/token.
 */
export async function requestPasswordReset(
  payload: ForgotPasswordRequest,
): Promise<ForgotPasswordResponse> {
  return apiPost<ForgotPasswordResponse>("/api/auth/forgot-password", payload);
}

/**
 * Verify token validity on page load before displaying the reset form.
 */
export async function verifyResetToken(token: string): Promise<VerifyResetTokenResponse> {
  try {
    return await apiGet<VerifyResetTokenResponse>("/api/auth/verify-reset-token", {
      params: { token },
    });
  } catch (err: unknown) {
    return { valid: false, error: "Invalid or expired reset token." };
  }
}

/**
 * Submit the new password using the validated reset token.
 */
export async function resetPassword(
  payload: ResetPasswordRequest,
): Promise<ResetPasswordResponse> {
  return apiPost<ResetPasswordResponse>("/api/auth/reset-password", payload);
}

/**
 * Update current user's profile settings (email, password).
 */
export async function updateUserProfile(
  payload: ProfileUpdateRequest,
): Promise<ProfileUpdateResponse> {
  return apiFetch<ProfileUpdateResponse>("/api/auth/profile", {
    method: "PUT",
    body: payload,
  });
}
