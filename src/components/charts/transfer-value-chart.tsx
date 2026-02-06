"use client";

import { useMemo } from "react";
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
import { ArrowRightLeft, TrendingUp, TrendingDown } from "lucide-react";

interface TransferValueChartProps {
  currentSchool: string;
  currentValue: number;
  position: string;
}

// School multipliers based on brand value
const SCHOOL_MULTIPLIERS: Record<string, { multiplier: number; tier: string }> = {
  "Alabama": { multiplier: 2.5, tier: "Blue Blood" },
  "Ohio State": { multiplier: 2.5, tier: "Blue Blood" },
  "Georgia": { multiplier: 2.4, tier: "Blue Blood" },
  "Texas": { multiplier: 2.3, tier: "Blue Blood" },
  "USC": { multiplier: 2.2, tier: "Blue Blood" },
  "Michigan": { multiplier: 2.2, tier: "Blue Blood" },
  "Notre Dame": { multiplier: 2.1, tier: "Blue Blood" },
  "Oklahoma": { multiplier: 2.0, tier: "Blue Blood" },
  "LSU": { multiplier: 1.9, tier: "Elite" },
  "Florida": { multiplier: 1.8, tier: "Elite" },
  "Penn State": { multiplier: 1.8, tier: "Elite" },
  "Oregon": { multiplier: 1.8, tier: "Elite" },
  "Clemson": { multiplier: 1.7, tier: "Elite" },
  "Tennessee": { multiplier: 1.7, tier: "Elite" },
  "Texas A&M": { multiplier: 1.7, tier: "Elite" },
  "Miami": { multiplier: 1.5, tier: "Power" },
  "Florida State": { multiplier: 1.5, tier: "Power" },
  "Auburn": { multiplier: 1.4, tier: "Power" },
  "Wisconsin": { multiplier: 1.3, tier: "Power" },
  "Iowa": { multiplier: 1.2, tier: "Power" },
  "UCLA": { multiplier: 1.4, tier: "Power" },
};

function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

function getSchoolMultiplier(school: string): number {
  return SCHOOL_MULTIPLIERS[school]?.multiplier || 1.0;
}

export function TransferValueChart({
  currentSchool,
  currentValue,
  position,
}: TransferValueChartProps) {
  const currentMultiplier = getSchoolMultiplier(currentSchool);
  // Calculate base value (normalized)
  const baseValue = currentValue / currentMultiplier;

  // Generate comparison data for top schools
  const comparisonData = useMemo(() => {
    const schools = Object.entries(SCHOOL_MULTIPLIERS)
      .sort((a, b) => b[1].multiplier - a[1].multiplier)
      .slice(0, 12)
      .map(([school, { multiplier, tier }]) => {
        const projectedValue = baseValue * multiplier;
        const difference = projectedValue - currentValue;
        const percentChange = ((projectedValue - currentValue) / currentValue) * 100;

        return {
          school,
          value: projectedValue,
          multiplier,
          tier,
          difference,
          percentChange,
          isCurrent: school === currentSchool,
        };
      });

    // Add current school if not in top 12
    if (!schools.some((s) => s.school === currentSchool)) {
      schools.push({
        school: currentSchool,
        value: currentValue,
        multiplier: currentMultiplier,
        tier: "Current",
        difference: 0,
        percentChange: 0,
        isCurrent: true,
      });
    }

    return schools.sort((a, b) => b.value - a.value);
  }, [baseValue, currentValue, currentSchool, currentMultiplier]);

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
          Compare NIL value at different schools based on market size and brand
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
