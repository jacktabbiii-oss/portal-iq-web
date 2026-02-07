"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface RadarDataPoint {
  stat: string;
  fullMark: number;
  [key: string]: string | number;
}

interface PlayerRadarChartProps {
  player1Name: string;
  player2Name: string;
  player1Stats: {
    overall?: number | null;
    offense?: number | null;
    defense?: number | null;
    pass_block?: number | null;
    run_block?: number | null;
    pass_rush?: number | null;
    run_defense?: number | null;
    coverage?: number | null;
  };
  player2Stats: {
    overall?: number | null;
    offense?: number | null;
    defense?: number | null;
    pass_block?: number | null;
    run_block?: number | null;
    pass_rush?: number | null;
    run_defense?: number | null;
    coverage?: number | null;
  };
}

export function PlayerRadarChart({
  player1Name,
  player2Name,
  player1Stats,
  player2Stats,
}: PlayerRadarChartProps) {
  // Build radar data from available stats
  const radarData: RadarDataPoint[] = [];

  const addStat = (label: string, key: keyof typeof player1Stats) => {
    const val1 = player1Stats[key];
    const val2 = player2Stats[key];
    if (val1 != null || val2 != null) {
      radarData.push({
        stat: label,
        player1: val1 ?? 0,
        player2: val2 ?? 0,
        fullMark: 100,
      });
    }
  };

  // Add stats in order of importance
  addStat("Overall", "overall");
  addStat("Offense", "offense");
  addStat("Defense", "defense");
  addStat("Pass Block", "pass_block");
  addStat("Run Block", "run_block");
  addStat("Pass Rush", "pass_rush");
  addStat("Run Defense", "run_defense");
  addStat("Coverage", "coverage");

  // Need at least 3 stats for a meaningful radar chart
  if (radarData.length < 3) {
    return (
      <div className="h-64 flex items-center justify-center text-muted-foreground">
        Not enough performance data available for radar visualization
      </div>
    );
  }

  // Truncate names for legend
  const truncateName = (name: string, maxLen: number = 15) => {
    if (name.length <= maxLen) return name;
    return name.substring(0, maxLen - 1) + "…";
  };

  return (
    <ResponsiveContainer width="100%" height={350}>
      <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
        <PolarGrid
          stroke="#2A3A54"
          strokeOpacity={0.6}
        />
        <PolarAngleAxis
          dataKey="stat"
          tick={{ fill: "#9CA3AF", fontSize: 11 }}
          tickLine={false}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "#6B7A8F", fontSize: 10 }}
          axisLine={false}
          tickCount={5}
        />
        <Radar
          name={truncateName(player1Name)}
          dataKey="player1"
          stroke="#D4AF37"
          fill="#D4AF37"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Radar
          name={truncateName(player2Name)}
          dataKey="player2"
          stroke="#3B82F6"
          fill="#3B82F6"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Legend
          wrapperStyle={{
            paddingTop: "16px",
            fontSize: "12px",
          }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1a2744",
            border: "1px solid #2A3A54",
            borderRadius: "8px",
            color: "#fff",
            fontSize: "12px",
          }}
          formatter={(value) => typeof value === 'number' ? value.toFixed(1) : String(value ?? '')}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// Compact version for smaller spaces
export function PlayerRadarChartCompact({
  player1Name,
  player2Name,
  player1Stats,
  player2Stats,
}: PlayerRadarChartProps) {
  const radarData: RadarDataPoint[] = [];

  const addStat = (label: string, key: keyof typeof player1Stats) => {
    const val1 = player1Stats[key];
    const val2 = player2Stats[key];
    if (val1 != null || val2 != null) {
      radarData.push({
        stat: label,
        player1: val1 ?? 0,
        player2: val2 ?? 0,
        fullMark: 100,
      });
    }
  };

  addStat("OVR", "overall");
  addStat("OFF", "offense");
  addStat("DEF", "defense");
  addStat("PBK", "pass_block");
  addStat("RBK", "run_block");
  addStat("PRU", "pass_rush");
  addStat("RDF", "run_defense");
  addStat("COV", "coverage");

  if (radarData.length < 3) {
    return (
      <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
        Insufficient data
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
        <PolarGrid stroke="#2A3A54" strokeOpacity={0.5} />
        <PolarAngleAxis
          dataKey="stat"
          tick={{ fill: "#9CA3AF", fontSize: 9 }}
          tickLine={false}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={false}
          axisLine={false}
        />
        <Radar
          name={player1Name.split(" ")[1] || player1Name}
          dataKey="player1"
          stroke="#D4AF37"
          fill="#D4AF37"
          fillOpacity={0.25}
          strokeWidth={1.5}
        />
        <Radar
          name={player2Name.split(" ")[1] || player2Name}
          dataKey="player2"
          stroke="#3B82F6"
          fill="#3B82F6"
          fillOpacity={0.25}
          strokeWidth={1.5}
        />
        <Legend
          wrapperStyle={{ fontSize: "10px", paddingTop: "8px" }}
          iconSize={8}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
