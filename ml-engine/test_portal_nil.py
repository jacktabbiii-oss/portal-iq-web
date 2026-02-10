"""Test On3 Portal Data & NIL Changes Integration"""
import sys
sys.path.insert(0, 'src')

from models.school_tiers import get_school_tiers, refresh_tiers

# Refresh to load new data
refresh_tiers()
tiers = get_school_tiers()

print("=" * 90)
print("ON3 TEAM PORTAL RANKINGS & NIL VALUATION CHANGES")
print("=" * 90)

# Get teams with portal data
teams_with_portal = []
for school, info in tiers.items():
    if info.get('portal_rank'):
        teams_with_portal.append((school, info))

print(f"\nTotal teams with On3 portal data: {len(teams_with_portal)}")

if teams_with_portal:
    # Sort by portal rank
    teams_with_portal.sort(key=lambda x: x[1]['portal_rank'])

    print("\nTOP 20 PORTAL PERFORMERS (On3 Rankings):")
    print("-" * 90)
    print(f"{'Rank':<6} {'School':<25} {'Transfers':<15} {'NIL Change':<20} {'Star Net':<15}")
    print("-" * 90)

    for school, info in teams_with_portal[:20]:
        rank = info.get('portal_rank', 0)
        transfers_in = info.get('transfers_in', 0)
        transfers_out = info.get('transfers_out', 0)
        nil_change = info.get('nil_valuation_change', 0)
        five_net = info.get('five_stars_net', 0)
        four_net = info.get('four_stars_net', 0)
        three_net = info.get('three_stars_net', 0)

        transfers_str = f"+{transfers_in}/-{transfers_out}"
        nil_str = f"${nil_change/1000000:+.2f}M" if nil_change else "$0.00M"
        stars_str = f"5*:{five_net:+d} 4*:{four_net:+d}"

        print(f"#{rank:<5} {school:<25} {transfers_str:<15} {nil_str:<20} {stars_str:<15}")

    print("\n" + "=" * 90)
    print("BIGGEST NIL SPENDERS (Portal Cycle):")
    print("-" * 90)
    print(f"{'School':<30} {'NIL Spent':<20} {'Transfers In':<15} {'Avg Rating':<12}")
    print("-" * 90)

    # Sort by NIL valuation change
    teams_with_portal.sort(key=lambda x: x[1].get('nil_valuation_change', 0), reverse=True)

    for school, info in teams_with_portal[:15]:
        nil_change = info.get('nil_valuation_change', 0)
        transfers_in = info.get('transfers_in', 0)
        avg_rating = info.get('avg_rating_in', 0)

        nil_str = f"${nil_change/1000000:.2f}M" if nil_change else "$0.00M"

        print(f"{school:<30} {nil_str:<20} {transfers_in:<15} {avg_rating:<12.1f}")

else:
    print("\n[WARNING] No On3 portal data loaded!")
    print("Check if on3_team_portal_rankings.csv exists and team names match.")

print("\n[OK] On3 portal integration test complete!")
