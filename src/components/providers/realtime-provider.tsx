"use client";

import { useRealtime } from "@/hooks/use-realtime";

interface RealtimeProviderProps {
  children: React.ReactNode;
}

/**
 * Provider component that initializes WebSocket connection for real-time updates.
 * Place this at the root of your authenticated app to enable real-time data sync.
 */
export function RealtimeProvider({ children }: RealtimeProviderProps) {
  // Initialize real-time connection to "all" channel
  useRealtime({ channel: "all", enabled: true });

  return <>{children}</>;
}
