"use client";

import { useState, useCallback } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Users } from "lucide-react";

interface SocialGrowthSimulatorProps {
  currentNILValue: number;
  currentFollowers: number;
  playerName?: string;
}

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

function formatFollowers(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(0)}K`;
  }
  return value.toLocaleString();
}

export function SocialGrowthSimulator({
  currentNILValue,
  currentFollowers,
  playerName = "Player",
}: SocialGrowthSimulatorProps) {
  const [followerGrowth, setFollowerGrowth] = useState(100000);

  // Generate data points for the growth chart
  const generateGrowthData = useCallback(() => {
    const steps = 20;
    const data = [];

    for (let i = 0; i <= steps; i++) {
      const additionalFollowers = (followerGrowth * i) / steps;
      // Logarithmic growth curve - social media has diminishing returns
      const growthMultiplier = 1 + (Math.log1p(additionalFollowers / 10000) * 0.15);
      const projectedValue = currentNILValue * growthMultiplier;

      data.push({
        followers: currentFollowers + additionalFollowers,
        newFollowers: additionalFollowers,
        value: projectedValue,
        growth: projectedValue - currentNILValue,
      });
    }

    return data;
  }, [currentNILValue, currentFollowers, followerGrowth]);

  const data = generateGrowthData();
  const projectedValue = data[data.length - 1]?.value || currentNILValue;
  const valueIncrease = projectedValue - currentNILValue;
  const percentIncrease = ((projectedValue - currentNILValue) / currentNILValue) * 100;

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: { newFollowers: number; value: number; growth: number } }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm text-muted-foreground">
            +{formatFollowers(data.newFollowers)} followers
          </p>
          <p className="text-lg font-bold text-primary">
            {formatCurrency(data.value)}
          </p>
          <p className="text-sm text-green-500">
            +{formatCurrency(data.growth)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="glass">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Users className="h-5 w-5 text-primary" />
          Social Media Growth Simulator
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          See how growing your social following impacts NIL value
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-card rounded-lg p-4 text-center">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              Current Followers
            </p>
            <p className="text-2xl font-bold">{formatFollowers(currentFollowers)}</p>
          </div>
          <div className="bg-card rounded-lg p-4 text-center">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              Current NIL Value
            </p>
            <p className="text-2xl font-bold text-primary">{formatCurrency(currentNILValue)}</p>
          </div>
        </div>

        {/* Growth Slider */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Simulated Follower Growth</span>
            <Badge variant="outline" className="font-mono">
              +{formatFollowers(followerGrowth)}
            </Badge>
          </div>
          <Slider
            value={[followerGrowth]}
            onValueChange={(value) => setFollowerGrowth(value[0])}
            max={1000000}
            min={0}
            step={10000}
            className="py-4"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0</span>
            <span>250K</span>
            <span>500K</span>
            <span>750K</span>
            <span>1M</span>
          </div>
        </div>

        {/* Projected Value */}
        <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Projected NIL Value</p>
              <p className="text-3xl font-bold text-primary">{formatCurrency(projectedValue)}</p>
            </div>
            <div className="text-right">
              <Badge className="bg-green-500/20 text-green-500 border-green-500/30">
                <TrendingUp className="h-3 w-3 mr-1" />
                +{percentIncrease.toFixed(1)}%
              </Badge>
              <p className="text-sm text-green-500 mt-1">+{formatCurrency(valueIncrease)}</p>
            </div>
          </div>
        </div>

        {/* Interactive Growth Chart */}
        <div className="h-[300px] mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#D4AF37" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#D4AF37" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="newFollowers"
                tickFormatter={(value) => formatFollowers(value)}
                stroke="rgba(255,255,255,0.5)"
                fontSize={12}
              />
              <YAxis
                tickFormatter={(value) => formatCurrency(value)}
                stroke="rgba(255,255,255,0.5)"
                fontSize={12}
                width={80}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine
                y={currentNILValue}
                stroke="#666"
                strokeDasharray="5 5"
                label={{ value: "Current", fill: "#666", fontSize: 10 }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#D4AF37"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorValue)"
              />
              {/* Brush for zoom/pan */}
              <Brush
                dataKey="newFollowers"
                height={30}
                stroke="#D4AF37"
                fill="rgba(15, 26, 46, 0.8)"
                tickFormatter={(value) => formatFollowers(value)}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <p className="text-xs text-muted-foreground text-center">
          Drag the brush below the chart to zoom in on specific ranges
        </p>
      </CardContent>
    </Card>
  );
}

export default SocialGrowthSimulator;
