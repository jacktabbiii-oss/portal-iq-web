# Portal IQ — Data Sources & Aggregation Addendum

## Use this alongside the main build guide. These prompts REPLACE Prompts 2-6 in the original guide.

---

## Your Data Stack

### Tier 1: Free API/Package Sources (Use Now)
| Source | Package | What You Get |
|--------|---------|-------------|
| sportsdataverse-py | `pip install sportsdataverse` | Play-by-play with EPA/WPA, box scores, schedules, team data — the MAIN source for advanced CFB analytics |
| cfbd (CollegeFootballData API) | `pip install cfbd` | Player stats, team records, game results, drives, ratings, SP+, betting lines, coaches |
| recruitR-py | `pip install recruitR` | Recruiting rankings, player ratings, stars, team class rankings — football AND basketball |
| sportypy | `pip install sportypy` | Draw regulation football fields for depth chart visualizations, roster displays, formation plots |
| nfl_data_py | `pip install nfl_data_py` | NFL draft history, combine data, rookie stats (for draft projection model) |

### Tier 2: Scraping Bridge (Use Until You Get Partnerships)
| Source | What You Scrape | Priority |
|--------|----------------|----------|
| On3.com NIL 100 | NIL valuations, rankings | CRITICAL — this is your NIL training data |
| 247Sports | Transfer portal entries, composite recruiting rankings, team talent composites | HIGH |
| ESPN | FPI ratings, team efficiency stats, recruiting rankings | HIGH |
| Rivals | Recruiting rankings (cross-reference with 247) | MEDIUM |
| Pro Football Focus (free tier) | Any available college grades/rankings | MEDIUM |
| Spotrac | College football NIL tracker data | HIGH |
| Over The Cap | NFL rookie wage scale (for draft value model) | LOW |
| Social media profiles | Instagram/TikTok/Twitter follower counts for top players | HIGH |

### Tier 3: Future Partnerships (Pitch After MVP)
| Partner | What They Have | Why You Need It |
|---------|---------------|-----------------|
| PFF | Player grades, snap counts, advanced metrics for every player | Game-changer for model accuracy — the single biggest upgrade |
| On3 | Structured NIL deal data, valuations, collective info | Makes NIL model go from good to great |
| 247Sports | Structured portal data, composite rankings API | Cleaner than scraping |
| ESPN/Stats LLC | Play-by-play detail, advanced box scores | Supplements sportsdataverse |
| Hudl/Catapult | Player tracking data (GPS, speed, acceleration) | The college equivalent of NFL Next Gen Stats — this is the holy grail |

---

## Updated Prompts — Data Collection Layer

