"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Bell,
  ArrowRightLeft,
  DollarSign,
  Star,
  CheckCheck,
  Loader2,
  RefreshCw,
  Filter,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getActivePortalPlayers, type PortalPlayer } from "@/lib/api/portal";
import { getNILLeaderboard, type NILLeaderboardPlayer } from "@/lib/api/nil";
import { useWatchlist } from "@/hooks/use-watchlist";
import { formatNILValue } from "@/lib/api/players";

// =============================================================================
// Types
// =============================================================================

type NotificationType = "portal" | "commit" | "watchlist" | "nil";

interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  timestamp: string;
}

const FILTER_TABS: { value: NotificationType | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "portal", label: "Portal" },
  { value: "nil", label: "NIL" },
  { value: "watchlist", label: "Watchlist" },
];

const READ_STORAGE_KEY = "portaliq_notifications_read";

// =============================================================================
// Helpers
// =============================================================================

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case "portal":
    case "commit":
      return ArrowRightLeft;
    case "watchlist":
      return Star;
    case "nil":
      return DollarSign;
  }
}

function getNotificationColor(type: NotificationType) {
  switch (type) {
    case "portal":
      return "text-blue-400";
    case "commit":
      return "text-green-400";
    case "watchlist":
      return "text-yellow-500";
    case "nil":
      return "text-primary";
  }
}

function getNotificationBadgeColor(type: NotificationType) {
  switch (type) {
    case "portal":
      return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    case "commit":
      return "bg-green-500/10 text-green-400 border-green-500/30";
    case "watchlist":
      return "bg-yellow-500/10 text-yellow-500 border-yellow-500/30";
    case "nil":
      return "bg-primary/10 text-primary border-primary/30";
  }
}

function getNotificationLabel(type: NotificationType) {
  switch (type) {
    case "portal":
      return "Portal Entry";
    case "commit":
      return "Commitment";
    case "watchlist":
      return "Watchlist";
    case "nil":
      return "NIL Update";
  }
}

// =============================================================================
// Component
// =============================================================================

