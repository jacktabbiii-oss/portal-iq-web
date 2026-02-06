"use client";

import Link from "next/link";

const REPORT_TYPES = [
  {
    id: "team-portal",
    title: "Team Portal Report",
    description: "Comprehensive analysis of a team's transfer portal activity",
    icon: "🏈",
    href: "/team-analysis",
    available: true,
  },
  {
    id: "nil-leaderboard",
    title: "NIL Leaderboard Report",
    description: "Top players by NIL valuation with WAR metrics",
    icon: "💰",
    href: "/win-impact",
    available: true,
  },
  {
    id: "position-analysis",
    title: "Position Analysis Report",
    description: "Deep dive into specific positions across the portal",
    icon: "📊",
    href: "/portal-intelligence",
    available: true,
  },
  {
    id: "conference-comparison",
    title: "Conference Comparison",
    description: "Compare portal activity across conferences",
    icon: "🏆",
    href: "#",
    available: false,
  },
  {
    id: "trend-analysis",
    title: "Portal Trends Report",
    description: "Historical trends and predictions",
    icon: "📈",
    href: "#",
    available: false,
  },
  {
    id: "custom-report",
    title: "Custom Report Builder",
    description: "Build your own custom reports (Enterprise)",
    icon: "⚙️",
    href: "#",
    available: false,
  },
];

export default function ReportsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-2">Reports</h1>
      <p className="text-gray-400 mb-6">Generate and download analytical reports</p>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {REPORT_TYPES.map((report) => (
          <Link
            key={report.id}
            href={report.available ? report.href : "#"}
            className={`bg-[#1a2744] rounded-xl p-6 transition ${
              report.available
                ? "hover:bg-[#243354] cursor-pointer"
                : "opacity-60 cursor-not-allowed"
            }`}
          >
            <div className="text-4xl mb-4">{report.icon}</div>
            <h3 className="text-white font-bold text-lg mb-2">{report.title}</h3>
            <p className="text-gray-400 text-sm mb-4">{report.description}</p>
            {report.available ? (
              <span className="text-[#D4AF37] text-sm font-medium">
                Generate Report →
              </span>
            ) : (
              <span className="bg-[#243354] text-gray-400 px-3 py-1 rounded-full text-xs">
                Coming Soon
              </span>
            )}
          </Link>
        ))}
      </div>

      {/* Recent Reports */}
      <div className="mt-8">
        <h2 className="text-lg font-bold text-white mb-4">Recent Reports</h2>
        <div className="bg-[#1a2744] rounded-xl p-6">
          <div className="text-center text-gray-400 py-8">
            <p>No recent reports</p>
            <p className="text-sm mt-1">Reports you generate will appear here</p>
          </div>
        </div>
      </div>
    </div>
  );
}
