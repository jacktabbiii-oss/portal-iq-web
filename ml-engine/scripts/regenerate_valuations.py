"""
Quick script to regenerate NIL valuations with the correct (simple) algorithm.

Run: python scripts/regenerate_valuations.py
"""

import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    print("=" * 70)
    print("REGENERATING NIL VALUATIONS WITH CORRECT ALGORITHM")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Use the transparent CustomNILValuator (not the ML black box)")
    print("  2. Properly apply school multipliers (Ball State MAC = 0.6x)")
    print("  3. Generate realistic valuations for all players")
    print()
    print("=" * 70)
    print()

    # Import and run the main generation script
    from generate_all_valuations import main
    main()
