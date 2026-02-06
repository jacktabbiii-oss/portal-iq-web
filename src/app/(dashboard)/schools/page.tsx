"use client";

import { useState } from "react";
import Link from "next/link";
import { SCHOOL_LIST } from "@/lib/api/team";

// School tiers for display
const SCHOOL_TIERS: Record<string, { schools: string[]; color: string; label: string }> = {
  elite: {
    schools: ["Alabama", "Georgia", "Ohio State", "Michigan", "Texas", "Oregon", "Penn State", "Notre Dame", "USC", "Clemson"],
    color: "#D4AF37",
    label: "Elite",
  },
  power: {
    schools: ["LSU", "Oklahoma", "Florida", "Miami", "Tennessee", "Auburn", "Texas A&M", "Wisconsin", "UCLA", "Washington", "Utah", "Ole Miss", "Missouri", "Florida State", "Louisville", "Kentucky", "Arkansas"],
    color: "#3B82F6",
    label: "Power",
  },
  rising: {
    schools: ["Colorado", "Indiana", "Illinois", "Iowa State", "Kansas State", "Arizona", "NC State", "Virginia Tech", "Baylor", "Pittsburgh", "SMU", "Syracuse", "Duke", "California", "Nebraska"],
    color: "#22C55E",
    label: "Rising",
  },
};

function getSchoolTier(school: string): { tier: string; color: string; label: string } {
  for (const [tierName, tierData] of Object.entries(SCHOOL_TIERS)) {
    if (tierData.schools.some((s) => s.toLowerCase() === school.toLowerCase())) {
      return { tier: tierName, color: tierData.color, label: tierData.label };
    }
  }
  return { tier: "other", color: "#6B7280", label: "Other" };
}

export default function SchoolsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedConference, setSelectedConference] = useState("all");

  const conferences = {
    all: "All Schools",
    sec: "SEC",
    bigten: "Big Ten",
    acc: "ACC",
    big12: "Big 12",
  };

  // Conference school mappings (simplified)
  const conferenceSchools: Record<string, string[]> = {
    sec: ["Alabama", "Arkansas", "Auburn", "Florida", "Georgia", "Kentucky", "LSU", "Mississippi State", "Missouri", "Oklahoma", "Ole Miss", "South Carolina", "Tennessee", "Texas", "Texas A&M", "Vanderbilt"],
    bigten: ["Illinois", "Indiana", "Iowa", "Maryland", "Michigan", "Michigan State", "Minnesota", "Nebraska", "Northwestern", "Ohio State", "Oregon", "Penn State", "Purdue", "Rutgers", "UCLA", "USC", "Washington", "Wisconsin"],
    acc: ["Boston College", "California", "Clemson", "Duke", "Florida State", "Georgia Tech", "Louisville", "Miami", "NC State", "North Carolina", "Notre Dame", "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia", "Virginia Tech", "Wake Forest"],
    big12: ["Arizona", "Arizona State", "Baylor", "BYU", "Cincinnati", "Colorado", "Houston", "Iowa State", "Kansas", "Kansas State", "Oklahoma State", "TCU", "Texas Tech", "UCF", "Utah", "West Virginia"],
  };

  const filteredSchools = SCHOOL_LIST.filter((school) => {
    const matchesSearch = school.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesConference =
      selectedConference === "all" ||
      conferenceSchools[selectedConference]?.includes(school);
    return matchesSearch && matchesConference;
  });

  // Group by tier
  const groupedSchools = {
    elite: filteredSchools.filter((s) => SCHOOL_TIERS.elite.schools.includes(s)),
    power: filteredSchools.filter((s) => SCHOOL_TIERS.power.schools.includes(s)),
    rising: filteredSchools.filter((s) => SCHOOL_TIERS.rising.schools.includes(s)),
    other: filteredSchools.filter(
      (s) =>
        !SCHOOL_TIERS.elite.schools.includes(s) &&
        !SCHOOL_TIERS.power.schools.includes(s) &&
        !SCHOOL_TIERS.rising.schools.includes(s)
    ),
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-2">Schools</h1>
      <p className="text-gray-400 mb-6">
        Browse schools and analyze their transfer portal activity.
      </p>

      {/* Filters */}
      <div className="bg-[#1a2744] rounded-xl p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search schools..."
              className="w-full bg-[#243354] border border-[#3a4d6e] rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-[#D4AF37]"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(conferences).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setSelectedConference(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  selectedConference === key
                    ? "bg-[#D4AF37] text-[#0f1a2e]"
                    : "bg-[#243354] text-gray-300 hover:bg-[#2a3d5e]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Schools Grid by Tier */}
      {Object.entries(groupedSchools).map(
        ([tier, schools]) =>
          schools.length > 0 && (
            <div key={tier} className="mb-8">
              <div className="flex items-center gap-3 mb-4">
                <h2
                  className="text-lg font-bold"
                  style={{
                    color:
                      tier === "elite"
                        ? "#D4AF37"
                        : tier === "power"
                        ? "#3B82F6"
                        : tier === "rising"
                        ? "#22C55E"
                        : "#6B7280",
                  }}
                >
                  {tier === "elite"
                    ? "Elite Programs"
                    : tier === "power"
                    ? "Power Programs"
                    : tier === "rising"
                    ? "Rising Programs"
                    : "Other Programs"}
                </h2>
                <span className="text-gray-500 text-sm">({schools.length})</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {schools.map((school) => {
                  const tierInfo = getSchoolTier(school);
                  return (
                    <Link
                      key={school}
                      href={`/team-analysis?school=${encodeURIComponent(school)}`}
                      className="bg-[#1a2744] hover:bg-[#243354] rounded-lg p-4 transition group"
                    >
                      <p className="text-white font-medium group-hover:text-[#D4AF37] transition">
                        {school}
                      </p>
                      <p className="text-xs mt-1" style={{ color: tierInfo.color }}>
                        {tierInfo.label}
                      </p>
                    </Link>
                  );
                })}
              </div>
            </div>
          )
      )}

      {filteredSchools.length === 0 && (
        <div className="bg-[#1a2744] rounded-xl p-12 text-center">
          <p className="text-gray-400">No schools found matching your search.</p>
        </div>
      )}
    </div>
  );
}