### Prompt 2 (REPLACES original) — Master Data Collector with sportsdataverse-py
```
Write src/data_collection/cfb_stats.py with a class CFBStatsCollector.

This class is the MAIN data collection engine. It uses TWO packages:
1. sportsdataverse (pip install sportsdataverse) — for play-by-play data with EPA/WPA metrics, box scores, schedules
2. cfbd (pip install cfbd) — for player season stats, team records, game results, ratings, SP+, coaches

The class should have these methods:

collect_play_by_play(start_year, end_year):
- Use sportsdataverse.cfb.CFBPlayProcess or sportsdataverse.cfb functions to load play-by-play data
- The sportsdataverse-py package provides access to the cfbfastR team's data including:
  - Expected Points Added (EPA) per play
  - Win Probability Added (WPA) per play  
  - Success rate
  - Explosiveness
  - Play type, down, distance, field position
- For each season, load the full PBP dataset
- Aggregate to player-level EPA metrics:
  - Offensive EPA/play by player (for QBs, RBs, WRs)
  - Total EPA contributed per season per player
  - EPA per dropback (QBs), EPA per rush (RBs), EPA per target (WRs)
  - Success rate on plays involving each player
- This is the MOST IMPORTANT data source because EPA is the gold standard for measuring player value
- Save raw PBP to data/cache/ (these files are large, ~50-200MB per season)
- Save player-aggregated EPA metrics to data/raw/player_epa_metrics.csv

collect_player_season_stats(start_year, end_year):
- Use cfbd API to pull traditional season stats: passing, rushing, receiving, defensive
- Include: player name, team, conference, season, games played, all counting stats
- Also pull player info: position, height, weight, year, hometown
- Save to data/raw/player_season_stats.csv

collect_team_data(start_year, end_year):
- Use cfbd for: team records (wins/losses), conference standings
- Use cfbd for: SP+ ratings, SRS, talent composite rankings
- Use sportsdataverse/ESPN for: FPI ratings if available through the package
- Use cfbd for: team recruiting class rankings per year
- Use cfbd for: coaching history (coach name, years at school, career record)
- Save to data/raw/team_data.csv

collect_game_data(start_year, end_year):
- Use cfbd for: game-by-game results with scores, home/away, conference game flag, week
- Use cfbd for: team game stats (total yards, turnovers, etc. per game)
- Use sportsdataverse for: pregame and postgame win probabilities per game
- Save to data/raw/game_results.csv

collect_advanced_metrics(start_year, end_year):
- Use cfbd's metrics endpoints for: PPA (predicted points added) per team
- Use cfbd's ratings endpoints for: SP+, SRS, Elo ratings
- Use sportsdataverse for: EPA-based team efficiency rankings (offense, defense, special teams)
- Calculate team-level metrics: offensive EPA/play, defensive EPA/play, turnover margin, explosiveness
- Save to data/raw/team_advanced_metrics.csv

collect_all(start_year=2020, end_year=2025):
- Runs everything above
- Implements caching: check data/cache/ for files with today's date before re-downloading
- Rate limits cfbd calls (0.5s between requests)
- Prints summary of all data collected
- Returns dict of all dataframes

IMPORTANT NOTES FOR IMPLEMENTATION:
- sportsdataverse-py documentation is at https://py.sportsdataverse.org/
- The main module path is: from sportsdataverse.cfb import *
- Key functions include loading PBP data that already has EPA/WPA calculated
- If sportsdataverse functions fail or have changed, fall back to cfbd for basic stats and print a warning
- cfbd API key should be loaded from .env: CFBD_API_KEY
- Add try/except around every API call with informative error messages
- Log everything with Python logging module
- Make it runnable standalone with __main__
```

### Prompt 3 (REPLACES original) — Recruiting Data with recruitR-py
```
Write src/data_collection/cfb_recruiting.py with a class CFBRecruitingCollector.

This class uses TWO packages:
1. recruitR (pip install recruitR) — the sportsdataverse recruiting package for football and basketball
2. cfbd — as a backup/supplement for recruiting data

Methods:

collect_player_rankings(start_year, end_year):
- Use recruitR to pull individual player recruiting rankings for football
- The recruitR package should have functions like:
  - recruitR.get_recruits() or similar for player-level recruiting data
  - recruitR.get_team_rankings() for team class rankings
- If recruitR doesn't have a specific function, fall back to cfbd's recruiting endpoints:
  - cfbd_recruiting_players() for individual recruits
  - cfbd_recruiting_teams() for team rankings
- Collect: player name, position, school committed to, state, city, stars (1-5), 
  rating (0.0-1.0), composite ranking, national rank, position rank, state rank
- Pull for years 2018-2025 (going back further for development tracking)
- Save to data/raw/recruiting_player_rankings.csv

collect_team_class_rankings(start_year, end_year):
- Use recruitR or cfbd for team-level recruiting class data
- Collect: school, year, national rank, total commits, average star rating, 
  total points/composite score, number of 5-stars, 4-stars, 3-stars
- Save to data/raw/recruiting_team_rankings.csv

collect_transfer_recruiting(start_year, end_year):
- If recruitR has transfer portal recruiting data, pull it
- Otherwise, this will come from our scraping module (Prompt 4)
- At minimum, create the data structure for it

build_recruit_to_player_mapping():
- This is CRITICAL — connecting a recruit to their college player record
- Take recruiting data (name + school + position + year)
- Match to our player stats data from cfb_stats.py
- Use fuzzy matching with these strategies:
  a. Exact match on name + school
  b. Fuzzy name match (difflib.SequenceMatcher, threshold 0.85) + exact school
  c. Fuzzy name match + conference match + position match (for transfers who changed schools)
- Store mapping in data/processed/recruit_player_mapping.csv
- Report matching rate (target: >80% of recruits who played college ball should match)
- Log unmatched recruits for manual review

build_recruiting_roi_dataset():
- For matched recruits, combine: recruiting info + college stats
- Calculate "production over expectation":
  - Average stats by star rating and position
  - Each player's deviation from that average
  - A 3-star producing like a 5-star average = high ROE
- Calculate "development score": how much did production improve from year 1 to peak year
- Save to data/processed/recruiting_roi_dataset.csv

IMPLEMENTATION NOTES:
- recruitR-py repo is at https://github.com/sportsdataverse/recruitR-py/
- Check the actual function signatures — the package may use different naming conventions
- If recruitR is outdated or broken, fall back entirely to cfbd recruiting endpoints
- Always try recruitR first, then cfbd, then log what failed
- Same caching/logging/error handling patterns as cfb_stats.py
```

