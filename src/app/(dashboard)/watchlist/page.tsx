"use client";

import { useState, useEffect } from "react";

interface WatchlistPlayer {
  id: string;
  player_name: string;
  position: string;
  school: string;
  nil_valuation: number;
  stars?: number;
  added_date: string;
  notes?: string;
}

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<WatchlistPlayer[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});

  // Load watchlist from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("portaliq_watchlist");
    if (saved) {
      try {
        setWatchlist(JSON.parse(saved));
      } catch {
        console.error("Failed to parse watchlist");
      }
    }
    const savedNotes = localStorage.getItem("portaliq_watchlist_notes");
    if (savedNotes) {
      try {
        setNotes(JSON.parse(savedNotes));
      } catch {
        console.error("Failed to parse notes");
      }
    }
  }, []);

  const removeFromWatchlist = (playerId: string) => {
    const updated = watchlist.filter((p) => p.id !== playerId);
    setWatchlist(updated);
    localStorage.setItem("portaliq_watchlist", JSON.stringify(updated));
  };

  const updateNote = (playerId: string, note: string) => {
    const updated = { ...notes, [playerId]: note };
    setNotes(updated);
    localStorage.setItem("portaliq_watchlist_notes", JSON.stringify(updated));
  };

  const exportWatchlist = () => {
    const data = watchlist.map((p) => ({
      ...p,
      notes: notes[p.id] || "",
    }));
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "portaliq_watchlist.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Watchlist</h1>
          <p className="text-gray-400">Track players you&apos;re interested in</p>
        </div>
        {watchlist.length > 0 && (
          <button
            onClick={exportWatchlist}
            className="bg-[#243354] text-white px-4 py-2 rounded-lg hover:bg-[#2a3d5e] transition"
          >
            Export
          </button>
        )}
      </div>

      {watchlist.length === 0 ? (
        <div className="bg-[#1a2744] rounded-xl p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h2 className="text-xl font-bold text-white mb-2">Your watchlist is empty</h2>
          <p className="text-gray-400 mb-6">
            Add players from the Portal Intelligence or NIL Valuator pages to track them here.
          </p>
          <div className="flex justify-center gap-4">
            <a
              href="/portal-intelligence"
              className="bg-[#D4AF37] text-[#0f1a2e] px-6 py-2 rounded-lg font-semibold hover:bg-[#c4a030]"
            >
              Browse Portal
            </a>
            <a
              href="/nil-valuator"
              className="bg-[#243354] text-white px-6 py-2 rounded-lg font-semibold hover:bg-[#2a3d5e]"
            >
              NIL Valuator
            </a>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {watchlist.map((player) => (
            <div
              key={player.id}
              className="bg-[#1a2744] rounded-xl p-6 flex flex-col md:flex-row md:items-center gap-4"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-[#243354] rounded-full flex items-center justify-center">
                    <span className="text-[#D4AF37] font-bold">{player.position}</span>
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-lg">{player.player_name}</h3>
                    <p className="text-gray-400">
                      {player.school} • {"⭐".repeat(player.stars || 3)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[#D4AF37] font-bold text-xl">
                  ${(player.nil_valuation / 1000).toFixed(0)}K
                </p>
                <p className="text-gray-500 text-sm">Added {new Date(player.added_date).toLocaleDateString()}</p>
              </div>
              <div className="flex-1">
                <textarea
                  value={notes[player.id] || ""}
                  onChange={(e) => updateNote(player.id, e.target.value)}
                  placeholder="Add notes..."
                  className="w-full bg-[#243354] border border-[#3a4d6e] rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-[#D4AF37] resize-none"
                  rows={2}
                />
              </div>
              <button
                onClick={() => removeFromWatchlist(player.id)}
                className="text-red-400 hover:text-red-300 p-2"
                title="Remove from watchlist"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
