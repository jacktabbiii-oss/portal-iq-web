"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { getTeamOutlook, SCHOOL_LIST, TeamPlayer } from "@/lib/api/team";

// Position colors
const POSITION_COLORS: Record<string, string> = {
  QB: "#D4AF37",
  RB: "#22C55E",
  WR: "#3B82F6",
  TE: "#8B5CF6",
  OT: "#F59E0B",
  OG: "#F59E0B",
  C: "#F59E0B",
  EDGE: "#EF4444",
  DT: "#EC4899",
  LB: "#14B8A6",
  CB: "#06B6D4",
  S: "#6366F1",
};

const NEED_COLORS: Record<string, string> = {
  none: "#22C55E",
  low: "#84CC16",
  moderate: "#F59E0B",
  critical: "#EF4444",
};

export default function TeamAnalysisPage() {
  return (
    <Suspense fallback={<div className="p-6 text-center text-gray-400">Loading...</div>}>
      <TeamAnalysisContent />
    </Suspense>
  );
}

function TeamAnalysisContent() {
  const searchParams = useSearchParams();
  const [selectedSchool, setSelectedSchool] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Awaited<ReturnType<typeof getTeamOutlook>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filteredSchools = SCHOOL_LIST.filter((s) =>
    s.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAnalyze = useCallback(async (school?: string) => {
    const teamToAnalyze = school || selectedSchool;
    if (!teamToAnalyze) return;

    setLoading(true);
    setError(null);

    try {
      const result = await getTeamOutlook(teamToAnalyze);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load team data");
    } finally {
      setLoading(false);
    }
  }, [selectedSchool]);

  // Auto-load from URL params (e.g. /team-analysis?school=Ohio State)
  useEffect(() => {
    const schoolParam = searchParams.get("school");
    if (schoolParam) {
      setSelectedSchool(schoolParam);
      handleAnalyze(schoolParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const renderPlayerCard = (player: TeamPlayer, type: "incoming" | "outgoing") => (
    <div
      key={`${player.player_name}-${type}`}
      className="bg-[#243354] rounded-lg p-4 flex items-center justify-between"
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
          style={{ backgroundColor: POSITION_COLORS[player.position] || "#6B7280" }}
        >
          {player.position}
        </div>
        <div>
          <p className="text-white font-medium">{player.player_name}</p>
          <p className="text-gray-400 text-sm">
            {type === "incoming" ? `From ${player.origin_school}` : `To ${player.destination_school || "TBD"}`}
          </p>
        </div>
      </div>
      <div className="text-right">
        <p className="text-[#D4AF37] font-bold">{player.war.toFixed(1)} WAR</p>
        <p className="text-gray-400 text-sm">
          {"⭐".repeat(player.stars || 3)}{" "}
          {player.nil_valuation >= 1000000
            ? `$${(player.nil_valuation / 1000000).toFixed(1)}M`
            : `$${(player.nil_valuation / 1000).toFixed(0)}K`}
        </p>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-2">Team Analysis</h1>
      <p className="text-gray-400 mb-6">
        Analyze any team&apos;s transfer portal activity, incoming/outgoing players, and roster needs.
      </p>

      {/* School Selector */}
      <div className="bg-[#1a2744] rounded-xl p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-gray-400 text-sm mb-2">Search School</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Type to search..."
              className="w-full bg-[#243354] border border-[#3a4d6e] rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-[#D4AF37]"
            />
          </div>
          <div className="flex-1">
            <label className="block text-gray-400 text-sm mb-2">Select School</label>
            <select
              value={selectedSchool}
              onChange={(e) => setSelectedSchool(e.target.value)}
              className="w-full bg-[#243354] border border-[#3a4d6e] rounded-lg px-4 py-2 text-white focus:outline-none focus:border-[#D4AF37]"
            >
              <option value="">Choose a school...</option>
              {filteredSchools.map((school) => (
                <option key={school} value={school}>
                  {school}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => handleAnalyze()}
              disabled={!selectedSchool || loading}
              className="bg-[#D4AF37] text-[#0f1a2e] px-6 py-2 rounded-lg font-semibold hover:bg-[#c4a030] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-500 rounded-lg p-4 mb-6 text-red-300">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-[#1a2744] rounded-xl p-4">
              <p className="text-gray-400 text-xs uppercase mb-1">Portal Grade</p>
              <p className="text-3xl font-bold text-[#D4AF37]">{data.grade}</p>
            </div>
            <div className="bg-[#1a2744] rounded-xl p-4">
              <p className="text-gray-400 text-xs uppercase mb-1">Net WAR</p>
              <p className={`text-3xl font-bold ${data.summary.net_war >= 0 ? "text-green-400" : "text-red-400"}`}>
                {data.summary.net_war >= 0 ? "+" : ""}{data.summary.net_war.toFixed(1)}
              </p>
            </div>
            <div className="bg-[#1a2744] rounded-xl p-4">
              <p className="text-gray-400 text-xs uppercase mb-1">Transfers In</p>
              <p className="text-3xl font-bold text-green-400">{data.summary.transfers_in}</p>
            </div>
            <div className="bg-[#1a2744] rounded-xl p-4">
              <p className="text-gray-400 text-xs uppercase mb-1">Transfers Out</p>
              <p className="text-3xl font-bold text-red-400">{data.summary.transfers_out}</p>
            </div>
            <div className="bg-[#1a2744] rounded-xl p-4">
              <p className="text-gray-400 text-xs uppercase mb-1">NIL Invested</p>
              <p className="text-3xl font-bold text-white">
                {data.summary.total_nil >= 1000000
                  ? `$${(data.summary.total_nil / 1000000).toFixed(1)}M`
                  : `$${Math.round(data.summary.total_nil / 1000).toLocaleString()}K`}
              </p>
            </div>
          </div>

          {/* Incoming/Outgoing Grid */}
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            {/* Incoming */}
            <div className="bg-[#1a2744] rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-white">Incoming Transfers</h2>
                <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm">
                  +{data.activity.summary.incoming_war.toFixed(1)} WAR
                </span>
              </div>
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {data.activity.incoming.length > 0 ? (
                  data.activity.incoming.map((p) => renderPlayerCard(p, "incoming"))
                ) : (
                  <p className="text-gray-500 text-center py-8">No incoming transfers yet</p>
                )}
              </div>
            </div>

            {/* Outgoing */}
            <div className="bg-[#1a2744] rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-white">Outgoing Transfers</h2>
                <span className="bg-red-500/20 text-red-400 px-3 py-1 rounded-full text-sm">
                  -{data.activity.summary.outgoing_war.toFixed(1)} WAR
                </span>
              </div>
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {data.activity.outgoing.length > 0 ? (
                  data.activity.outgoing.map((p) => renderPlayerCard(p, "outgoing"))
                ) : (
                  <p className="text-gray-500 text-center py-8">No outgoing transfers</p>
                )}
              </div>
            </div>
          </div>

          {/* Position Needs */}
          <div className="bg-[#1a2744] rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">Position Needs Analysis</h2>
            {data.needs.priority_positions.length > 0 && (
              <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <p className="text-yellow-400 text-sm">
                  <strong>Priority Needs:</strong> {data.needs.priority_positions.join(", ")}
                </p>
              </div>
            )}
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              {Object.entries(data.needs.needs).map(([pos, need]) => (
                <div
                  key={pos}
                  className="bg-[#243354] rounded-lg p-3 text-center"
                  style={{ borderLeft: `3px solid ${NEED_COLORS[need.need_level]}` }}
                >
                  <p className="text-white font-bold">{pos}</p>
                  <p className="text-2xl font-bold" style={{ color: need.net >= 0 ? "#22C55E" : "#EF4444" }}>
                    {need.net >= 0 ? "+" : ""}{need.net}
                  </p>
                  <p className="text-gray-400 text-xs">
                    In: {need.incoming} / Out: {need.outgoing}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {!data && !loading && (
        <div className="bg-[#1a2744] rounded-xl p-12 text-center">
          <p className="text-gray-400">Select a school and click Analyze to view their portal activity.</p>
        </div>
      )}
    </div>
  );
}
