import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import pb from "@/lib/pocketbase/client";

// API Base URL
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "dev-key-123";

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor - add auth headers
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add API key for Portal IQ endpoints
    config.headers["X-API-Key"] = API_KEY;

    // Add JWT token if available (for user-specific features)
    const token = pb.authStore.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle standard response format
apiClient.interceptors.response.use(
  (response) => {
    // API returns { status, data, message, timestamp }
    // Extract the data field for convenience
    if (response.data && response.data.status === "success") {
      return response.data.data;
    }
    return response.data;
  },
  (error: AxiosError<{ status: string; message: string; detail?: string }>) => {
    // Handle auth errors
    if (error.response?.status === 401) {
      // Token expired or invalid
      pb.authStore.clear();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }

    // Extract error message
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      "An error occurred";

    return Promise.reject(new Error(message));
  }
);

export default apiClient;

// Typed API response wrapper
export interface APIResponse<T> {
  status: "success" | "error";
  data: T;
  message?: string;
  timestamp?: string;
}
