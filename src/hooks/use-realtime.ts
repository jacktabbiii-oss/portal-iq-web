import { useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { wsClient, type Channel, type MessageType } from "@/lib/websocket/client";
import { nilKeys } from "./queries/use-nil-queries";
import { portalKeys } from "./queries/use-portal-queries";
import { draftKeys } from "./queries/use-draft-queries";
import { rosterKeys } from "./queries/use-roster-queries";

interface UseRealtimeOptions {
  channel?: Channel;
  enabled?: boolean;
}

/**
 * Hook to enable real-time updates for the application.
 * Connects to WebSocket and invalidates relevant queries when updates are received.
 */
export function useRealtime(options: UseRealtimeOptions = {}) {
  const { channel = "all", enabled = true } = options;
  const queryClient = useQueryClient();

  const handleMessage = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as MessageType;

      switch (type) {
        case "nil_update":
        case "market_update":
          // Invalidate all NIL-related queries
          queryClient.invalidateQueries({ queryKey: nilKeys.all });
          break;

        case "portal_entry":
        case "portal_commit":
        case "flight_risk_change":
          // Invalidate all portal-related queries
          queryClient.invalidateQueries({ queryKey: portalKeys.all });
          break;

        case "draft_projection":
          // Invalidate all draft-related queries
          queryClient.invalidateQueries({ queryKey: draftKeys.all });
          break;

        case "roster_change":
          // Invalidate all roster-related queries
          queryClient.invalidateQueries({ queryKey: rosterKeys.all });
          break;

        case "connected":
          console.log("[Realtime] Connected to", data.channel);
          break;

        default:
          // For unknown types, invalidate everything
          queryClient.invalidateQueries();
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (!enabled) return;

    // Connect to WebSocket
    wsClient.connect(channel);

    // Subscribe to all messages
    const unsubscribe = wsClient.subscribe("*", handleMessage);

    // Cleanup on unmount
    return () => {
      unsubscribe();
      // Don't disconnect on unmount - keep connection alive for other components
    };
  }, [channel, enabled, handleMessage]);

  return {
    isConnected: wsClient.isConnected(),
    channel: wsClient.getChannel(),
  };
}

/**
 * Hook to subscribe to specific message types.
 * Use this for custom handling of real-time events.
 */
export function useRealtimeSubscription(
  messageType: MessageType | "*",
  handler: (data: Record<string, unknown>) => void,
  enabled = true
) {
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = wsClient.subscribe(messageType, handler);
    return unsubscribe;
  }, [messageType, handler, enabled]);
}
