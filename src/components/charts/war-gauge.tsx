"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Target, TrendingUp, DollarSign, Zap } from "lucide-react";

interface WARGaugeProps {
  war: number;
  warLow?: number;
  warHigh?: number;
  confidence?: "high" | "medium" | "low";
  position?: string;
  compact?: boolean;
}

function getGradeColor(war: number): string {
  if (war >= 2.0) return "#22c55e"; // Elite - green
  if (war >= 1.2) return "#D4AF37"; // Premium - gold
  if (war >= 0.6) return "#f59e0b"; // Solid - amber
  return "#6b7280"; // Average - gray
}

function getGradeLabel(war: number): string {
  if (war >= 2.0) return "Elite";
  if (war >= 1.2) return "Premium";
  if (war >= 0.6) return "Solid";
  return "Average";
}

export function WARGauge({
  war,
  warLow,
  warHigh,
  confidence,
  position,
  compact = false,
}: WARGaugeProps) {
  const color = getGradeColor(war);
  const grade = getGradeLabel(war);

  // Calculate arc path for gauge
  const gaugeData = useMemo(() => {
    const maxWAR = 4.0; // Max expected WAR
    const percentage = Math.min(war / maxWAR, 1);
    const angle = percentage * 180; // 180 degree arc

    // SVG arc calculation
    const radius = compact ? 40 : 60;
    const centerX = compact ? 50 : 70;
    const centerY = compact ? 50 : 70;

    const startAngle = -180;
    const endAngle = startAngle + angle;

    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const x1 = centerX + radius * Math.cos(startRad);
    const y1 = centerY + radius * Math.sin(startRad);
    const x2 = centerX + radius * Math.cos(endRad);
    const y2 = centerY + radius * Math.sin(endRad);

    const largeArcFlag = angle > 180 ? 1 : 0;

    return {
      path: `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
      bgPath: `M ${centerX - radius} ${centerY} A ${radius} ${radius} 0 0 1 ${centerX + radius} ${centerY}`,
      centerX,
      centerY,
      radius,
    };
  }, [war, compact]);

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <svg width="100" height="60" viewBox="0 0 100 60">
          {/* Background arc */}
          <path
            d={gaugeData.bgPath}
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="8"
            strokeLinecap="round"
          />
          {/* Value arc */}
          <path
            d={gaugeData.path}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
          />
          {/* Center text */}
          <text
            x={gaugeData.centerX}
            y={gaugeData.centerY + 5}
            textAnchor="middle"
            fill="white"
            fontSize="16"
            fontWeight="bold"
          >
            {war.toFixed(2)}
          </text>
        </svg>
        <div>
          <Badge
            className="uppercase text-xs"
            style={{ backgroundColor: `${color}20`, color, borderColor: color }}
          >
            {grade}
          </Badge>
          {confidence && (
            <p className="text-xs text-muted-foreground mt-1 capitalize">
              {confidence} confidence
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="text-center">
      <svg width="140" height="90" viewBox="0 0 140 90">
        {/* Background arc */}
        <path
          d={gaugeData.bgPath}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={gaugeData.path}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          style={{
            filter: `drop-shadow(0 0 8px ${color}40)`,
          }}
        />
        {/* Center text */}
        <text
          x={gaugeData.centerX}
          y={gaugeData.centerY + 10}
          textAnchor="middle"
          fill="white"
          fontSize="24"
          fontWeight="bold"
        >
          {war.toFixed(2)}
        </text>
        <text
          x={gaugeData.centerX}
          y={gaugeData.centerY + 28}
          textAnchor="middle"
          fill="rgba(255,255,255,0.5)"
          fontSize="10"
        >
          WAR
        </text>
      </svg>
      <Badge
        className="uppercase text-xs mt-2"
        style={{ backgroundColor: `${color}20`, color, borderColor: color }}
      >
        {grade}
      </Badge>
      {warLow !== undefined && warHigh !== undefined && (
        <p className="text-xs text-muted-foreground mt-2">
          Range: {warLow.toFixed(2)} - {warHigh.toFixed(2)}
        </p>
      )}
      {confidence && (
        <p className="text-xs text-muted-foreground capitalize">
          {confidence} confidence
        </p>
      )}
    </div>
  );
}

interface WARBreakdownProps {
  breakdown: {
    base_war: number;
    position_scarcity: number;
    star_multiplier: number;
    school_tier: string;
    school_multiplier: number;
    nil_bonus: number;
  };
}

export function WARBreakdown({ breakdown }: WARBreakdownProps) {
  const items = [
    { label: "Base WAR", value: breakdown.base_war.toFixed(2), icon: Target },
    { label: "Position Scarcity", value: `${breakdown.position_scarcity.toFixed(2)}x`, icon: Zap },
    { label: "Star Multiplier", value: `${breakdown.star_multiplier.toFixed(2)}x`, icon: TrendingUp },
    { label: `School (${breakdown.school_tier})`, value: `${breakdown.school_multiplier.toFixed(2)}x`, icon: Target },
    { label: "NIL Bonus", value: `+${breakdown.nil_bonus.toFixed(2)}`, icon: DollarSign },
  ];

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.label} className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2 text-muted-foreground">
            <item.icon className="h-3 w-3" />
            {item.label}
          </span>
          <span className="font-mono text-foreground">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

interface TransferValueProps {
  costPerWAR: number;
  fairValue: number;
  valueRatio: number;
  valueRating: string;
  roiProjection: string;
  marketComparison: string;
}

export function TransferValueAnalysis({
  costPerWAR,
  fairValue,
  valueRatio,
  valueRating,
  roiProjection,
  marketComparison,
}: TransferValueProps) {
  const getRatingColor = (rating: string) => {
    switch (rating) {
      case "exceptional_value":
        return "text-green-500";
      case "good_value":
        return "text-green-400";
      case "fair_value":
        return "text-yellow-500";
      case "slight_overpay":
        return "text-orange-500";
      case "significant_overpay":
        return "text-red-500";
      default:
        return "text-muted-foreground";
    }
  };

  const formatRating = (rating: string) => {
    return rating.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value.toLocaleString()}`;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Cost per WAR</span>
        <span className="font-mono text-sm">{formatCurrency(costPerWAR)}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Fair Value</span>
        <span className="font-mono text-sm">{formatCurrency(fairValue)}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Value Ratio</span>
        <span className="font-mono text-sm">{valueRatio.toFixed(2)}x</span>
      </div>
      <div className="pt-2 border-t border-border">
        <p className={`font-semibold ${getRatingColor(valueRating)}`}>
          {formatRating(valueRating)}
        </p>
        <p className="text-xs text-muted-foreground mt-1">{roiProjection}</p>
        <p className="text-xs text-muted-foreground">{marketComparison}</p>
      </div>
    </div>
  );
}

interface PlayerWARCardProps {
  war: number;
  warLow: number;
  warHigh: number;
  confidence: "high" | "medium" | "low";
  winProbAdded: number;
  breakdown: WARBreakdownProps["breakdown"];
  transferValue?: TransferValueProps;
}

export function PlayerWARCard({
  war,
  warLow,
  warHigh,
  confidence,
  winProbAdded,
  breakdown,
  transferValue,
}: PlayerWARCardProps) {
  return (
    <Card className="glass">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Target className="h-4 w-4" />
          Win Impact (WAR)
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4 pt-0 space-y-4">
        <div className="flex justify-center">
          <WARGauge
            war={war}
            warLow={warLow}
            warHigh={warHigh}
            confidence={confidence}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-3 bg-card rounded-lg">
            <p className="text-xs text-muted-foreground">Win Prob Added</p>
            <p className="text-lg font-bold text-primary">+{winProbAdded.toFixed(1)}%</p>
          </div>
          <div className="text-center p-3 bg-card rounded-lg">
            <p className="text-xs text-muted-foreground">WAR Range</p>
            <p className="text-lg font-bold">{warLow.toFixed(2)} - {warHigh.toFixed(2)}</p>
          </div>
        </div>

        <div className="pt-2 border-t border-border">
          <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Breakdown</p>
          <WARBreakdown breakdown={breakdown} />
        </div>

        {transferValue && (
          <div className="pt-2 border-t border-border">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Transfer Value</p>
            <TransferValueAnalysis {...transferValue} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default WARGauge;
