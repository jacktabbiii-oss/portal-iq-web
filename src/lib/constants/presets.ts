/**
 * Position-specific height and weight presets for filtering.
 * Heights are in inches, weights are in pounds.
 */

export interface MeasurablePreset {
  min: number;
  max?: number;
  ideal_min?: number;
  tall?: number;
  label: string;
}

export const HEIGHT_PRESETS: Record<string, MeasurablePreset> = {
  QB: { min: 72, ideal_min: 74, label: "6'0\"+ (ideal 6'2\"+)" },
  WR: { min: 69, tall: 75, label: "5'9\"+ (tall: 6'3\"+)" },
  RB: { min: 66, max: 74, label: "5'6\" - 6'2\"" },
  TE: { min: 75, ideal_min: 77, label: "6'3\"+ (ideal 6'5\"+)" },
  OT: { min: 76, ideal_min: 78, label: "6'4\"+ (ideal 6'6\"+)" },
  OG: { min: 74, ideal_min: 76, label: "6'2\"+ (ideal 6'4\"+)" },
  C: { min: 73, ideal_min: 75, label: "6'1\"+ (ideal 6'3\"+)" },
  IOL: { min: 73, ideal_min: 75, label: "6'1\"+ (ideal 6'3\"+)" },
  EDGE: { min: 74, ideal_min: 76, label: "6'2\"+ (ideal 6'4\"+)" },
  DT: { min: 74, ideal_min: 76, label: "6'2\"+ (ideal 6'4\"+)" },
  DL: { min: 74, ideal_min: 76, label: "6'2\"+ (ideal 6'4\"+)" },
  LB: { min: 72, ideal_min: 74, label: "6'0\"+ (ideal 6'2\"+)" },
  CB: { min: 69, max: 75, label: "5'9\" - 6'3\"" },
  S: { min: 70, ideal_min: 73, label: "5'10\"+ (ideal 6'1\"+)" },
  K: { min: 66, max: 76, label: "5'6\" - 6'4\"" },
  P: { min: 70, max: 78, label: "5'10\" - 6'6\"" },
  ATH: { min: 66, max: 78, label: "Varies" },
};

export const WEIGHT_PRESETS: Record<string, MeasurablePreset> = {
  QB: { min: 200, ideal_min: 215, label: "200+ lbs (ideal 215+)" },
  WR: { min: 170, max: 220, label: "170-220 lbs" },
  RB: { min: 190, max: 230, label: "190-230 lbs" },
  TE: { min: 240, ideal_min: 250, label: "240+ lbs (ideal 250+)" },
  OT: { min: 300, ideal_min: 315, label: "300+ lbs (ideal 315+)" },
  OG: { min: 300, ideal_min: 315, label: "300+ lbs (ideal 315+)" },
  C: { min: 290, ideal_min: 305, label: "290+ lbs (ideal 305+)" },
  IOL: { min: 290, ideal_min: 305, label: "290+ lbs (ideal 305+)" },
  EDGE: { min: 240, ideal_min: 260, label: "240+ lbs (ideal 260+)" },
  DT: { min: 280, ideal_min: 300, label: "280+ lbs (ideal 300+)" },
  DL: { min: 280, ideal_min: 300, label: "280+ lbs (ideal 300+)" },
  LB: { min: 220, ideal_min: 235, label: "220+ lbs (ideal 235+)" },
  CB: { min: 175, max: 210, label: "175-210 lbs" },
  S: { min: 190, ideal_min: 205, label: "190+ lbs (ideal 205+)" },
  K: { min: 160, max: 220, label: "160-220 lbs" },
  P: { min: 180, max: 240, label: "180-240 lbs" },
  ATH: { min: 170, max: 280, label: "Varies" },
};

/**
 * Get height preset for a position
 */
export function getHeightPreset(position: string): MeasurablePreset | null {
  return HEIGHT_PRESETS[position.toUpperCase()] || null;
}

/**
 * Get weight preset for a position
 */
export function getWeightPreset(position: string): MeasurablePreset | null {
  return WEIGHT_PRESETS[position.toUpperCase()] || null;
}

/**
 * Check if a player meets the minimum height for their position
 */
export function meetsHeightMinimum(
  position: string,
  heightInches: number
): boolean {
  const preset = getHeightPreset(position);
  if (!preset) return true;
  return heightInches >= preset.min;
}

/**
 * Check if a player meets the ideal height for their position
 */
export function meetsIdealHeight(
  position: string,
  heightInches: number
): boolean {
  const preset = getHeightPreset(position);
  if (!preset || !preset.ideal_min) return true;
  return heightInches >= preset.ideal_min;
}

/**
 * Check if a player meets the minimum weight for their position
 */
export function meetsWeightMinimum(
  position: string,
  weightLbs: number
): boolean {
  const preset = getWeightPreset(position);
  if (!preset) return true;
  return weightLbs >= preset.min;
}

/**
 * Check if a player meets the ideal weight for their position
 */
export function meetsIdealWeight(
  position: string,
  weightLbs: number
): boolean {
  const preset = getWeightPreset(position);
  if (!preset || !preset.ideal_min) return true;
  return weightLbs >= preset.ideal_min;
}

/**
 * Format height in inches to display string
 */
export function formatHeight(inches: number | null | undefined): string {
  if (!inches) return "-";
  const feet = Math.floor(inches / 12);
  const remainingInches = Math.round(inches % 12);
  return `${feet}'${remainingInches}"`;
}

/**
 * Parse height string (e.g., "6'4\"") to inches
 */
export function parseHeight(heightStr: string): number | null {
  if (!heightStr) return null;
  const match = heightStr.match(/(\d+)'(\d+)/);
  if (match) {
    const feet = parseInt(match[1], 10);
    const inches = parseInt(match[2], 10);
    return feet * 12 + inches;
  }
  return null;
}

/**
 * List of all positions
 */
export const POSITIONS = [
  "QB",
  "RB",
  "WR",
  "TE",
  "OT",
  "OG",
  "C",
  "IOL",
  "EDGE",
  "DT",
  "DL",
  "LB",
  "CB",
  "S",
  "K",
  "P",
  "ATH",
];

/**
 * List of conferences
 */
export const CONFERENCES = [
  "SEC",
  "Big Ten",
  "Big 12",
  "ACC",
  "Pac-12",
  "Mountain West",
  "AAC",
  "Sun Belt",
  "MAC",
  "C-USA",
];

/**
 * NIL tiers with labels and colors
 */
export const NIL_TIERS = {
  mega: { label: "Mega", color: "text-purple-500", min: 1000000 },
  premium: { label: "Premium", color: "text-primary", min: 500000 },
  established: { label: "Established", color: "text-green-500", min: 200000 },
  emerging: { label: "Emerging", color: "text-blue-500", min: 50000 },
  developing: { label: "Developing", color: "text-muted-foreground", min: 0 },
};

/**
 * Get NIL tier from value
 */
export function getNILTier(
  value: number
): keyof typeof NIL_TIERS {
  if (value >= 1000000) return "mega";
  if (value >= 500000) return "premium";
  if (value >= 200000) return "established";
  if (value >= 50000) return "emerging";
  return "developing";
}
