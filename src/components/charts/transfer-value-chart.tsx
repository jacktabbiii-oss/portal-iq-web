"use client";

import { useMemo, useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRightLeft, TrendingUp, Loader2 } from "lucide-react";
import { getSchoolTiers, type SchoolTierInfo } from "@/lib/api/team";

interface TransferValueChartProps {
  currentSchool: string;
  currentValue: number;
  position: string;
}

// Tier display labels
const TIER_LABELS: Record<string, string> = {
  blue_blood: "Blue Blood",
  elite: "Elite",
  power_strong: "Strong P4",
  power_mid: "Mid P4",
  power_low: "Lower P4",
  g5_strong: "Strong G5",
  g5_mid: "Mid G5",
  fcs: "FCS",
};

function formatCurrency(value: number): string {
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  } else if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

export function TransferValueChart({
  currentSchool,
  currentValue,
  position,
}: TransferValueChartProps) {
  const [allSchools, setAllSchools] = useState<SchoolTierInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getSchoolTiers();
        if (!cancelled && data.all_schools) {
          setAllSchools(data.all_schools);
        }
      } catch {
        // Will use empty list — chart won't render comparison schools
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Find current school multiplier from API data
  const currentMultiplier = useMemo(() => {
    const match = allSchools.find(
      (s) => s.school.toLowerCase() === currentSchool.toLowerCase()
    );
    return match?.multiplier || 1.0;
  }, [allSchools, currentSchool]);

  const baseValue = currentValue / currentMultiplier;

  // Generate comparison data from top schools by score
  const comparisonData = useMemo(() => {
    if (allSchools.length === 0) return [];

    // Take top 12 schools by score (these are the most relevant comparisons)
    const topSchools = allSchools
      .slice(0, 15)
      .map((s) => {
        const projectedValue = baseValue * s.multiplier;
        const difference = projectedValue - currentValue;
        const percentChange = currentValue > 0 ? ((projectedValue - currentValue) / currentValue) * 100 : 0;

        return {
          school: s.school,
          value: projectedValue,
          multiplier: s.multiplier,
          tier: TIER_LABELS[s.tier] || s.tier,
          difference,
          percentChange,
          isCurrent: s.school.toLowerCase() === currentSchool.toLowerCase(),
        };
      })
      .slice(0, 12);

    // Add current school if not in top 12
    if (!topSchools.some((s) => s.isCurrent)) {
      topSchools.push({
        school: currentSchool,
        value: currentValue,
        multiplier: currentMultiplier,
        tier: "Current",
        difference: 0,
        percentChange: 0,
        isCurrent: true,
      });
    }

    return topSchools.sort((a, b) => b.value - a.value);
  }, [allSchools, baseValue, currentValue, currentSchool, currentMultiplier]);

  if (loading) {
    return (
      <Card className="glass">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  if (comparisonData.length === 0) return null;

  const bestOption = comparisonData[0];
  const potentialGain = bestOption.value - currentValue;

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: { school: string; value: number; tier: string; percentChange: number; isCurrent: boolean } }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="font-bold text-foreground">{data.school}</p>
          <p className="text-xs text-muted-foreground">{data.tier}</p>
          <p className="text-lg font-bold text-primary mt-1">
            {formatCurrency(data.value)}
          </p>
          {!data.isCurrent && (
            <p className={`text-sm ${data.percentChange >= 0 ? "text-green-500" : "text-red-500"}`}>
              {data.percentChange >= 0 ? "+" : ""}{data.percentChange.toFixed(1)}% vs current
            </p>
          )}
          {data.isCurrent && (
            <Badge variant="outline" className="mt-1 text-xs">Current School</Badge>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="glass">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <ArrowRightLeft className="h-5 w-5 text-primary" />
          Transfer Value Calculator
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Compare NIL value at different schools based on CFBD performance tiers
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current vs Best Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-card rounded-lg p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              Current School
            </p>
            <p className="font-bold text-foreground">{currentSchool}</p>
            <p className="text-xl font-bold text-primary">{formatCurrency(currentValue)}</p>
          </div>
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              Highest Potential
            </p>
            <p className="font-bold text-foreground">{bestOption.school}</p>
            <p className="text-xl font-bold text-green-500">{formatCurrency(bestOption.value)}</p>
            {potentialGain > 0 && (
              <Badge className="mt-1 bg-green-500/20 text-green-500 border-green-500/30">
                <TrendingUp className="h-3 w-3 mr-1" />
                +{formatCurrency(potentialGain)}
              </Badge>
            )}
          </div>
        </div>

        {/* School Comparison Chart */}
        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={comparisonData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" horizontal={false} />
              <XAxis
                type="number"
                tickFormatter={(value) => formatCurrency(value)}
                stroke="rgba(255,255,255,0.5)"
                fontSize={12}
              />
              <YAxis
                type="category"
                dataKey="school"
                stroke="rgba(255,255,255,0.5)"
                fontSize={11}
                width={75}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine
                x={currentValue}
                stroke="#888"
                strokeDasharray="5 5"
                label={{ value: "Current", fill: "#888", fontSize: 10, position: "top" }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {comparisonData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.isCurrent ? "#D4AF37" : entry.value > currentValue ? "#22c55e" : "#ef4444"}
                    fillOpacity={entry.isCurrent ? 1 : 0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-[#D4AF37]" />
            <span className="text-muted-foreground">Current School</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-green-500" />
            <span className="text-muted-foreground">Higher Value</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span className="text-muted-foreground">Lower Value</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default TransferValueChart;