### Prompt 4 (REPLACES original) — Transfer Portal + Scraping Bridge
```
Write src/data_collection/cfb_portal.py with a class CFBPortalCollector.

This handles transfer portal data through a combination of API sources and web scraping.

Methods:

collect_portal_from_api(start_year, end_year):
- Try cfbd's transfer portal endpoint first (if it exists)
- Try sportsdataverse if it has portal data
- Collect whatever is available: player name, origin school, destination school, position, year, status
- Save to data/raw/portal_api_data.csv

scrape_247_portal():
- Scrape 247Sports transfer portal page
- URL pattern: https://247sports.com/season/{year}-college-football-transfer-portal/
- Use BeautifulSoup with proper headers:
  headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml",
      "Accept-Language": "en-US,en;q=0.9",
  }
- Extract: player name, original school, new school, position, star rating, status (committed/uncommitted/withdrawn)
- Handle pagination if the list spans multiple pages
- Rate limit: 2 seconds between requests
- If JavaScript rendering blocks scraping, print clear instructions:
  "247Sports requires JavaScript rendering. Install playwright: pip install playwright && playwright install chromium"
  Then provide a playwright-based fallback scraper
- Save to data/raw/portal_247_scraped.csv

scrape_on3_portal():
- Similar scraping approach for On3's portal tracker
- URL: https://www.on3.com/transfer-portal/
- Same headers and rate limiting
- Extract available data
- Save to data/raw/portal_on3_scraped.csv

create_portal_template():
- If ALL scraping fails (which is likely for JavaScript-heavy sites), create a comprehensive CSV template
- data/raw/portal_entries_manual.csv with columns:
  player_name, original_school, original_conference, new_school, new_conference,
  position, season, stars, composite_rating, transfer_direction, entry_date,
  commitment_date, prev_games_started, prev_stats_summary, reason_category,
  coaching_change_flag, nil_factor_flag, playing_time_factor_flag
- Include 20 real example entries (manually filled from recent portal cycles) so tests work
- Print instructions for where to find complete data for manual entry

merge_portal_sources():
- Combine API data, scraped data, and manual data
- Deduplicate on player_name + original_school + season
- Prefer API data > scraped data > manual data when conflicts exist
- Enrich with:
  - Player stats from cfb_stats (join on name + school + year before transfer)
  - Recruiting data from cfb_recruiting
  - School tier from config.yaml
  - Coaching change data from cfbd coaches endpoint
- Calculate transfer_direction: compare origin school tier to destination school tier
- Save enriched dataset to data/processed/portal_enriched.csv

build_portal_outcomes():
- For transfers who played at least one season at new school:
  - Compare stats at old school vs new school (per-game to normalize)
  - Create transfer_success score: improvement in production percentile at position
  - Flag "successful transfers" (improved) vs "failed transfers" (declined)
- This is training data for the portal fit model
- Save to data/processed/portal_outcomes.csv

Same patterns: caching, logging, error handling, standalone runnable.
Also add a class attribute: self.scraping_enabled = True that can be set to False in config to skip all scraping.
```

