
import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "smarttriage_access_token";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Attach JWT token to outgoing API requests
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = sessionStorage.getItem(TOKEN_KEY);

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Save authentication token after successful login
export const setAuthToken = (token: string) => {
  if (typeof window !== "undefined") {
    sessionStorage.setItem(TOKEN_KEY, token);
  }
};

// Retrieve stored authentication token
export const getAuthToken = () => {
  if (typeof window !== "undefined") {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  return null;
};

// Remove authentication token during logout
export const clearAuthToken = () => {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(TOKEN_KEY);
  }
};

export default api;
