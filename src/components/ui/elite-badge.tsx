"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Zap, Trophy, Medal, Target } from "lucide-react";

/**
 * Athletic tier definitions matching the backend elite_traits.py thresholds.
 * Top 10% measurables by position = elite bonus.
 */
export type AthleticTier = "elite" | "above_average" | "good" | "average";

interface EliteBadgeProps {
  tier: AthleticTier;
  eliteBonus?: number;
  eliteTraits?: string[];
  showDetails?: boolean;
  className?: string;
}

const tierConfig: Record<
  AthleticTier,
  {
    label: string;
    description: string;
    icon: typeof Zap;
    bgClass: string;
    textClass: string;
    borderClass: string;
    glowClass?: string;
  }
> = {
  elite: {
    label: "Elite Athlete",
    description: "Top 10% measurables for position",
    icon: Zap,
    bgClass: "bg-gradient-to-r from-amber-500/20 to-yellow-500/20",
    textClass: "text-amber-400",
    borderClass: "border-amber-500/50",
    glowClass: "shadow-amber-500/20 shadow-lg",
  },
  above_average: {
    label: "Above Average",
    description: "Top 20% measurables for position",
    icon: Trophy,
    bgClass: "bg-blue-500/10",
    textClass: "text-blue-400",
    borderClass: "border-blue-500/30",
  },
  good: {
    label: "Good Athlete",
    description: "Top 35% measurables for position",
    icon: Medal,
    bgClass: "bg-slate-500/10",
    textClass: "text-slate-400",
    borderClass: "border-slate-500/30",
  },
  average: {
    label: "Average",
    description: "Standard measurables for position",
    icon: Target,
    bgClass: "bg-slate-800/50",
    textClass: "text-slate-500",
    borderClass: "border-slate-700/30",
  },
};

/**
 * Elite Badge Component
 *
 * Displays a player's athletic tier based on their measurables.
 * Only shows for players with meaningful athletic distinction.
 *
 * Usage:
 * ```tsx
 * <EliteBadge tier="elite" eliteTraits={["forty", "ras", "vertical"]} />
 * ```
 */
export function EliteBadge({
  tier,
  eliteBonus = 1.0,
  eliteTraits = [],
  showDetails = false,
  className,
}: EliteBadgeProps) {
  // Don't show badge for average athletes (no special treatment)
  if (tier === "average") {
    return null;
  }

  const config = tierConfig[tier];
  const Icon = config.icon;

  // Format bonus percentage
  const bonusPercent = Math.round((eliteBonus - 1) * 100);
  const bonusText = bonusPercent > 0 ? `+${bonusPercent}%` : null;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold transition-all",
        config.bgClass,
        config.textClass,
        config.borderClass,
        config.glowClass,
        className
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      <span>{config.label}</span>
      {bonusText && (
        <span className="ml-0.5 opacity-75 text-[10px]">{bonusText}</span>
      )}

      {/* Tooltip-style details on hover */}
      {showDetails && eliteTraits.length > 0 && (
        <div className="hidden group-hover:block absolute top-full left-0 mt-1 p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs z-10 min-w-[150px]">
          <div className="text-slate-400 mb-1">{config.description}</div>
          <div className="text-slate-300">
            Elite traits: {eliteTraits.join(", ")}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for table cells and tight spaces
 */
export function EliteBadgeCompact({
  tier,
  className,
}: {
  tier: AthleticTier;
  className?: string;
}) {
  if (tier === "average") {
    return null;
  }

  const config = tierConfig[tier];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center w-6 h-6 rounded-full",
        config.bgClass,
        config.textClass,
        config.borderClass,
        className
      )}
      title={config.label}
    >
      <Icon className="h-3.5 w-3.5" />
    </div>
  );
}

/**
 * Format elite traits for display
 */
export function formatEliteTrait(trait: string): string {
  const traitLabels: Record<string, string> = {
    height: "Height",
    weight: "Weight",
    forty: "40-Yard",
    ras: "RAS",
    vertical: "Vertical",
    broad_jump: "Broad Jump",
    three_cone: "3-Cone",
    shuttle: "Shuttle",
    bench: "Bench",
    arm_length: "Arm Length",
  };
  return traitLabels[trait] || trait;
}

/**
 * Get tier from elite bonus value
 */
export function getTierFromBonus(eliteBonus: number): AthleticTier {
  if (eliteBonus >= 1.25) return "elite";
  if (eliteBonus >= 1.15) return "above_average";
  if (eliteBonus >= 1.08) return "good";
  return "average";
}

export { tierConfig };