### Prompt 5 (REPLACES original) — NIL Data + Social Media Scraping
```
Write src/data_collection/cfb_nil.py with a class CFBNILCollector.

This is the most scraping-heavy collector since NIL data isn't in any free API.

Methods:

scrape_on3_nil_100():
- Target: https://www.on3.com/nil/rankings/player/nil-100/
- Extract: rank, player name, school, position, On3 NIL valuation
- Use requests + BeautifulSoup first
- If blocked by JavaScript:
  - Try with playwright (headless Chromium):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector('.player-row')  # adjust selector
        content = page.content()
        browser.close()
  - Parse the rendered HTML with BeautifulSoup
- If playwright isn't installed, fall back to template
- Save to data/raw/on3_nil_100.csv

scrape_spotrac_nil():
- Target Spotrac's college football NIL tracker pages
- Look for: player name, school, position, reported deal values, deal type
- Same scraping approach with fallback chain: requests → playwright → template
- Save to data/raw/spotrac_nil.csv

scrape_social_media_profiles(player_list):
- Given a list of player names and schools, attempt to find and scrape follower counts
- Instagram: Search for player profiles, extract follower count from public profiles
  - Use mobile user agent for better access to public profiles
  - URL pattern: https://www.instagram.com/{username}/
  - Look for follower count in page metadata or JSON-LD
- TikTok: Similar approach
  - URL pattern: https://www.tiktok.com/@{username}
- Twitter/X: Harder to scrape, may need to use a manual template
- For each player, save: platform, username (if found), follower_count, scrape_date
- This WILL be unreliable — build it to fail gracefully
- Save to data/raw/social_media_scraped.csv
- Also maintain a manual override file: data/raw/social_media_manual.csv that takes priority

create_nil_templates():
- data/raw/nil_valuations_manual.csv:
  player_name, school, position, conference, season, estimated_annual_nil_value,
  nil_tier, on3_nil_valuation, primary_source, number_of_deals, collective_pct,
  brand_pct, social_pct, notes

- data/raw/social_media_manual.csv:
  player_name, school, position, instagram_followers, instagram_engagement_rate,
  tiktok_followers, tiktok_avg_views, twitter_followers, youtube_subscribers,
  total_following, measurement_date

- data/raw/nil_collective_budgets.csv:
  school, conference, estimated_annual_budget, estimated_roster_spots_funded,
  avg_deal_value, top_deal_value, collective_name, source_url, season

- Populate each with 50+ realistic sample entries for testing
- Mark sample data with is_sample=True column

estimate_social_value(social_profile):
- Takes a player's social media profile dict
- Estimates annual monetization value:
  instagram_value = followers * engagement_rate * posts_per_month * cpm_rate * 12
  tiktok_value = followers * 0.005 * posts_per_month * 5.0 * 12  
  twitter_value = followers * 0.003 * posts_per_month * 3.0 * 12
  total = instagram_value + tiktok_value + twitter_value
- Default engagement rates and CPMs are configurable in config.yaml
- Returns: {"total_social_value": X, "platform_breakdown": {...}, "confidence": "high/medium/low"}

build_nil_master_dataset():
- Merge in priority order: scraped On3 > scraped Spotrac > manual valuations
- Join with social media data (scraped > manual)
- Join with player stats from cfb_stats
- Join with recruiting data from cfb_recruiting
- Add school tier, conference tier, market size from config
- Calculate derived features (done properly in feature engineering, but get the joins right here)
- Save to data/processed/nil_master_dataset.csv
- Print: total players with NIL data, coverage by position, coverage by conference, data quality score

SCRAPING BEST PRACTICES — apply to all scraping methods:
- Always use realistic browser headers with User-Agent rotation
- Rate limit: minimum 2 seconds between requests to same domain
- Respect robots.txt (check before scraping, warn if disallowed)
- Cache all scraped results with timestamps
- Never scrape more than 100 pages in a single run
- Log every request URL and response status
- If a site returns 403/429, stop immediately and switch to template fallback
- Store raw HTML in data/cache/html/ for debugging
- All scraping is wrapped in try/except — scraping failures should NEVER crash the pipeline
- Add a config flag: SCRAPING_ENABLED=true in .env (can disable all scraping)
```

