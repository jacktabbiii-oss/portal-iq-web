import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import numeral from "numeral";
import type { NILTier, RiskLevel, DraftGrade } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Currency formatting
export function formatCurrency(
  value: number,
  options?: { compact?: boolean; decimals?: number }
): string {
  if (options?.compact) {
    if (value >= 1_000_000) {
      return `$${numeral(value).format("0.0a").toUpperCase()}`;
    }
    if (value >= 1_000) {
      return `$${numeral(value).format("0a").toUpperCase()}`;
    }
  }
  return numeral(value).format("$0,0");
}

// Percentage formatting
export function formatPercentage(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

// Number formatting with commas
export function formatNumber(value: number): string {
  return numeral(value).format("0,0");
}

// NIL Tier utilities
export const tierConfig: Record<
  NILTier,
  { label: string; color: string; bgClass: string; textClass: string }
> = {
  mega: {
    label: "MEGA",
    color: "#FFD700",
    bgClass: "bg-yellow-500",
    textClass: "text-black",
  },
  premium: {
    label: "PREMIUM",
    color: "#9C27B0",
    bgClass: "bg-purple-500",
    textClass: "text-white",
  },
  solid: {
    label: "SOLID",
    color: "#2196F3",
    bgClass: "bg-blue-500",
    textClass: "text-white",
  },
  moderate: {
    label: "MODERATE",
    color: "#00C853",
    bgClass: "bg-emerald-500",
    textClass: "text-white",
  },
  entry: {
    label: "ENTRY",
    color: "#9E9E9E",
    bgClass: "bg-gray-500",
    textClass: "text-white",
  },
};

export function getTierFromValue(value: number): NILTier {
  if (value >= 1_000_000) return "mega";
  if (value >= 250_000) return "premium";
  if (value >= 50_000) return "solid";
  if (value >= 10_000) return "moderate";
  return "entry";
}

// Risk Level utilities
export const riskConfig: Record<
  RiskLevel,
  { label: string; color: string; bgClass: string; textClass: string }
> = {
  critical: {
    label: "CRITICAL",
    color: "#F44336",
    bgClass: "bg-red-500",
    textClass: "text-white",
  },
  high: {
    label: "HIGH",
    color: "#FF9800",
    bgClass: "bg-orange-500",
    textClass: "text-white",
  },
  moderate: {
    label: "MODERATE",
    color: "#FFC107",
    bgClass: "bg-yellow-500",
    textClass: "text-black",
  },
  low: {
    label: "LOW",
    color: "#4CAF50",
    bgClass: "bg-green-500",
    textClass: "text-white",
  },
};

export function getRiskLevel(probability: number): RiskLevel {
  if (probability >= 0.75) return "critical";
  if (probability >= 0.5) return "high";
  if (probability >= 0.25) return "moderate";
  return "low";
}

// Draft Grade utilities
export const gradeColors: Record<string, string> = {
  "A+": "#00C853",
  A: "#00C853",
  "A-": "#4CAF50",
  "B+": "#8BC34A",
  B: "#CDDC39",
  "B-": "#FFEB3B",
  "C+": "#FFC107",
  C: "#FF9800",
  "C-": "#FF5722",
  D: "#F44336",
  F: "#B71C1C",
};

// Position utilities
export const positionGroups = {
  offense: ["QB", "RB", "WR", "TE", "OT", "OG", "C"],
  defense: ["EDGE", "DT", "ILB", "OLB", "CB", "S"],
  specialTeams: ["K", "P", "LS"],
};

export function getPositionGroup(position: string): string {
  for (const [group, positions] of Object.entries(positionGroups)) {
    if (positions.includes(position)) return group;
  }
  return "other";
}

// School tier utilities
export const schoolTiers: Record<number, string[]> = {
  5: [
    "Alabama",
    "Ohio State",
    "Georgia",
    "Michigan",
    "USC",
    "Notre Dame",
    "Texas",
    "Oklahoma",
    "Clemson",
  ],
  4: [
    "Oregon",
    "Penn State",
    "Florida",
    "Auburn",
    "Tennessee",
    "Miami",
    "Florida State",
    "Texas A&M",
    "LSU",
  ],
  3: [
    "UCLA",
    "Michigan State",
    "Washington",
    "Iowa",
    "Utah",
    "Ole Miss",
    "Arkansas",
    "Wisconsin",
  ],
};

export function getSchoolTier(school: string): number {
  for (const [tier, schools] of Object.entries(schoolTiers)) {
    if (schools.includes(school)) return parseInt(tier);
  }
  return 2;
}

// Date utilities
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffInSeconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (diffInSeconds < 60) return "just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800)
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  return formatDate(date);
}

// Constants
export const CONFERENCES = [
  "SEC",
  "Big Ten",
  "Big 12",
  "ACC",
  "Pac-12",
  "American",
  "Mountain West",
  "Sun Belt",
  "MAC",
  "Conference USA",
];

export const POSITIONS = [
  "QB",
  "RB",
  "WR",
  "TE",
  "OT",
  "OG",
  "C",
  "EDGE",
  "DT",
  "ILB",
  "OLB",
  "CB",
  "S",
  "K",
  "P",
];

export const CLASS_YEARS = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"];
