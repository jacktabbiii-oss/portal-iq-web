"use client";

import { useState } from "react";
import { compareTeams, SCHOOL_LIST, type TeamComparison } from "@/lib/api/team";
import { X, Plus, GitCompare, TrendingUp, Users, Activity } from "lucide-react";

const POSITION_COLORS: Record<string, string> = {
  QB: "#D4AF37",
  RB: "#22C55E",
  WR: "#3B82F6",
  TE: "#8B5CF6",
  OL: "#F59E0B",
  DL: "#EF4444",
  LB: "#14B8A6",
  DB: "#06B6D4",
};

export default function TeamComparePage() {
  const [selectedSchools, setSelectedSchools] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [comparisons, setComparisons] = useState<TeamComparison[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredSchools = SCHOOL_LIST.filter(
    (s) =>
      s.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !selectedSchools.includes(s)
  );

  const addSchool = (school: string) => {
    if (selectedSchools.length < 4) {
      setSelectedSchools([...selectedSchools, school]);
      setSearchQuery("");
    }
  };

  const removeSchool = (school: string) => {
    setSelectedSchools(selectedSchools.filter((s) => s !== school));
    // Clear comparisons when removing schools
    if (selectedSchools.length - 1 === 0) {
      setComparisons([]);
    }
  };

  const handleCompare = async () => {
    if (selectedSchools.length < 2) {
      setError("Select at least 2 schools to compare");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await compareTeams(selectedSchools);
      setComparisons(response.comparisons);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compare teams");
    } finally {
      setLoading(false);
    }
  };

  const formatNIL = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value}`;
  };

  const getTopPositions = (breakdown: Record<string, number>) => {
    return Object.entries(breakdown)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);
  };

  return (
    <div className="min-h-screen bg-[#0f1a2e] text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center gap-3 mb-2">
          <GitCompare className="w-8 h-8 text-[#D4AF37]" />
          <h1 className="text-3xl font-bold">Team Comparison</h1>
        </div>
        <p className="text-gray-400">
          Compare multiple teams side-by-side across all metrics: performance, roster, portal, and NIL
        </p>
      </div>

      {/* School Selection */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-[#1a2744] rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Select Teams to Compare (2-4 teams)</h2>

          {/* Selected Schools */}
          <div className="flex flex-wrap gap-2 mb-4">
            {selectedSchools.map((school) => (
              <div
                key={school}
                className="bg-[#243354] px-4 py-2 rounded-lg flex items-center gap-2 border border-[#D4AF37]/20"
              >
                <span className="text-white font-medium">{school}</span>
                <button
                  onClick={() => removeSchool(school)}
                  className="text-gray-400 hover:text-red-400 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}

            {selectedSchools.length < 4 && (
              <div className="relative flex-1 min-w-[250px]">
                <input
                  type="text"
                  placeholder="Search for a team..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-[#243354] border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent"
                />

                {/* Dropdown */}
                {searchQuery && filteredSchools.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-[#243354] border border-gray-600 rounded-lg max-h-60 overflow-y-auto z-10">
                    {filteredSchools.slice(0, 10).map((school) => (
                      <button
                        key={school}
                        onClick={() => addSchool(school)}
                        className="w-full px-4 py-2 text-left hover:bg-[#1a2744] transition-colors text-white"
                      >
                        {school}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Compare Button */}
          <button
            onClick={handleCompare}
            disabled={selectedSchools.length < 2 || loading}
            className="bg-[#D4AF37] hover:bg-[#D4AF37]/90 disabled:bg-gray-600 disabled:cursor-not-allowed text-[#0f1a2e] font-semibold px-6 py-3 rounded-lg transition-colors flex items-center gap-2"
          >
            <GitCompare className="w-5 h-5" />
            {loading ? "Comparing..." : `Compare ${selectedSchools.length} Teams`}
          </button>

          {error && (
            <div className="mt-4 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
              <p className="text-red-400">{error}</p>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Results */}
      {comparisons.length > 0 && (
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {comparisons.map((team, idx) => (
              <div key={team.school} className="bg-[#1a2744] rounded-xl p-6 border border-[#D4AF37]/20">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white">{team.school}</h3>
                  <span className="text-sm text-gray-400">#{idx + 1}</span>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Conference:</span>
                    <span className="text-white font-medium">{team.conference}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Tier:</span>
                    <span className="text-[#D4AF37]">{team.tier_label}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Record:</span>
                    <span className="text-white font-medium">{team.wins}-{team.losses}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Performance Comparison */}
          <div className="bg-[#1a2744] rounded-xl p-6">
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp className="w-5 h-5 text-[#3B82F6]" />
              <h2 className="text-xl font-bold">Performance Metrics</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Metric</th>
                    {comparisons.map((team) => (
                      <th key={team.school} className="px-4 py-3 text-center text-sm font-semibold text-white">
                        {team.school}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-400">SP+ Overall</td>
                    {comparisons.map((team) => (
                      <td key={team.school} className="px-4 py-3 text-center">
                        <span className={team.sp_plus_overall >= 0 ? "text-green-400" : "text-red-400"}>
                          {team.sp_plus_overall >= 0 ? "+" : ""}{team.sp_plus_overall.toFixed(1)}
                        </span>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-400">SP+ Offense</td>
                    {comparisons.map((team) => (
                      <td key={team.school} className="px-4 py-3 text-center text-white">
                        {team.sp_plus_offense >= 0 ? "+" : ""}{team.sp_plus_offense.toFixed(1)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-400">SP+ Defense</td>
                    {comparisons.map((team) => (
                      <td key={team.school} className="px-4 py-3 text-center text-white">
                        {team.sp_plus_defense >= 0 ? "+" : ""}{team.sp_plus_defense.toFixed(1)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-400">Talent Composite</td>
                    {comparisons.map((team) => (
                      <td key={team.school} className="px-4 py-3 text-center text-white">
                        {team.talent_composite || "—"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Roster Comparison */}
          <div className="bg-[#1a2744] rounded-xl p-6">
            <div className="flex items-center gap-2 mb-6">
              <Users className="w-5 h-5 text-[#22C55E]" />
              <h2 className="text-xl font-bold">Roster Analysis</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* PFF Grades */}
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-3">PFF Grades</h3>
                <div className="space-y-2">
                  {comparisons.map((team) => (
                    <div key={team.school} className="flex items-center justify-between bg-[#243354] rounded-lg p-3">
                      <span className="text-white font-medium">{team.school}</span>
                      <div className="flex gap-3 text-sm">
                        <span className="text-gray-400">
                          Overall: <span className="text-white font-semibold">{team.pff_grades.pff_overall?.toFixed(1) || "—"}</span>
                        </span>
                        <span className="text-gray-400">
                          Off: <span className="text-green-400">{team.pff_grades.pff_offense?.toFixed(1) || "—"}</span>
                        </span>
                        <span className="text-gray-400">
                          Def: <span className="text-blue-400">{team.pff_grades.pff_defense?.toFixed(1) || "—"}</span>
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Roster Size & Portal */}
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-3">Roster & Portal Activity</h3>
                <div className="space-y-2">
                  {comparisons.map((team) => (
                    <div key={team.school} className="flex items-center justify-between bg-[#243354] rounded-lg p-3">
                      <span className="text-white font-medium">{team.school}</span>
                      <div className="flex gap-3 text-sm">
                        <span className="text-gray-400">
                          Size: <span className="text-white font-semibold">{team.roster_size}</span>
                        </span>
                        <span className="text-gray-400">
                          Portal: <span className="text-red-400">{team.portal_outgoing}</span>
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Top Positions */}
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">Top Position Groups</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {comparisons.map((team) => (
                  <div key={team.school} className="bg-[#243354] rounded-lg p-4">
                    <h4 className="text-white font-semibold mb-3">{team.school}</h4>
                    <div className="space-y-2">
                      {getTopPositions(team.position_breakdown).map(([pos, count]) => (
                        <div key={pos} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: POSITION_COLORS[pos] || "#6B7280" }}
                            />
                            <span className="text-sm text-gray-300">{pos}</span>
                          </div>
                          <span className="text-sm text-white font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* NIL Comparison */}
          <div className="bg-[#1a2744] rounded-xl p-6">
            <div className="flex items-center gap-2 mb-6">
              <Activity className="w-5 h-5 text-[#D4AF37]" />
              <h2 className="text-xl font-bold">NIL Investment</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {comparisons.map((team) => (
                <div key={team.school} className="bg-[#243354] rounded-lg p-4">
                  <h4 className="text-white font-semibold mb-3">{team.school}</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Total NIL:</span>
                      <span className="text-[#D4AF37] font-bold">{formatNIL(team.nil_total)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Average NIL:</span>
                      <span className="text-white">{formatNIL(team.nil_avg)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {comparisons.length === 0 && !loading && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-[#1a2744] rounded-xl p-12 text-center">
            <GitCompare className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">
              Select 2-4 teams above to start comparing
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
