"""
Test Portal IQ Proprietary Power Rankings
Combines: On-field + Roster Quality + Portal Performance + NIL
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Add parent directory to find ml-engine module
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

from models.school_tiers import get_school_tiers

# For unified cache, we'll use data_loader approach instead
import pandas as pd

print("=" * 100)
print("PORTAL IQ PROPRIETARY POWER RANKINGS")
print("Algorithm: On-field (30%) + Roster (25%) + Portal (25%) + NIL (20%)")
print("=" * 100)

tiers = get_school_tiers()

# Load unified players data
try:
    unified_df = pd.read_csv('data/processed/unified_players.csv')
    print(f"Loaded {len(unified_df)} players from unified cache")
except:
    unified_df = pd.read_csv('data/processed/portal_nil_valuations.csv')
    print(f"Loaded {len(unified_df)} players from legacy cache")

# Calculate power scores for all teams
rankings = []

for school, tier_info in list(tiers.items())[:50]:  # Test top 50
    # Get roster data
    roster_df = unified_df[unified_df['school'].str.lower() == school.lower()] if 'school' in unified_df.columns else pd.DataFrame()

    # Calculate roster metrics
    if not roster_df.empty:
        # PFF average
        if "pff_overall" in roster_df.columns:
            pff_grades = roster_df["pff_overall"].dropna()
            avg_pff = float(pff_grades.mean()) if not pff_grades.empty else 0
        else:
            avg_pff = 0

        # Roster talent (NIL-based)
        if "nil_value" in roster_df.columns:
            nil_values = roster_df["nil_value"].dropna()
            if not nil_values.empty:
                avg_nil = float(nil_values.mean())
                top_10_nil = float(nil_values.nlargest(10).mean())
                roster_talent = (avg_nil * 0.6 + top_10_nil * 0.4) / 100
            else:
                roster_talent = 0
        else:
            roster_talent = 0
    else:
        avg_pff, roster_talent = 0, 0

    # Calculate power score
    power_score = 0

    # On-field (30%)
    sp_plus = tier_info.get("sp_plus_overall", 0)
    wins = tier_info.get("wins", 0)
    if sp_plus > -15:
        power_score += ((sp_plus + 15) / 45) * 18
    power_score += (wins / 15) * 12

    # Roster quality (25%)
    if avg_pff > 0:
        power_score += (avg_pff / 90) * 15
    if roster_talent > 0:
        power_score += (roster_talent / 1000) * 10

    # Portal performance (25%)
    portal_rank = tier_info.get("portal_rank")
    if portal_rank:
        portal_score = max(0, (51 - portal_rank) / 51 * 15)
        power_score += portal_score

    avg_in = tier_info.get("avg_rating_in")
    avg_out = tier_info.get("avg_rating_out")
    if avg_in and avg_out:
        rating_diff = avg_in - avg_out
        power_score += min(5, max(0, (rating_diff / 10) * 5))

    stars = (tier_info.get("five_stars_net", 0) * 3 +
             tier_info.get("four_stars_net", 0) * 1.5 +
             tier_info.get("three_stars_net", 0) * 0.5)
    power_score += min(5, max(0, stars / 2))

    # NIL/recruiting (20%)
    power_score += (tier_info.get("multiplier", 1.0) / 3.0) * 10

    nil_change = tier_info.get("nil_valuation_change")
    if nil_change and nil_change > 0:
        nil_score = min(10, (nil_change / 5000000) * 10)
        power_score += nil_score

    rankings.append({
        "school": school,
        "power_score": round(power_score, 1),
        "wins": wins,
        "sp_plus": sp_plus,
        "pff_avg": round(avg_pff, 1),
        "roster_talent": round(roster_talent, 1),
        "portal_rank": portal_rank,
        "nil_change": nil_change,
        "tier": tier_info.get("tier")
    })

# Sort by power score
rankings.sort(key=lambda x: x["power_score"], reverse=True)

print("\nTOP 25 TEAMS - PORTAL IQ POWER RANKINGS:")
print("-" * 100)
print(f"{'Rank':<6} {'School':<25} {'Power':<8} {'W-L':<6} {'SP+':<7} {'PFF':<6} {'Talent':<8} {'Portal':<8}")
print("-" * 100)

for i, team in enumerate(rankings[:25], 1):
    school = team["school"]
    power = team["power_score"]
    wins = team["wins"]
    sp = team["sp_plus"]
    pff = team["pff_avg"]
    talent = team["roster_talent"]
    portal = f"#{team['portal_rank']}" if team["portal_rank"] else "N/A"

    print(f"{i:<6} {school:<25} {power:<8} {wins:<6} {sp:<7.1f} {pff:<6} {talent:<8} {portal:<8}")

print("\n" + "=" * 100)
print("ALGORITHM BREAKDOWN:")
print("  On-field performance: SP+ (18%) + Wins (12%) = 30%")
print("  Roster quality: PFF grades (15%) + NIL talent (10%) = 25%")
print("  Portal performance: On3 rank (15%) + Transfer quality (5%) + Stars (5%) = 25%")
print("  NIL/recruiting: School tier (10%) + Portal spending (10%) = 20%")
print("=" * 100)