### Prompt 6 (REPLACES original) — Draft History + NFL Data
```
Write src/data_collection/draft_history.py with a class DraftHistoryCollector.

Uses nfl_data_py for NFL-side data and connects it back to college stats.

Methods:

collect_draft_picks(start_year, end_year):
- Use nfl_data_py to pull all NFL draft picks 2015-2025
- Columns: player name, college, college conference, position, round, pick, team, age
- Save to data/raw/nfl_draft_picks.csv

collect_combine_data(start_year, end_year):
- Use nfl_data_py for NFL combine results
- Columns: player name, college, position, height, weight, 40_yard, bench_press,
  vertical_jump, broad_jump, three_cone, shuttle, arm_length, hand_size
- Save to data/raw/nfl_combine.csv

collect_rookie_performance(start_year, end_year):
- Use nfl_data_py for NFL player seasonal stats
- For each drafted player, pull their first 1-4 years of NFL production
- This measures "draft hit rate" — did the pick actually work out
- Save to data/raw/nfl_rookie_stats.csv

build_rookie_wage_scale():
- Create a reference table mapping draft slot to contract value
- Round 1: 4 years + 5th year option, values by pick (pick 1 ≈ $41M, pick 32 ≈ $14M)
- Rounds 2-7: 4 years, values decrease by round
- Save as data/raw/rookie_wage_scale.csv
- This is used by draft_projector.py to estimate NFL earnings

build_college_to_nfl_dataset():
- For each draft pick, match to their college stats using cfb_stats + cfb_recruiting
- Fuzzy match on name + college
- Create unified dataset: college stats + recruiting + combine + draft result + NFL production
- This is THE training dataset for the draft projection model
- Save to data/processed/college_to_nfl_dataset.csv
- Print matching rate and log unmatched players
```

---

## New Prompt — Visualization Layer with sportypy

### Prompt 6B — Visualization Utilities with sportypy
```
Write src/utils/visualization.py with visualization utilities for the dashboard.

This module uses:
1. sportypy — for drawing football field surfaces
2. plotly — for interactive charts
3. matplotlib/seaborn — for static charts and SHAP plots

FOOTBALL FIELD VISUALIZATIONS (using sportypy):

create_depth_chart_field(roster_df, school_name, side='offense'):
- Use sportypy to draw a regulation football field:
  from sportypy.surfaces.football import FootballField
  field = FootballField(league="ncaa")  # or however sportypy initializes
- Overlay player positions on the field as a visual depth chart
- For offense: show QB, RBs, WRs, TEs, OL in their typical alignment
  - Color code by: starter (green), backup (yellow), at-risk of transferring (red)
  - Size dots by production score (bigger = more productive)
  - Label with player name and jersey number
- For defense: show DL, LBs, DBs in base alignment
- Use matplotlib to render sportypy's field and add player annotations
- Return a matplotlib figure
- If sportypy doesn't support the exact overlay you need, draw a simplified field using matplotlib patches/rectangles and overlay players manually

create_roster_heatmap(roster_df, metric='flight_risk_score'):
- Football field visualization where each position is color-coded by a metric
- Could show: flight risk (red = high risk), NIL value (green = well-paid), production (blue = productive)
- Useful for quickly seeing which parts of the roster are vulnerable

create_position_depth_visual(roster_df, position_group):
- Vertical depth chart for a single position group
- Show: starter, backup, 3rd string with stats, NIL value, and flight risk for each
- Highlight gaps where depth is thin

INTERACTIVE CHARTS (using plotly):

create_nil_breakdown_donut(prediction_result):
- Donut chart showing value breakdown: performance, social media, school brand, recruiting, draft potential
- Use plotly for interactivity (hover for details)

create_flight_risk_scatter(roster_df):
- X-axis: production score, Y-axis: flight risk score
- Size: NIL value, Color: position group
- Quadrants labeled: "Retain at All Costs" (high production, high risk), "Core Players" (high production, low risk), "Monitor" (low production, high risk), "Development" (low production, low risk)

create_transfer_impact_comparison(current_value, projected_value, school_names):
- Side-by-side bar chart: current NIL value vs projected at each potential school

create_win_projection_gauge(projected_wins, confidence_interval):
- Gauge/speedometer chart showing projected wins with confidence bands
- Mark conference championship threshold and CFP threshold

create_cap_allocation_treemap(budget_allocation):
- Treemap showing NIL budget allocation by position group and player
- Size = dollars allocated, color = ROI (wins per dollar)

create_shap_waterfall(shap_values, feature_names, prediction_value):
- SHAP waterfall chart showing which features pushed the prediction up or down
- Use shap library's built-in plotting, styled to match our dashboard theme

create_comparable_players_radar(player_features, comparable_features, feature_names):
- Radar/spider chart comparing a player's profile to their top 3 comparables
- Good for NIL valuation and draft projection explanations

STYLING:
- All charts should use a consistent color palette defined at the top of the file:
  COLORS = {
    "primary": "#00C853",      # green
    "secondary": "#1a1a2e",    # dark navy
    "accent": "#00BCD4",       # teal
    "warning": "#FF9800",      # orange
    "danger": "#F44336",       # red
    "success": "#4CAF50",      # green
    "text": "#FFFFFF",         # white
    "text_secondary": "#B0BEC5", # gray
    "background": "#0d1117",   # dark background
    "surface": "#161b22",      # card background
  }
- All plotly charts: dark template, transparent background, white text
- All matplotlib charts: dark style, matching colors
- Include a set_portal_iq_style() function that configures matplotlib rcParams globally

UTILITY FUNCTIONS:
- save_figure(fig, filename, format='png'): saves to outputs/figures/
- fig_to_streamlit(fig): converts matplotlib figure to format Streamlit can display
- create_school_logo_badge(school_name): returns a simple colored badge with school initials (placeholder until real logos)

SPORTYPY IMPLEMENTATION NOTES:
- sportypy docs: https://sportypy.sportsdataverse.org/
- Main class is likely: sportypy.surfaces.football.FootballField or similar
- The package draws regulation surfaces — we overlay our data on top
- If sportypy API doesn't match expectations, check their docs and adapt
- If sportypy can't do what we need, fall back to custom matplotlib field drawing
- Test sportypy independently first: draw a blank field and verify it works before building overlays
```

