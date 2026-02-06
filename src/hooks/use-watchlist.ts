"use client";

import { useState, useEffect, useCallback } from "react";

export interface WatchlistPlayer {
  id: string;
  player_name: string;
  position: string;
  school: string;
  nil_valuation: number;
  stars?: number;
  added_date: string;
  headshot_url?: string;
}

const STORAGE_KEY = "portaliq_watchlist";

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState<WatchlistPlayer[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setWatchlist(JSON.parse(saved));
      }
    } catch (error) {
      console.error("Failed to load watchlist:", error);
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage whenever watchlist changes
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
    }
  }, [watchlist, isLoaded]);

  const addToWatchlist = useCallback((player: Omit<WatchlistPlayer, "added_date">) => {
    setWatchlist((prev) => {
      // Check if already exists
      if (prev.some((p) => p.id === player.id)) {
        return prev;
      }
      return [
        ...prev,
        {
          ...player,
          added_date: new Date().toISOString(),
        },
      ];
    });
  }, []);

  const removeFromWatchlist = useCallback((playerId: string) => {
    setWatchlist((prev) => prev.filter((p) => p.id !== playerId));
  }, []);

  const isInWatchlist = useCallback(
    (playerId: string) => {
      return watchlist.some((p) => p.id === playerId);
    },
    [watchlist]
  );

  const toggleWatchlist = useCallback(
    (player: Omit<WatchlistPlayer, "added_date">) => {
      if (isInWatchlist(player.id)) {
        removeFromWatchlist(player.id);
        return false;
      } else {
        addToWatchlist(player);
        return true;
      }
    },
    [isInWatchlist, removeFromWatchlist, addToWatchlist]
  );

  return {
    watchlist,
    isLoaded,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist,
    toggleWatchlist,
  };
}
