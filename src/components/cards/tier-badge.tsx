import { Badge } from "@/components/ui/badge";
import { cn, tierConfig, riskConfig } from "@/lib/utils";
import type { NILTier, RiskLevel } from "@/types";

interface TierBadgeProps {
  tier: NILTier;
  className?: string;
}

export function TierBadge({ tier, className }: TierBadgeProps) {
  const config = tierConfig[tier];

  return (
    <Badge
      className={cn(config.bgClass, config.textClass, "font-semibold", className)}
    >
      {config.label}
    </Badge>
  );
}

interface RiskBadgeProps {
  level: RiskLevel;
  showLabel?: boolean;
  className?: string;
}

export function RiskBadge({
  level,
  showLabel = true,
  className,
}: RiskBadgeProps) {
  const config = riskConfig[level];

  return (
    <Badge
      className={cn(config.bgClass, config.textClass, "font-semibold", className)}
    >
      {showLabel ? config.label : level}
    </Badge>
  );
}

interface StockTrendBadgeProps {
  trend: "rising" | "stable" | "falling";
  className?: string;
}

export function StockTrendBadge({ trend, className }: StockTrendBadgeProps) {
  const config = {
    rising: { icon: "📈", label: "Rising", className: "bg-green-500/20 text-green-500" },
    stable: { icon: "➡️", label: "Stable", className: "bg-blue-500/20 text-blue-500" },
    falling: { icon: "📉", label: "Falling", className: "bg-red-500/20 text-red-500" },
  };

  const { icon, label, className: badgeClass } = config[trend];

  return (
    <Badge variant="outline" className={cn(badgeClass, "font-medium", className)}>
      {icon} {label}
    </Badge>
  );
}

interface GradeBadgeProps {
  grade: string;
  className?: string;
}

export function GradeBadge({ grade, className }: GradeBadgeProps) {
  const gradeColors: Record<string, string> = {
    "A+": "bg-green-500 text-white",
    A: "bg-green-500 text-white",
    "A-": "bg-green-400 text-white",
    "B+": "bg-lime-500 text-white",
    B: "bg-yellow-500 text-black",
    "B-": "bg-yellow-400 text-black",
    "C+": "bg-orange-400 text-white",
    C: "bg-orange-500 text-white",
    "C-": "bg-orange-600 text-white",
    D: "bg-red-500 text-white",
    F: "bg-red-700 text-white",
  };

  return (
    <Badge className={cn(gradeColors[grade] || "bg-gray-500", "font-bold", className)}>
      {grade}
    </Badge>
  );
}
