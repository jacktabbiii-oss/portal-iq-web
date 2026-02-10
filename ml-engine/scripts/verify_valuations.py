"""
Verify NIL Valuations - Check that Ball State and other mid-tier schools are reasonable.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

def verify_valuations():
    """Check valuations for sanity."""
    print("=" * 70)
    print("VERIFYING NIL VALUATIONS")
    print("=" * 70)
    print()

    # Load unified players
    unified_path = DATA_DIR / "unified_players.csv"
    portal_path = DATA_DIR / "portal_nil_valuations.csv"

    if not unified_path.exists() and not portal_path.exists():
        print("XX No valuation files found!")
        return False

    # Load whichever exists
    if unified_path.exists():
        df = pd.read_csv(unified_path)
        print(f"OK Loaded unified_players.csv: {len(df)} players")
    else:
        df = pd.read_csv(portal_path)
        print(f"OK Loaded portal_nil_valuations.csv: {len(df)} players")

    print()

    # Check Ball State specifically
    print("1. BALL STATE CHECK (MAC School - Should be reasonable)")
    print("-" * 70)
    ball_state = df[df["school"].str.contains("Ball", case=False, na=False)]
    if not ball_state.empty:
        for _, row in ball_state.head(10).iterrows():
            name = row.get("name", "Unknown")
            pos = row.get("position", "?")
            nil = row.get("nil_value", 0)
            tier = row.get("nil_tier", "?")

            # Check if reasonable
            status = "OK" if nil < 1_000_000 else "XX TOO HIGH"
            print(f"  {status} {name:30} {pos:4} ${nil:>12,.0f} ({tier})")
    else:
        print("  No Ball State players found")

    print()

    # Check MAC schools
    print("2. MAC SCHOOLS CHECK (Should be under $1M for most)")
    print("-" * 70)
    mac_schools = ["Ball State", "Toledo", "Ohio", "Kent State", "Bowling Green",
                   "Miami (OH)", "Buffalo", "Akron"]
    mac_players = df[df["school"].isin(mac_schools) & df["nil_value"].notna()]

    if not mac_players.empty:
        over_1m = len(mac_players[mac_players["nil_value"] >= 1_000_000])
        total = len(mac_players)
        print(f"  MAC players with NIL: {total}")
        print(f"  Over $1M: {over_1m} ({over_1m/total*100:.1f}%)")
        if over_1m > total * 0.05:  # More than 5% over $1M is suspicious
            print(f"  XX WARNING: {over_1m/total*100:.1f}% over $1M (should be <5%)")
        else:
            print(f"  OK Reasonable distribution")

        print(f"\n  Top 5 MAC players:")
        top_mac = mac_players.nlargest(5, "nil_value")
        for _, row in top_mac.iterrows():
            name = row.get("name", "Unknown")
            school = row.get("school", "?")
            pos = row.get("position", "?")
            nil = row.get("nil_value", 0)
            print(f"    ${nil:>10,.0f} - {name:25} ({pos}, {school})")
    else:
        print("  No MAC players found")

    print()

    # Check blue bloods
    print("3. BLUE BLOOD CHECK (Should have high valuations)")
    print("-" * 70)
    blue_bloods = ["Alabama", "Ohio State", "Georgia", "Texas"]
    bb_players = df[df["school"].isin(blue_bloods) & df["nil_value"].notna()]

    if not bb_players.empty:
        over_1m = len(bb_players[bb_players["nil_value"] >= 1_000_000])
        total = len(bb_players)
        print(f"  Blue blood players with NIL: {total}")
        print(f"  Over $1M: {over_1m} ({over_1m/total*100:.1f}%)")

        print(f"\n  Top 5 blue blood players:")
        top_bb = bb_players.nlargest(5, "nil_value")
        for _, row in top_bb.iterrows():
            name = row.get("name", "Unknown")
            school = row.get("school", "?")
            pos = row.get("position", "?")
            nil = row.get("nil_value", 0)
            tier = row.get("nil_tier", "?")
            print(f"    ${nil:>10,.0f} - {name:25} ({pos}, {school}, {tier})")
    else:
        print("  No blue blood players found")

    print()

    # Overall stats
    print("4. OVERALL DISTRIBUTION")
    print("-" * 70)
    fbs = df[df.get("division") == "FBS"] if "division" in df.columns else df
    fbs_nil = fbs[fbs["nil_value"].notna()]

    if not fbs_nil.empty:
        print(f"  Total FBS with NIL: {len(fbs_nil)}")
        print(f"  Mean:   ${fbs_nil['nil_value'].mean():>12,.0f}")
        print(f"  Median: ${fbs_nil['nil_value'].median():>12,.0f}")
        print(f"  Max:    ${fbs_nil['nil_value'].max():>12,.0f}")
        print()
        print("  Tier Distribution:")
        if "nil_tier" in fbs_nil.columns:
            for tier in ["mega", "premium", "solid", "moderate", "entry"]:
                count = len(fbs_nil[fbs_nil["nil_tier"] == tier])
                pct = count / len(fbs_nil) * 100
                print(f"    {tier:10} {count:6,} ({pct:5.1f}%)")

    print()
    print("=" * 70)
    print("OK VERIFICATION COMPLETE")
    print("=" * 70)

    # Check if Ball State is reasonable
    ball_state_reasonable = True
    if not ball_state.empty:
        max_ball_state = ball_state["nil_value"].max()
        if max_ball_state >= 2_000_000:
            print("\nXX ISSUE: Ball State player valued over $2M!")
            ball_state_reasonable = False

    if ball_state_reasonable:
        print("\nOK Ball State valuations look reasonable!")
        return True
    else:
        print("\nXX Ball State valuations still broken!")
        return False


if __name__ == "__main__":
    verify_valuations()
