type MessageHandler = (data: Record<string, unknown>) => void;

export type Channel = "nil" | "portal" | "draft" | "roster" | "all";

export type MessageType =
  | "connected"
  | "pong"
  | "nil_update"
  | "portal_entry"
  | "portal_commit"
  | "flight_risk_change"
  | "draft_projection"
  | "roster_change"
  | "market_update";

interface WebSocketMessage {
  type: MessageType;
  [key: string]: unknown;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: NodeJS.Timeout | null = null;
  private currentChannel: Channel | null = null;
  private isConnecting = false;

  connect(channel: Channel = "all") {
    // Prevent multiple simultaneous connection attempts
    if (this.isConnecting || (this.ws?.readyState === WebSocket.OPEN && this.currentChannel === channel)) {
      return;
    }

    // Close existing connection if switching channels
    if (this.ws && this.currentChannel !== channel) {
      this.disconnect();
    }

    this.isConnecting = true;
    this.currentChannel = channel;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsUrl = apiUrl.replace(/^http/, "ws");

    try {
      this.ws = new WebSocket(`${wsUrl}/ws/${channel}`);

      this.ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${channel} channel`);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (e) {
          console.error("[WebSocket] Failed to parse message:", e);
        }
      };

      this.ws.onclose = (event) => {
        console.log(`[WebSocket] Disconnected (code: ${event.code})`);
        this.isConnecting = false;
        this.stopPingInterval();

        // Attempt reconnect if not a clean close
        if (event.code !== 1000 && this.currentChannel) {
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
        this.isConnecting = false;
      };
    } catch (e) {
      console.error("[WebSocket] Connection failed:", e);
      this.isConnecting = false;
      this.attemptReconnect();
    }
  }

  disconnect() {
    this.stopPingInterval();
    this.currentChannel = null;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect

    if (this.ws) {
      this.ws.close(1000);
      this.ws = null;
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log("[WebSocket] Max reconnect attempts reached");
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    setTimeout(() => {
      this.reconnectAttempts++;
      if (this.currentChannel) {
        this.connect(this.currentChannel);
      }
    }, delay);
  }

  private startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private handleMessage(data: WebSocketMessage) {
    const { type } = data;

    // Skip pong messages
    if (type === "pong") return;

    // Notify handlers for this message type
    const typeHandlers = this.handlers.get(type);
    if (typeHandlers) {
      typeHandlers.forEach((handler) => handler(data));
    }

    // Also notify "all" handlers
    const allHandlers = this.handlers.get("*");
    if (allHandlers) {
      allHandlers.forEach((handler) => handler(data));
    }
  }

  subscribe(type: MessageType | "*", handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getChannel(): Channel | null {
    return this.currentChannel;
  }
}

// Singleton instance
export const wsClient = new WebSocketClient();
