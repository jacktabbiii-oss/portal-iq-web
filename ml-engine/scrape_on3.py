"""Quick script to scrape On3 NIL data."""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to path for direct imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "data_collection" / "college"))

# Import the scraper module directly
import on3_scraper
On3Scraper = on3_scraper.On3Scraper

async def main():
    print("On3 NIL Data Scraper")
    print("=" * 50)

    # Check for credentials
    email = os.getenv("ON3_EMAIL")
    password = os.getenv("ON3_PASSWORD")

    # Check for --interactive flag
    interactive_mode = "--interactive" in sys.argv or "-i" in sys.argv

    if email and password:
        print(f"\nCredentials found for: {email}")
    elif interactive_mode:
        print("\nInteractive login mode - browser will open for Google login")
    else:
        print("\nNo credentials found. Options:")
        print("  1. Add ON3_EMAIL and ON3_PASSWORD to .env")
        print("  2. Run with --interactive flag for Google login")
        print("\nContinuing without login (limited data)...\n")

    # Use headless=False for interactive login so user can see the browser
    use_headless = not interactive_mode

    async with On3Scraper(headless=use_headless) as scraper:
        # Try to login
        if email and password:
            print("\n[1/3] Logging in to On3...")
            login_success = await scraper.login(email, password)
            if login_success:
                print("Login successful! Full NIL data will be available.")
            else:
                print("Login failed. Continuing without login...")
        elif interactive_mode:
            print("\n[1/3] Opening browser for Google login...")
            login_success = await scraper.login_interactive(timeout=120)
            if login_success:
                print("Login successful! Full NIL data will be available.")
            else:
                print("Login timed out. Continuing without login...")
        else:
            # Check if we have saved cookies from a previous session
            if scraper.cookies_path.exists():
                print("\n[1/3] Found saved session, checking if still valid...")
                if await scraper._check_logged_in():
                    scraper.is_logged_in = True
                    print("Previous session still valid!")
                else:
                    print("Saved session expired. Run with --interactive to login again.")
            else:
                print("\n[1/3] Skipping login (no credentials)")

        # Scrape NIL 100 rankings
        print("\n[2/3] Scraping NIL 100 rankings...")
        players = await scraper.scrape_nil_100(pages=1)

        if players:
            print(f"\nFound {len(players)} players!")
            print("\nTop 10 by NIL valuation:")
            sorted_players = sorted(players, key=lambda p: p.nil_valuation or 0, reverse=True)[:10]
            for i, p in enumerate(sorted_players, 1):
                val = f"${p.nil_valuation:,.0f}" if p.nil_valuation else "N/A"
                print(f"  {i:2}. {p.name:25} | {p.school:15} | {p.position:5} | {val}")
        else:
            print("\nNo players found from DOM extraction.")
            print("This may be due to On3's JavaScript rendering or anti-bot measures.")

        # Build merged dataset
        print("\n[3/3] Building merged dataset with performance stats...")
        merged = await scraper.build_nil_performance_dataset()

        if not merged.empty:
            print(f"\nMerged dataset: {len(merged)} rows, {len(merged.columns)} columns")
            print(f"Saved to: data/processed/nil_performance_merged.csv")

        print("\n" + "=" * 50)
        print("Done!")

        if not scraper.is_logged_in:
            print("\nNOTE: Run with ON3_EMAIL and ON3_PASSWORD in .env for full NIL values.")

if __name__ == "__main__":
    asyncio.run(main())
