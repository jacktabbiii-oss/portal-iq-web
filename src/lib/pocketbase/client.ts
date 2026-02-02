import PocketBase from "pocketbase";

const pocketbaseUrl =
  process.env.NEXT_PUBLIC_POCKETBASE_URL || "http://localhost:8090";

// Create a singleton PocketBase instance
const pb = new PocketBase(pocketbaseUrl);

// Disable auto-cancellation to prevent issues with React 18 strict mode
pb.autoCancellation(false);

export default pb;

// Type for user record
export interface User {
  id: string;
  email: string;
  name: string;
  organization?: string;
  organization_type?: string;
  subscription_tier: "free" | "pro" | "enterprise";
  avatar?: string;
  created: string;
  updated: string;
}

// Helper to get current user
export function getCurrentUser(): User | null {
  if (!pb.authStore.isValid) return null;
  // Type assertion needed for PocketBase model to User interface
  return pb.authStore.model as unknown as User;
}

// Helper to get auth token
export function getAuthToken(): string | null {
  if (!pb.authStore.isValid) return null;
  return pb.authStore.token;
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  return pb.authStore.isValid;
}