---

## New Prompt — Data Aggregation Layer

### Prompt 6C — Master Data Aggregator
```
Write src/utils/data_loader.py with a class PortalIQDataLoader.

This is the single entry point for loading and merging all data sources. Every model and the dashboard should use this class instead of loading CSVs directly.

Methods:

__init__(self, config_path='config.yaml'):
- Load config
- Set up paths to all data directories
- Initialize empty dataframe cache (in-memory)

load_player_stats(season=None):
- Load player season stats from cfb_stats output
- If season specified, filter to that season
- Cache in memory after first load
- Return dataframe

load_epa_metrics(season=None):
- Load player-level EPA metrics from sportsdataverse output
- This is the advanced analytics data
- Return dataframe

load_recruiting(year_range=None):
- Load recruiting rankings from recruitR output
- Return dataframe

load_portal_data(season=None):
- Load enriched portal data
- Return dataframe

load_nil_data():
- Load the NIL master dataset
- Return dataframe

load_team_data(season=None):
- Load team records, ratings, and advanced metrics
- Return dataframe

load_draft_history():
- Load college-to-NFL dataset
- Return dataframe

build_master_player_dataset(season=None):
- This is the MAIN method — joins everything into one comprehensive player dataframe
- Join order:
  1. Start with player season stats (base)
  2. LEFT JOIN EPA metrics on player_name + team + season
  3. LEFT JOIN recruiting data on player_name + school (using the recruit-player mapping)
  4. LEFT JOIN NIL data on player_name + school + season
  5. LEFT JOIN social media data on player_name + school
  6. LEFT JOIN team data on team + season
  7. ADD school tier, conference tier from config
  8. ADD market size from school-city mapping
- Handle name mismatches between sources:
  - Normalize all names: strip whitespace, title case, handle Jr./III/etc.
  - Use the fuzzy matching utility from player_matching.py
- Handle duplicates: if a player transferred mid-season, they might appear in two teams — keep both records with a transfer_flag
- Add data_completeness_score: what percentage of columns are non-null for each player (0-100)
- Save to data/processed/master_player_dataset.csv
- Print data quality report:
  - Total players
  - Players with EPA data: X%
  - Players with recruiting data: X%
  - Players with NIL data: X%
  - Players with social media data: X%
  - Average data completeness score
- Return dataframe

get_school_roster(school, season=None):
- Filter master dataset to a specific school
- Return sorted by position group, then by production score

get_portal_players(season=None, position=None, min_stars=None):
- Get available portal players with optional filters
- Return sorted by production score

get_position_group_stats(position_group, season=None):
- Get all players at a position group with their stats, NIL, recruiting
- Useful for comparisons and percentile calculations

refresh_data():
- Clear all caches
- Re-run all data collection scripts
- Re-build master dataset
- Use for scheduled data updates

DATA QUALITY CHECKS — run these on every load:
- Check for duplicate player entries (same name + school + season)
- Check for impossible values (negative stats, ratings > 1.0, etc.)
- Check for missing critical columns (player_name, school, position must always exist)
- Log all quality issues to outputs/data_quality_log.txt
- Never silently drop data — always warn
```