export default function NotificationsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [activeFilter, setActiveFilter] = useState<NotificationType | "all">("all");
  const [readIds, setReadIds] = useState<Set<string>>(new Set());
  const { watchlist } = useWatchlist();

  // Load read state from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(READ_STORAGE_KEY);
      if (saved) {
        setReadIds(new Set(JSON.parse(saved)));
      }
    } catch {
      // ignore
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const [portalResponse, nilResponse] = await Promise.all([
        getActivePortalPlayers({ limit: 30, status: "all" }).catch(() => ({
          players: [] as PortalPlayer[],
          total: 0,
          total_count: 0,
          active_in_portal: 0,
          committed: 0,
          schools_active: 0,
        })),
        getNILLeaderboard({ limit: 5 }).catch(() => ({
          players: [] as NILLeaderboardPlayer[],
          total: 0,
        })),
      ]);

      const items: Notification[] = [];
      const watchlistNames = new Set(watchlist.map((p) => p.player_name.toLowerCase()));

      // Process portal players
      for (const player of portalResponse.players) {
        const isWatchlisted = watchlistNames.has(player.player_name.toLowerCase());
        const timestamp = player.entry_date || new Date().toISOString();

        if (player.status === "committed" && player.destination_school) {
          if (isWatchlisted) {
            items.push({
              id: `watchlist-commit-${player.player_id}`,
              type: "watchlist",
              message: `${player.player_name} (${player.position}) from your watchlist committed to ${player.destination_school}`,
              timestamp,
            });
          }
          items.push({
            id: `commit-${player.player_id}`,
            type: "commit",
            message: `${player.player_name} (${player.position}) committed to ${player.destination_school} from ${player.origin_school}`,
            timestamp,
          });
        } else if (player.status === "available") {
          if (isWatchlisted) {
            items.push({
              id: `watchlist-portal-${player.player_id}`,
              type: "watchlist",
              message: `${player.player_name} (${player.position}) from your watchlist is in the portal from ${player.origin_school}`,
              timestamp,
            });
          }
          items.push({
            id: `portal-${player.player_id}`,
            type: "portal",
            message: `${player.player_name} (${player.position}) entered the portal from ${player.origin_school}`,
            timestamp,
          });
        }
      }

      // Add top NIL players
      for (const player of nilResponse.players) {
        items.push({
          id: `nil-${player.player_name}`,
          type: "nil",
          message: `${player.player_name} (${player.position}, ${player.school}) valued at ${formatNILValue(player.valuation)}`,
          timestamp: new Date().toISOString(),
        });
      }

      // Sort: watchlist first, then by timestamp descending
      items.sort((a, b) => {
        if (a.type === "watchlist" && b.type !== "watchlist") return -1;
        if (b.type === "watchlist" && a.type !== "watchlist") return 1;
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      });

      setNotifications(items);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setIsLoading(false);
    }
  }, [watchlist]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const filteredNotifications = useMemo(() => {
    if (activeFilter === "all") return notifications;
    if (activeFilter === "watchlist") {
      return notifications.filter((n) => n.type === "watchlist");
    }
    if (activeFilter === "portal") {
      return notifications.filter((n) => n.type === "portal" || n.type === "commit");
    }
    return notifications.filter((n) => n.type === activeFilter);
  }, [notifications, activeFilter]);

  const unreadCount = useMemo(
    () => notifications.filter((n) => !readIds.has(n.id)).length,
    [notifications, readIds]
  );

  const markAllRead = () => {
    const allIds = new Set(notifications.map((n) => n.id));
    setReadIds(allIds);
    localStorage.setItem(READ_STORAGE_KEY, JSON.stringify([...allIds]));
  };

  const markRead = (id: string) => {
    setReadIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      localStorage.setItem(READ_STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            Notifications
            {unreadCount > 0 && (
              <Badge variant="destructive" className="text-xs">
                {unreadCount}
              </Badge>
            )}
          </h1>
          <p className="text-muted-foreground mt-1">
            Live portal activity, NIL updates, and watchlist alerts
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button variant="ghost" size="sm" onClick={markAllRead}>
              <CheckCheck className="h-4 w-4 mr-2" />
              Mark all read
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchNotifications}
            disabled={isLoading}
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="h-4 w-4 text-muted-foreground" />
        {FILTER_TABS.map((tab) => (
          <Button
            key={tab.value}
            variant={activeFilter === tab.value ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveFilter(tab.value)}
            className={cn(
              activeFilter === tab.value
                ? "bg-primary text-primary-foreground"
                : "border-border"
            )}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : filteredNotifications.length > 0 ? (
        <div className="space-y-2">
          {filteredNotifications.map((notification) => {
            const Icon = getNotificationIcon(notification.type);
            const isRead = readIds.has(notification.id);

            return (
              <Card
                key={notification.id}
                className={cn(
                  "glass cursor-pointer transition-all duration-200 hover:bg-card",
                  !isRead && "border-l-4 border-l-primary"
                )}
                onClick={() => markRead(notification.id)}
              >
                <CardContent className="p-4 flex items-start gap-4">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center shrink-0",
                      notification.type === "watchlist" && "bg-yellow-500/10",
                      notification.type === "portal" && "bg-blue-500/10",
                      notification.type === "commit" && "bg-green-500/10",
                      notification.type === "nil" && "bg-primary/10"
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-5 w-5",
                        getNotificationColor(notification.type)
                      )}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[10px] font-bold",
                          getNotificationBadgeColor(notification.type)
                        )}
                      >
                        {getNotificationLabel(notification.type)}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {timeAgo(notification.timestamp)}
                      </span>
                      {!isRead && (
                        <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
                      )}
                    </div>
                    <p
                      className={cn(
                        "text-sm",
                        isRead ? "text-muted-foreground" : "text-foreground font-medium"
                      )}
                    >
                      {notification.message}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="glass">
          <CardContent className="py-16 text-center">
            <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
            <p className="text-muted-foreground font-medium">
              {activeFilter === "all"
                ? "No notifications yet"
                : `No ${activeFilter} notifications`}
            </p>
            <p className="text-muted-foreground text-sm mt-1">
              {activeFilter === "watchlist"
                ? "Add players to your watchlist to get alerts about their activity"
                : "Portal activity and updates will appear here"}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
