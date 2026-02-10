"use client";

import { useState, useEffect } from "react";
import { getTeamRankings, CONFERENCES, TIER_LIST, type TeamRanking } from "@/lib/api/team";
import { ChevronDown, ChevronUp, TrendingUp, Trophy, Target, Users } from "lucide-react";

const SORT_OPTIONS = [
  { value: "power_score", label: "Power Score" },
  { value: "wins", label: "Wins" },
  { value: "sp_plus", label: "SP+ Rating" },
  { value: "pff_avg", label: "PFF Average" },
  { value: "roster_talent", label: "Roster Talent" },
  { value: "portal_rank", label: "Portal Rank" },
  { value: "nil_change", label: "NIL Spending" },
];

const TIER_COLORS: Record<string, string> = {
  blue_blood: "#D4AF37",
  elite: "#F59E0B",
  power_strong: "#3B82F6",
  power_mid: "#06B6D4",
  power_low: "#8B5CF6",
  g5_strong: "#10B981",
  g5_mid: "#6B7280",
  fcs: "#4B5563",
};

export default function PowerRankingsPage() {
  const [rankings, setRankings] = useState<TeamRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedConference, setSelectedConference] = useState<string>("");
  const [selectedTier, setSelectedTier] = useState<string>("");
  const [sortBy, setSortBy] = useState("power_score");
  const [limit, setLimit] = useState(50);
  const [expandedTeam, setExpandedTeam] = useState<string | null>(null);

  useEffect(() => {
    loadRankings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedConference, selectedTier, sortBy, limit]);

  const loadRankings = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getTeamRankings(
        selectedConference || undefined,
        selectedTier || undefined,
        sortBy,
        limit
      );
      setRankings(response.teams);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load rankings");
    } finally {
      setLoading(false);
    }
  };

  const formatNIL = (value?: number) => {
    if (!value) return "N/A";
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-[#22C55E]";
    if (score >= 70) return "text-[#84CC16]";
    if (score >= 60) return "text-[#F59E0B]";
    if (score >= 50) return "text-[#EF4444]";
    return "text-gray-400";
  };

  return (
    <div className="min-h-screen bg-[#0f1a2e] text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Trophy className="w-8 h-8 text-[#D4AF37]" />
          <h1 className="text-3xl font-bold">Portal IQ Power Rankings</h1>
        </div>
        <p className="text-gray-400">
          Proprietary algorithm combining on-field performance, roster quality, portal activity, and NIL power
        </p>
      </div>

      {/* Algorithm Breakdown */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-[#1a2744] rounded-xl p-6 border border-[#D4AF37]/20">
          <h2 className="text-lg font-bold mb-4 text-[#D4AF37]">Algorithm Breakdown (100-Point Scale)</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-start gap-3">
              <TrendingUp className="w-5 h-5 text-[#3B82F6] mt-1" />
              <div>
                <p className="font-semibold text-white">On-Field (30%)</p>
                <p className="text-sm text-gray-400">SP+ ratings (18%) + Wins (12%)</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Users className="w-5 h-5 text-[#22C55E] mt-1" />
              <div>
                <p className="font-semibold text-white">Roster Quality (25%)</p>
                <p className="text-sm text-gray-400">PFF grades (15%) + NIL talent (10%)</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Target className="w-5 h-5 text-[#F59E0B] mt-1" />
              <div>
                <p className="font-semibold text-white">Portal Performance (25%)</p>
                <p className="text-sm text-gray-400">On3 rank (15%) + Transfers (10%)</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Trophy className="w-5 h-5 text-[#D4AF37] mt-1" />
              <div>
                <p className="font-semibold text-white">NIL/Recruiting (20%)</p>
                <p className="text-sm text-gray-400">School tier (10%) + Spending (10%)</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-[#1a2744] rounded-xl p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Conference</label>
              <select
                value={selectedConference}
                onChange={(e) => setSelectedConference(e.target.value)}
                className="w-full bg-[#243354] border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent"
              >
                <option value="">All Conferences</option>
                {CONFERENCES.map((conf) => (
                  <option key={conf} value={conf}>
                    {conf}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Tier</label>
              <select
                value={selectedTier}
                onChange={(e) => setSelectedTier(e.target.value)}
                className="w-full bg-[#243354] border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent"
              >
                <option value="">All Tiers</option>
                {TIER_LIST.map((tier) => (
                  <option key={tier} value={tier}>
                    {tier.replace(/_/g, " ").toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full bg-[#243354] border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Limit</label>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="w-full bg-[#243354] border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent"
              >
                <option value={25}>Top 25</option>
                <option value={50}>Top 50</option>
                <option value={100}>Top 100</option>
                <option value={136}>All FBS (136)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Rankings Table */}
      <div className="max-w-7xl mx-auto">
        {loading ? (
          <div className="bg-[#1a2744] rounded-xl p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#D4AF37] mx-auto mb-4"></div>
            <p className="text-gray-400">Loading rankings...</p>
          </div>
        ) : error ? (
          <div className="bg-[#1a2744] rounded-xl p-6 border border-red-500/20">
            <p className="text-red-400">{error}</p>
          </div>
        ) : (
          <div className="bg-[#1a2744] rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#243354] border-b border-gray-700">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Rank</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">School</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300">Power Score</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300">Record</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300">SP+</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300">PFF Avg</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300">Portal</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300">NIL Δ</th>
                    <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {rankings.map((team) => (
                    <>
                      <tr
                        key={team.school}
                        className="hover:bg-[#243354] cursor-pointer transition-colors"
                        onClick={() => setExpandedTeam(expandedTeam === team.school ? null : team.school)}
                      >
                        <td className="px-6 py-4">
                          <span className="text-lg font-bold text-[#D4AF37]">#{team.rank}</span>
                        </td>
                        <td className="px-6 py-4">
                          <div>
                            <p className="font-semibold text-white">{team.school}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span
                                className="text-xs px-2 py-0.5 rounded"
                                style={{ backgroundColor: TIER_COLORS[team.tier] + "20", color: TIER_COLORS[team.tier] }}
                              >
                                {team.tier_label}
                              </span>
                              <span className="text-xs text-gray-400">{team.conference}</span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className={`text-xl font-bold ${getScoreColor(team.power_score)}`}>
                            {team.power_score.toFixed(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-white font-medium">{team.wins}-{team.losses}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className={team.sp_plus_overall >= 0 ? "text-green-400" : "text-red-400"}>
                            {team.sp_plus_overall >= 0 ? "+" : ""}{team.sp_plus_overall.toFixed(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-white">{team.pff_avg > 0 ? team.pff_avg.toFixed(1) : "—"}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-white">
                            {team.portal_rank ? `#${team.portal_rank}` : "—"}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className={team.nil_valuation_change && team.nil_valuation_change > 0 ? "text-green-400" : "text-gray-400"}>
                            {formatNIL(team.nil_valuation_change)}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          {expandedTeam === team.school ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </td>
                      </tr>

                      {/* Expanded Details */}
                      {expandedTeam === team.school && (
                        <tr>
                          <td colSpan={9} className="bg-[#0f1a2e] px-6 py-4">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              <div>
                                <h4 className="text-sm font-semibold text-[#D4AF37] mb-2">Performance</h4>
                                <div className="space-y-1 text-sm">
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">SP+ Offense:</span>
                                    <span className="text-white">{team.sp_plus_offense?.toFixed(1) || "—"}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">SP+ Defense:</span>
                                    <span className="text-white">{team.sp_plus_defense?.toFixed(1) || "—"}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Talent Composite:</span>
                                    <span className="text-white">{team.talent_composite || "—"}</span>
                                  </div>
                                </div>
                              </div>

                              <div>
                                <h4 className="text-sm font-semibold text-[#D4AF37] mb-2">Roster</h4>
                                <div className="space-y-1 text-sm">
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Roster Size:</span>
                                    <span className="text-white">{team.roster_size}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Roster Talent:</span>
                                    <span className="text-white">{team.roster_talent?.toFixed(1) || "—"}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">PFF Grade:</span>
                                    <span className="text-white">{team.pff_avg > 0 ? team.pff_avg.toFixed(1) : "—"}</span>
                                  </div>
                                </div>
                              </div>

                              <div>
                                <h4 className="text-sm font-semibold text-[#D4AF37] mb-2">Portal Activity</h4>
                                <div className="space-y-1 text-sm">
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Transfers In/Out:</span>
                                    <span className="text-white">+{team.transfers_in}/-{team.transfers_out}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Net:</span>
                                    <span className={team.portal_net >= 0 ? "text-green-400" : "text-red-400"}>
                                      {team.portal_net >= 0 ? "+" : ""}{team.portal_net}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">5⭐ Net:</span>
                                    <span className={team.five_stars_net >= 0 ? "text-green-400" : "text-red-400"}>
                                      {team.five_stars_net >= 0 ? "+" : ""}{team.five_stars_net}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>

            {rankings.length === 0 && (
              <div className="p-12 text-center text-gray-400">
                No teams found matching your filters.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Note */}
      <div className="max-w-7xl mx-auto mt-6 text-center text-sm text-gray-500">
        Rankings updated with real CFBD, On3, ESPN, and PFF data • Algorithm proprietary to Portal IQ
      </div>
    </div>
  );
}
