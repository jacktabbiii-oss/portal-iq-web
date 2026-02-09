"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { FileText, TrendingUp, ArrowRightLeft, ArrowRight } from "lucide-react";

const REPORT_TYPES = [
  {
    id: "team-portal",
    title: "Team Portal Report",
    description: "Comprehensive analysis of a team's transfer portal activity, incoming and outgoing players, and roster impact.",
    icon: FileText,
    href: "/team-analysis",
  },
  {
    id: "nil-leaderboard",
    title: "NIL Leaderboard Report",
    description: "Top players by NIL valuation with WAR metrics and win impact analysis.",
    icon: TrendingUp,
    href: "/win-impact",
  },
  {
    id: "position-analysis",
    title: "Position Analysis Report",
    description: "Deep dive into specific positions across the transfer portal with filtering and comparison tools.",
    icon: ArrowRightLeft,
    href: "/portal-intelligence",
  },
];

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-1">Reports</h1>
        <p className="text-muted-foreground">Quick access to analytical reports and tools</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {REPORT_TYPES.map((report) => {
          const Icon = report.icon;
          return (
            <Link key={report.id} href={report.href}>
              <Card className="glass h-full hover:-translate-y-1 transition-all duration-200 cursor-pointer group">
                <CardContent className="p-6 flex flex-col h-full">
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">{report.title}</h3>
                  <p className="text-muted-foreground text-sm mb-4 flex-1">{report.description}</p>
                  <div className="flex items-center gap-2 text-primary font-semibold text-sm group-hover:translate-x-1 transition-transform">
                    View Report
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