### Prompt 6D — Player Matching Utility
```
Write src/utils/player_matching.py with robust player name matching across data sources.

This is a critical utility because player names are spelled differently across sources:
- cfbd: "CJ Stroud"
- recruitR: "C.J. Stroud"  
- On3: "C.J. Stroud Jr."
- 247Sports: "CJ Stroud"
- ESPN: "C.J. Stroud"

class PlayerMatcher:

normalize_name(name):
- Strip whitespace, convert to lowercase
- Remove suffixes: Jr., Sr., II, III, IV
- Remove periods from initials: "C.J." → "CJ"
- Handle common abbreviations: "William" / "Will", "Robert" / "Rob" / "Bobby"
- Remove accents/diacritics
- Return normalized string

fuzzy_match(name1, name2, threshold=0.85):
- Use difflib.SequenceMatcher
- Compare normalized versions
- Return (is_match: bool, confidence: float)

match_player(target_name, target_school, target_position, candidate_df, 
             name_col='player_name', school_col='school', position_col='position'):
- Try exact match on normalized name + school first
- If no exact match, try fuzzy name match + exact school
- If still no match, try fuzzy name + same conference + same position (for transfers)
- If still no match, try fuzzy name + same position (last resort, low confidence)
- Return: {"matched": True/False, "matched_record": row or None, "confidence": float, "match_type": "exact/fuzzy_school/fuzzy_conference/fuzzy_position"}

batch_match(source_df, target_df, source_name_col, target_name_col, 
            source_school_col, target_school_col):
- Match all players from source to target
- Return merged dataframe with match confidence column
- Print matching stats: exact matches, fuzzy matches, unmatched
- Save unmatched records to data/cache/unmatched_players.csv for manual review

build_player_id_mapping():
- Create a unified player ID system across all data sources
- For each unique player, assign a portal_iq_player_id
- Map all source-specific identifiers to this ID
- Save to data/processed/player_id_mapping.csv
- This becomes the join key for all future merges
```

---

## Updated requirements.txt

### Add to Prompt 1's requirements.txt:
```
sportsdataverse
recruitR
sportypy
playwright
nfl_data_py
cfbd
```

### Updated .env.example:
```
CFBD_API_KEY=your_key_here
SCRAPING_ENABLED=true
DATABASE_URL=sqlite:///data/portal_iq.db
PLAYWRIGHT_BROWSERS_PATH=0
```

---

## Updated Build Order

1. **Prompt 1** — Scaffold (from original guide)
2. **Prompt 2 (this doc)** — Master data collector with sportsdataverse + cfbd
3. **Prompt 3 (this doc)** — Recruiting with recruitR
4. **Prompt 5 (this doc)** — NIL data + scraping
5. **Prompt 6D (this doc)** — Player matching utility (you need this before merging anything)
6. **Prompt 6C (this doc)** — Data aggregation layer
7. **Prompt 7 (original guide)** — NIL feature engineering
8. **Prompt 10 (original guide)** — NIL valuation model ← FIRST WORKING MODEL
9. **Prompt 6B (this doc)** — Visualization layer with sportypy
10. **Prompt 16 (original guide)** — Dashboard Page 1 ← FIRST VISUAL
11. **Prompt 4 (this doc)** — Portal data + scraping
12. **Prompt 6 (this doc)** — Draft history
13. Continue with original guide Prompts 8-18

---

## Scraping-to-Partnership Transition Plan

When you're ready to pitch partnerships, you'll have:
1. A working product with real users (built on free data + scraping)
2. Model performance metrics showing what you CAN do
3. A clear story: "With PFF grades, our model accuracy improves from X to Y"

### Partnership Pitch Deck Points:
- "Portal IQ currently serves X programs/collectives"
- "Our NIL valuation model has Y% accuracy using public data"
- "With PFF data integration, we project Z% improvement in accuracy"
- "We're offering a co-branded partnership — 'Powered by PFF' badge in our dashboard"
- "Our platform drives awareness of your data to coaching staffs who may not currently subscribe"

### Data Partnership Priority Order:
1. **PFF** — biggest single accuracy improvement across all models
2. **On3** — structured NIL data makes the valuation model dramatically better
3. **247Sports** — cleaner portal and recruiting data
4. **Hudl** — player tracking data is the long-term moat if you can get it
