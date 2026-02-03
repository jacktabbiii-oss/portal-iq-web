# Portal IQ — Complete Build Guide

## Before You Touch Any Code

### 1. Get Your Accounts & API Keys Ready
- [ ] **College Football Data API** — Free key at https://collegefootballdata.com (sign up, get API key)
- [ ] **GitHub** — Create a new repo called `portal-iq`
- [ ] **On3.com** — Bookmark the NIL 100 page, you'll manually pull data from here
- [ ] **Spotrac.com** — Bookmark college football NIL tracker pages
- [ ] **Python 3.11+** installed
- [ ] **Node.js 18+** installed (for the dashboard later)
- [ ] **Cursor** installed with Claude Code extension or Claude Code CLI

### 2. Open Cursor, Create Your Workspace
```bash
mkdir portal-iq
cd portal-iq
git init
```

### 3. Open the integrated terminal in Cursor and start Claude Code

---

## Phase 1: Project Foundation

### Prompt 1 — Scaffold the Project
```
Create a Python project called "portal-iq" with this structure:

/portal-iq
  /data
    /raw
    /processed
    /cache
  /models
    /nil_valuation
    /portal_prediction
    /draft_projection
    /win_impact
  /src
    /data_collection
      __init__.py
      cfb_stats.py
      cfb_nil.py
      cfb_recruiting.py
      cfb_portal.py
      social_media.py
      draft_history.py
    /feature_engineering
      __init__.py
      nil_features.py
      portal_features.py
      draft_features.py
      roster_features.py
      shared_features.py
    /models
      __init__.py
      nil_valuator.py
      portal_predictor.py
      draft_projector.py
      win_model.py
      roster_optimizer.py
    /api
      __init__.py
      app.py
      routes.py
      schemas.py
    /utils
      __init__.py
      config.py
      data_loader.py
      visualization.py
      player_matching.py
  /dashboard
    streamlit_app.py
    /pages
      nil_valuator.py
      portal_intelligence.py
      draft_tracker.py
      roster_builder.py
  /outputs
    /reports
    /figures
  /tests
    /test_data_collection
    /test_models
    /test_api
    conftest.py
  requirements.txt
  README.md
  .env.example
  config.yaml
  .gitignore

requirements.txt should include:
pandas, numpy, scikit-learn, xgboost, lightgbm, matplotlib, seaborn, plotly,
beautifulsoup4, requests, cfbd, streamlit, fastapi, uvicorn, joblib, pyyaml,
python-dotenv, shap, scipy, pulp, nfl_data_py, lxml, openpyxl, pytest

config.yaml should have sections for:
- data_paths (all the /data subdirectories)
- current_season: 2025
- seasons_range: [2020, 2025]
- school_tiers with these classifications:
    blue_blood: [Alabama, Ohio State, USC, Michigan, Texas, Oklahoma, Notre Dame]
    elite: [Georgia, Clemson, Oregon, Penn State, LSU, Florida, Florida State, Tennessee, Auburn, Wisconsin, Miami]
    power_brand: [Texas A&M, Ole Miss, Michigan State, UCLA, Iowa, Arkansas, South Carolina, NC State, Virginia Tech, Pittsburgh, Louisville, Colorado, Arizona, Utah, Kansas State, Missouri]
    p4_mid: [remaining Power 4 schools]
    g5_strong: [Boise State, Memphis, SMU, UNLV, Tulane, Liberty, James Madison, Jacksonville State, Sam Houston]
    g5: [remaining Group of 5]
- conference_tiers:
    tier1: [SEC, Big Ten]
    tier2: [Big 12, ACC]
    tier3: [American, Mountain West, Sun Belt, MAC, CUSA]
- nil_tiers:
    mega: 1000000
    premium: 500000
    solid: 100000
    moderate: 25000
    entry: 0
- model_params (placeholder hyperparameters for each model type)
- api_keys section referencing .env variables

.env.example should have:
CFBD_API_KEY=your_key_here
DATABASE_URL=sqlite:///data/portal_iq.db

.gitignore for Python projects plus /data/raw/, /data/cache/, .env, /models/*.joblib

README.md should describe Portal IQ as: "AI-powered transfer portal and NIL intelligence platform for college football programs, NIL collectives, agents, and analysts. Built by Elite Sports Solutions." Include sections for Overview, Features (NIL Valuation, Portal Intelligence, Draft Projection, Roster Optimization), Setup, and Usage.
```

---

## Phase 2: Data Collection

### Prompt 2 — College Football Stats
```
Write src/data_collection/cfb_stats.py with a class CFBStatsCollector that uses the cfbd Python package.

The class should:

1. Load the API key from .env using python-dotenv and configure the cfbd client

2. Have these methods:

collect_player_stats(start_year, end_year):
- Pull player season stats for passing, rushing, receiving for each year
- Include: player name, team, conference, season, games played, and all stat columns
- Handle pagination if the API requires it
- Return a combined dataframe

collect_player_info(start_year, end_year):
- Pull player roster info for each team each year
- Include: player name, team, position, height, weight, year (FR/SO/JR/SR), hometown, jersey number
- Return a dataframe

collect_team_data(start_year, end_year):
- Pull team records (wins, losses) per season
- Pull team SP+ ratings or talent composite rankings if available
- Pull team recruiting class rankings per year
- Return a dataframe

collect_game_results(start_year, end_year):
- Pull game-by-game results for all teams
- Include: teams, scores, conference game flag, home/away, week
- This is needed later for strength of schedule calculations
- Return a dataframe

collect_all(start_year=2020, end_year=2025):
- Runs all collection methods
- Saves each dataframe as a CSV in data/raw/ with descriptive filenames
- Also saves to data/cache/ with a timestamp in the filename so we don't re-download
- Prints a summary: rows collected per dataset, date range, any missing data warnings
- Returns a dict of all dataframes

3. Every method should have:
- try/except with clear error messages
- Logging using Python's logging module
- A check for cached data before hitting the API (if cache exists and is less than 24 hours old, use it)
- Rate limiting (0.5 second sleep between API calls)

4. Add a main block at the bottom so you can run it standalone:
if __name__ == "__main__":
    collector = CFBStatsCollector()
    collector.collect_all()
```

### Prompt 3 — Recruiting Data
```
Write src/data_collection/cfb_recruiting.py with a class CFBRecruitingCollector that:

1. Uses cfbd to pull recruiting data for 2018-2025 (going back further for recruiting since we want to see how recruits from 2018 perform through 2025):
   - Individual player recruiting rankings: name, school committed to, position, stars (1-5), rating (0-1 scale), composite ranking, state, city
   - Team recruiting class rankings per year: school, year, overall rank, total commits, average rating, points

2. Creates a recruit-to-college-player matching function:
   - Takes a recruit's name, school, and position
   - Fuzzy matches them to our player stats data (from cfb_stats.py) since names may not match exactly
   - Returns the matched player record or None
   - Use difflib.SequenceMatcher for fuzzy matching with a threshold of 0.85

3. Has a build_recruiting_performance_dataset() method that:
   - For each recruit in our data, attempts to match them to their college stats
   - Creates a merged dataset: recruiting info + college production
   - This lets us analyze whether 5-stars outperform 3-stars, which feeds into our models
   - Calculates "production over expectation" (actual stats vs average for their star rating)

4. Saves everything to data/raw/recruiting_*.csv
5. Same caching, logging, and error handling patterns as cfb_stats.py
6. Standalone runnable with __main__
```

### Prompt 4 — Transfer Portal Data
```
Write src/data_collection/cfb_portal.py with a class CFBPortalCollector that:

1. Uses cfbd's transfer portal endpoint (if available) to pull portal entries for 2021-2025:
   - Player name, original school, new school (if committed), position, star rating, year
   - Entry date, commitment date (if applicable)

2. If the cfbd API doesn't have complete portal data, create a structured CSV template at data/raw/portal_entries.csv with columns:
   player_name, original_school, original_conference, new_school, new_conference,
   position, season, stars, recruiting_ranking, transfer_direction (up/lateral/down based on school tier),
   prev_team_wins, prev_snap_pct, prev_starter_flag, reason_category (playing_time/coaching_change/nil/scheme_fit/personal/unknown)

   Include detailed comments at the top of the file explaining where to manually source this data:
   - On3 Transfer Portal rankings
   - 247Sports transfer portal
   - ESPN transfer portal tracker
   - Rivals transfer portal

3. Has an enrich_portal_data() method that:
   - Takes portal entries and joins with player stats (from cfb_stats) to add production data from their previous school
   - Joins with recruiting data to add their original star rating
   - Adds school tier for both origin and destination schools (from config.yaml)
   - Calculates "transfer direction" — did they go to a higher-tier, same-tier, or lower-tier program
   - Adds whether the origin school had a coaching change that year

4. Has a build_portal_outcomes() method that:
   - For players who transferred and then played a season, compares their stats at the new school vs old school
   - Creates a "transfer success" metric: did they improve, maintain, or decline in production
   - This becomes training data for our portal fit model

5. Same patterns: caching, logging, error handling, standalone runnable
```

### Prompt 5 — NIL Data Templates
```
Write src/data_collection/cfb_nil.py with a class CFBNILCollector that:

1. Creates structured data templates (since NIL data isn't available via API):

   data/raw/nil_valuations.csv:
   player_name, school, position, conference, season, estimated_annual_nil_value,
   nil_tier (mega/premium/solid/moderate/entry), on3_nil_valuation, primary_nil_source,
   number_of_known_deals, collective_deal_flag, brand_deal_flag, social_media_deal_flag,
   notes

   data/raw/social_media_profiles.csv:
   player_name, school, position, instagram_followers, instagram_engagement_rate,
   tiktok_followers, tiktok_avg_views, twitter_followers, youtube_subscribers,
   total_social_following, verified_flag, measurement_date

   data/raw/nil_collective_budgets.csv:
   school, conference, estimated_annual_budget, estimated_roster_spots_funded,
   estimated_avg_deal_value, top_deal_value, collective_name, source, season

2. Has a scrape_on3_nil_rankings() method that:
   - Attempts to scrape the On3 NIL 100 list from https://www.on3.com/nil/rankings/player/nil-100/
   - Extracts: player name, school, position, On3 NIL valuation, ranking
   - Uses BeautifulSoup with proper headers
   - If scraping fails (likely due to JavaScript rendering), prints clear instructions:
     "On3 NIL 100 requires JavaScript. Please manually download the data and save to data/raw/on3_nil_100.csv"
   - Falls back gracefully to the template

3. Has an estimate_social_value() method that takes a player's social media profile and estimates their social media monetization value:
   - Instagram: followers * 0.01 * estimated_posts_per_month (default 4) * CPM_rate (default $10)
   - TikTok: followers * 0.005 * estimated_posts_per_month (default 8) * CPM_rate (default $5)
   - Twitter: followers * 0.003 * estimated_posts_per_month (default 10) * CPM_rate (default $3)
   - Returns annual estimated social media earnings
   - Document that these are rough estimates and CPM rates should be calibrated with real data

4. Has a build_nil_dataset() method that:
   - Merges nil_valuations with social_media_profiles and player stats
   - Adds school tier, conference tier from config
   - Adds recruiting star rating from recruiting data
   - Creates the master NIL analysis dataset
   - Saves to data/processed/nil_master_dataset.csv

5. Has a populate_sample_data() method that fills in the templates with realistic sample data for testing:
   - 50 sample players across different tiers and positions
   - Realistic social media follower counts by tier
   - This lets us build and test models before we have real data
   - Clearly mark this data as SAMPLE in a column

6. Same patterns: logging, caching, error handling, standalone runnable
```

### Prompt 6 — NFL Draft History (for Draft Projection Model)
```
Write src/data_collection/draft_history.py with a class DraftHistoryCollector that:

1. Uses nfl_data_py to pull NFL draft picks from 2018-2025:
   - Player name, college, position, round, pick number, team, age at draft

2. For each drafted player, pulls their college stats from our cfb_stats data and matches them:
   - Fuzzy match on name + college
   - Get their final 1-2 college seasons of production
   - Get their recruiting star rating

3. Pulls NFL combine data via nfl_data_py:
   - 40-yard dash, bench press, vertical jump, broad jump, 3-cone, shuttle, height, weight, arm length, hand size
   - Match to draft picks

4. Pulls rookie contract values from the NFL rookie wage scale:
   - Create a lookup table: round + pick number → estimated 4-year contract value + signing bonus
   - This is relatively standardized so we can use a formula or reference table

5. For drafted players, pulls their first 1-3 years of NFL stats (if available) to measure "draft hit rate":
   - Games played, games started, basic counting stats by position
   - This helps us calibrate: does our draft projection correlate with actual NFL production?

6. Creates a unified dataset: college stats + recruiting + combine + draft result + NFL production
   Saves to data/processed/draft_history_dataset.csv

7. Same patterns. Standalone runnable.
```

---

## Phase 3: Feature Engineering

### Prompt 7 — NIL Features
```
Write src/feature_engineering/nil_features.py with a class NILFeatureEngineer:

Method: build_features(player_data, nil_data, recruiting_data, social_data, team_data)

Takes the raw collected data and produces model-ready features. Return a clean dataframe with these features:

PERFORMANCE FEATURES (position-aware):
- For QBs: pass yards/game, pass TDs/game, completion pct, yards per attempt, TD:INT ratio, rushing yards/game, total TDs, passer rating or QBR if available
- For RBs: rush yards/game, rush TDs/game, yards per carry, receptions/game, receiving yards/game, total TDs, total scrimmage yards/game
- For WRs/TEs: receptions/game, receiving yards/game, receiving TDs/game, yards per reception, target share estimate (receptions / team pass attempts)
- For defensive players: tackles/game, tackles for loss/game, sacks/game (if DE/LB), interceptions, pass breakups
- Create a "position_group" column that maps specific positions to groups: QB, RB, WR, TE, OL, DL, EDGE, LB, CB, S
- Create a normalized "production score" 0-100 within each position group (percentile rank of key stats)

SCHOOL & BRAND FEATURES:
- school_tier: numeric encoding from config (blue_blood=6, elite=5, power_brand=4, p4_mid=3, g5_strong=2, g5=1)
- conference_tier: numeric encoding (SEC/BigTen=3, Big12/ACC=2, G5=1)
- team_wins: wins in current/most recent season
- team_win_pct: over player's career at school
- cfp_appearance: binary, has this team made the CFP during the player's tenure
- conference_championship: binary, has this team won its conference during player's tenure
- school_market_size: approximate metro population of school's city (create a dictionary mapping ~130 FBS schools to metro populations)
- football_state: binary flag for whether the school is in a top football state (Texas, Florida, Georgia, Alabama, Ohio, California, Louisiana, Tennessee, Oklahoma, Michigan, Pennsylvania)

RECRUITING & PROFILE FEATURES:
- recruiting_stars: 2-5 (or 0 if unrated)
- recruiting_composite: 0-1 rating
- recruiting_position_rank: position ranking in their class
- recruiting_class_rank: overall ranking in their class
- years_in_college: 1-6 (super seniors, COVID year)
- year_classification: FR=1, SO=2, JR=3, SR=4, encoded numerically
- remaining_eligibility: estimated years remaining
- is_starter: binary
- games_started_pct: career games started / games available
- age: if available

SOCIAL MEDIA FEATURES:
- total_social_following: sum of all platforms
- log_total_following: log transform (social media follows a power law)
- instagram_followers (log transformed)
- tiktok_followers (log transformed)
- twitter_followers (log transformed)
- estimated_social_value: from our social value estimator
- has_significant_following: binary flag (>50K total)
- social_platform_concentration: what % of following is on their largest platform (diversity matters for NIL)

NFL DRAFT FEATURES:
- projected_draft_flag: binary, is this player a projected draft pick
- projected_draft_round: 1-7 or 0 if undrafted projection (simple heuristic based on production + school tier + position for now, the full model comes later)

INTERACTION FEATURES:
- school_x_production: school_tier * production_score (great player at great school = premium)
- social_x_production: log_total_following * production_score
- qb_premium: binary flag if position is QB (QBs get outsized NIL)

TARGET VARIABLE:
- nil_value: the estimated annual NIL value (for regression)
- nil_tier: mega/premium/solid/moderate/entry (for classification)

Handle missing values:
- Numeric: fill with position-group median
- Categorical: fill with mode or "unknown"
- Drop any player with >50% missing features
- Document every imputation decision

Save the engineered features to data/processed/nil_features_ready.csv
Include a method get_feature_names() that returns the list of feature columns (excluding target)
Include a method get_feature_importance_groups() that returns features grouped by category for later SHAP analysis
```

### Prompt 8 — Portal Features
```
Write src/feature_engineering/portal_features.py with a class PortalFeatureEngineer:

Method: build_flight_risk_features(player_data, team_data, nil_data, recruiting_data, portal_history)

Returns a dataframe where each row is a player-season with features predicting whether they'll enter the portal. Target: entered_portal (binary 0/1).

PLAYING TIME FEATURES:
- snap_pct: estimated snap percentage (games started / total team games as proxy)
- snap_trend: is their playing time increasing or decreasing year over year
- is_starter: binary
- depth_chart_position: 1 (starter), 2 (backup), 3+ (buried) — estimate from stats
- career_starts: total games started
- games_played_pct: games played / games available in career

PERFORMANCE vs EXPECTATION:
- recruiting_stars: their original rating
- production_vs_star_avg: their stats vs the average stats for their star rating at their position (a 5-star playing like a 3-star is unhappy)
- production_trend: improving or declining year over year
- breakout_flag: binary, did they significantly outperform expectations this year (might attract portal interest FROM other schools, but also means they might stay if utilized)

TEAM CONTEXT:
- team_wins: current season
- team_win_trend: wins this year vs last year (losing drives transfers)
- coaching_change: binary flag, did the head coach change this offseason or during season
- coordinator_change: if available, did the OC/DC change
- team_nil_tier: estimated NIL budget tier of current school
- conference_tier: of current school
- school_tier: of current school

POSITIONAL CONTEXT:
- position_depth: how many other players at their position on the roster (crowded room = flight risk)
- incoming_recruits_at_position: did the school just sign highly rated recruits at their position (getting recruited over)
- position_group: encoded

PERSONAL/GEOGRAPHIC:
- distance_from_home: miles from hometown to school (can calculate from city coordinates)
- years_at_school: how long they've been there
- is_grad_transfer_eligible: binary (graduated, can transfer and play immediately)
- remaining_eligibility: years left

NIL CONTEXT:
- estimated_nil_value: their current NIL valuation
- nil_vs_team_median: their NIL relative to teammates (below median = unhappy)
- nil_vs_position_avg: their NIL relative to their position group nationally
- nil_could_increase_elsewhere: binary flag, would a higher-tier school likely pay more

HISTORICAL PORTAL PATTERNS:
- position_portal_rate: what percentage of players at this position typically enter the portal
- school_portal_rate: what percentage of players from this school have entered the portal in recent years
- conference_portal_rate: same for conference

TARGET:
- entered_portal: 1 if the player entered the transfer portal, 0 if not

Method: build_portal_fit_features(portal_player, target_school, school_roster, team_data)

Returns a single-row dataframe scoring how well a portal player fits a specific school. Features:

- positional_need_score: 0-100, does the school need this position (based on roster gaps, departures, depth)
- production_upgrade: how much better is this player than the current starter at their position
- school_tier_match: is the player moving to a similar, higher, or lower tier (over-reaching transfers often fail)
- conference_level_match: same for conference
- scheme_fit_estimate: basic proxy based on stat profile (spread offense QB vs pro-style, etc.)
- geographic_proximity: distance from player's hometown to target school
- nil_budget_fit: can this school afford what this player is likely worth
- academic_fit: if we have any academic data, otherwise skip
- returning_production_need: how much production did this team lose at this position group
- team_win_trajectory: is this team on the rise or declining

Save both feature sets to data/processed/
Include feature name getters and group mappings for SHAP.
```

### Prompt 9 — Draft Projection Features
```
Write src/feature_engineering/draft_features.py with a class DraftFeatureEngineer:

Method: build_features(player_stats, recruiting_data, combine_data, draft_history)

Features for predicting where a college player will be drafted:

PRODUCTION FEATURES (position-specific, same groupings as NIL features):
- Per-game stats for most recent season
- Per-game stats averaged over college career
- Production trend (improving or declining)
- Total career production (counting stats)
- Games played / started career totals
- "Breakout age" — what year did they first become a starter

MEASURABLES:
- Height, weight (from roster data)
- BMI calculated
- Combine metrics if available (40, vertical, bench, broad, 3-cone, shuttle)
- Position-specific athletic scores (speed score for RBs: weight * 200 / 40_time^4, etc.)
- If no combine data, fill with position averages and flag as estimated

SCHOOL & CONTEXT:
- school_tier
- conference_tier
- competition_level: strength of schedule proxy
- production_environment: was this player in a spread system (inflated WR/QB stats) or pro-style
- team_talent_composite: overall talent on their team (great stats on a bad team might mean more)

RECRUITING:
- stars, composite, position rank, overall rank
- "development score": production relative to recruiting ranking (a 3-star producing like a 1st rounder = great development)

DRAFT CONTEXT:
- position_scarcity: how many players at this position typically go in rounds 1-3
- draft_class_depth: how strong is this year's class at their position (more competition = later pick)
- age: age on draft day (younger is better, especially for non-QBs)
- years_in_college: 3-year juniors are valued differently than 5th-year seniors
- early_declare: binary, did they leave early (signal of confidence/talent)

TARGET VARIABLES:
- was_drafted: binary (for classification)
- draft_round: 1-7 (for ordinal/regression)
- draft_pick: 1-260ish (for regression)
- draft_value: using the Jimmy Johnson trade value chart points

Save to data/processed/draft_features_ready.csv
Same patterns for feature names and groupings.
```

---

## Phase 4: Models

### Prompt 10 — NIL Valuation Model
```
Write src/models/nil_valuator.py with a class NILValuator:

1. Has a train(features_df, target_col='nil_value', tier_col='nil_tier') method:

   REGRESSION MODEL (predicting dollar value):
   - Split: 80/20 train/test, stratified by nil_tier to ensure representation
   - Train these models: Ridge Regression, Random Forest, XGBoost, LightGBM
   - For each model:
     - StandardScaler on numeric features
     - 5-fold cross-validation on training set
     - Track: RMSE, MAE, R², MAPE
   - Use log-transform on the target variable (NIL values are right-skewed), then exponentiate predictions back
   - Select best model by test set MAE
   - Calculate SHAP values for the best model
   - Save best model to models/nil_valuation/value_model.joblib
   - Save scaler to models/nil_valuation/scaler.joblib
   - Save performance metrics to models/nil_valuation/metrics.json

   CLASSIFICATION MODEL (predicting tier):
   - Same split as regression
   - Train: Logistic Regression, Random Forest, XGBoost
   - Evaluate: accuracy, weighted F1, confusion matrix, per-class precision/recall
   - Select best by weighted F1
   - Save to models/nil_valuation/tier_model.joblib

   TWO-STAGE MODEL:
   - First predict tier (classification)
   - Then predict value within tier (separate regression model per tier)
   - Compare performance to the single regression model
   - Use whichever performs better

   Print a full training report with all metrics and save to outputs/reports/nil_model_training_report.txt

2. Has a predict(player_features) method that returns a dict:
   {
     "predicted_nil_value": dollar amount,
     "predicted_nil_range": {"low": X, "mid": Y, "high": Z},  # using CV error for confidence interval
     "predicted_tier": "premium",
     "tier_probabilities": {"mega": 0.05, "premium": 0.65, "solid": 0.25, "moderate": 0.05, "entry": 0.0},
     "confidence": "high/medium/low",  # based on how far the player is from training distribution
     "value_breakdown": {  # percentage of value attributable to each feature group
       "on_field_performance": 0.35,
       "social_media": 0.25,
       "school_brand": 0.20,
       "recruiting_pedigree": 0.10,
       "draft_projection": 0.10
     },
     "comparable_players": [  # 3 most similar players from training data by feature distance
       {"name": "...", "school": "...", "nil_value": X, "similarity_score": 0.92}
     ],
     "shap_explanation": {  # top 5 features driving this prediction up or down
       "school_tier": +150000,
       "log_instagram_followers": +120000,
       "production_score": +80000,
       "years_in_college": -30000,
       "conference_tier": +25000
     }
   }

3. Has a transfer_impact(player_features, new_school) method:
   - Takes current player features and a target school name
   - Swaps out school_tier, conference_tier, school_market_size, team_wins, and related features for the new school's values
   - Re-runs prediction
   - Returns: {"current_value": X, "projected_value_at_new_school": Y, "value_change": Z, "pct_change": W}

4. Has a what_if_social(player_features, new_follower_counts) method:
   - Swaps social media features
   - Re-runs prediction
   - Returns impact of social media growth on NIL value

5. Has a generate_position_market_report(features_df, position_group) method:
   - For a given position, shows the distribution of NIL values
   - Lists the top 10 most valuable players
   - Shows the average NIL by school tier and conference
   - Identifies the most "undervalued" players (high production, low NIL)
   - Saves report to outputs/reports/

6. All models should gracefully handle the case where training data is small (<50 observations):
   - Use simpler models (Ridge, small Random Forest)
   - Use leave-one-out CV instead of 5-fold
   - Print warnings about low confidence
   - Recommend minimum data size for reliable predictions
```

### Prompt 11 — Transfer Portal Predictor
```
Write src/models/portal_predictor.py with a class PortalPredictor:

1. Has a train_flight_risk(features_df) method:

   FLIGHT RISK MODEL (binary classification: will this player enter the portal?):
   - Handle class imbalance (most players DON'T transfer): use SMOTE or class_weight='balanced'
   - Split: temporal split — train on earlier years, test on most recent year
   - Train: Logistic Regression, Random Forest, XGBoost, LightGBM
   - Evaluate: AUC-ROC, precision, recall, F1, precision-recall AUC
   - Focus on recall for the positive class (we'd rather flag someone who doesn't transfer than miss someone who does)
   - SHAP values for best model
   - Save best model to models/portal_prediction/flight_risk_model.joblib
   - Save metrics and training report

2. Has a predict_flight_risk(player_features) method that returns:
   {
     "player_name": "...",
     "flight_risk_score": 0-100 (probability * 100),
     "risk_level": "high/medium/low",  # high >60, medium 30-60, low <30
     "top_risk_factors": [  # top 5 SHAP features pushing toward transfer
       {"factor": "coaching_change", "impact": "high", "description": "Head coach was replaced this offseason"},
       {"factor": "snap_pct_declining", "impact": "medium", "description": "Playing time decreased 20% from last season"},
     ],
     "retention_recommendations": [  # actionable suggestions
       "Increase NIL package — player is below team median",
       "Ensure role clarity with new coaching staff",
       "Player's production merits starter-level playing time"
     ]
   }

3. Has a team_flight_risk_report(school, roster_features_df) method:
   - Runs flight risk prediction for every player on the roster
   - Returns a sorted dataframe: player_name, position, flight_risk_score, risk_level, estimated_nil_value, production_score
   - Highlights "critical retention targets": high flight risk AND high production score
   - Estimates "roster impact" if each high-risk player leaves (how many wins would be lost)
   - Saves to outputs/reports/{school}_flight_risk_report.csv

4. Has a train_portal_fit(features_df) method:

   PORTAL FIT MODEL (regression: how well does a portal player fit a school?):
   - Target: transfer_success metric (improvement in production at new school)
   - Train regression models to predict success based on fit features
   - Save to models/portal_prediction/fit_model.joblib

5. Has a predict_portal_fit(player_features, target_school_features) method:
   - Returns a fit score 0-100
   - Returns specific fit factors (positional need, tier match, NIL budget fit, etc.)
   - Returns comparable past transfers that were similar

6. Has a rank_portal_targets(school, school_roster, available_portal_players) method:
   - For a given school, ranks all available portal players by fit score
   - Can filter by position group
   - Returns top recommendations with reasoning
   - Estimates the NIL cost to land each player
   - Saves to outputs/reports/

7. Has a rank_destinations(portal_player_features, schools_list) method:
   - For a given portal player, ranks the best destination schools
   - Considers: fit score, NIL potential, playing time likelihood, team competitiveness, geography
   - Returns ranked list with scores and reasoning
```

### Prompt 12 — Draft Projection Model
```
Write src/models/draft_projector.py with a class DraftProjector:

1. train(features_df) method:

   DRAFT CLASSIFICATION (drafted vs undrafted):
   - Binary classifier
   - Same model training pipeline as other models
   - Save to models/draft_projection/drafted_model.joblib

   DRAFT ROUND PREDICTION (for players predicted as drafted):
   - Treat as regression (round 1-7) or ordinal classification
   - Train regression models predicting draft pick number
   - Convert pick to round and round to value
   - Save to models/draft_projection/round_model.joblib

   Evaluate with: accuracy within 1 round, mean absolute round error, correlation between predicted and actual pick

2. predict(player_features) method returns:
   {
     "player_name": "...",
     "will_be_drafted": True/False,
     "draft_probability": 0.85,
     "projected_round": 2,
     "projected_pick_range": {"early": 33, "mid": 45, "late": 58},
     "comparable_draft_picks": [  # historical players with similar profiles
       {"name": "...", "college": "...", "year": 2023, "pick": 38, "similarity": 0.88}
     ],
     "projected_rookie_contract": {
       "total_value": 8200000,
       "signing_bonus": 3500000,
       "years": 4,
       "fifth_year_option_eligible": False
     },
     "projected_career_earnings_8yr": 45000000,  # rough estimate using position averages by draft slot
     "draft_stock_factors": {  # what helps and hurts
       "helps": ["elite production", "Power 4 conference", "good age (21)"],
       "hurts": ["below average measurables", "one year of starting"]
     },
     "shap_explanation": {}
   }

3. project_nil_from_draft_value(player_features) method:
   - Chains draft projection → career earnings estimate
   - Returns what a player's NIL "should" be relative to their NFL earning potential
   - Logic: agents and families use projected NFL earnings as leverage in NIL negotiations
   - "This player projects as a 2nd rounder worth ~$45M career earnings — their NIL should reflect top-tier status"

4. generate_mock_draft(all_player_features) method:
   - Takes all draft-eligible players
   - Ranks them by predicted draft value
   - Outputs a mock draft board: rank, player, school, position, projected round/pick
   - Saves to outputs/reports/model_mock_draft.csv

5. draft_stock_tracker(player_name, season_stats_by_week) method:
   - If we have weekly/monthly stats, shows how draft projection changes through the season
   - "After week 8, projected Round 1. After week 12 injury, dropped to Round 3."
   - Returns a list of projection snapshots over time
```

### Prompt 13 — Win Impact Model
```
Write src/models/win_model.py with a class WinImpactModel:

1. train(team_data, player_stats, recruiting_data) method:

   TEAM WIN PREDICTION MODEL:
   - Features: returning production percentage (how much of last year's stats come back), recruiting class talent composite, transfer portal net talent gain/loss, coaching tenure and quality estimate, conference strength, recent win trajectory
   - Target: team wins next season
   - Train regression models
   - Evaluate: MAE in wins (goal is within 1-2 wins)
   - Save to models/win_impact/team_win_model.joblib

   PLAYER WIN CONTRIBUTION MODEL:
   - Estimate each player's contribution to team wins
   - Simple approach: calculate the percentage of team offensive/defensive production each player accounts for, multiply by team wins
   - Advanced approach (if data allows): use EPA or points added per player
   - Create a "college WAR" equivalent: wins above replacement, where replacement level is defined as the average production of a fringe starter at that position
   - Save methodology and model

2. predict_team_wins(school, roster_features, incoming_players, outgoing_players) method:
   - Returns projected wins next season
   - Shows the impact of each incoming/outgoing player on the projection
   - Returns confidence interval

3. player_win_value(player_features, team_context) method:
   - Returns estimated wins this player contributes
   - Returns "NIL per win" — their NIL value divided by their win contribution (efficiency metric for collectives)
   - Returns ranking among teammates by win contribution

4. scenario_analysis(school, changes_list) method:
   - Input a list of changes: [{"action": "add", "player": X}, {"action": "remove", "player": Y}]
   - Returns projected wins under each scenario vs baseline
   - This is the killer feature for portal/roster decisions:
     "If we add this portal QB and lose our starting LB, net win impact is +1.5 wins"

5. roster_gap_analysis(school) method:
   - Compares current roster to a "conference championship caliber" roster template
   - Identifies the positions where adding talent would have the highest win impact
   - Prioritizes: "Adding an elite edge rusher projects +1.2 wins, adding a WR projects +0.4 wins"
   - This directly informs where to spend NIL and portal resources
```

### Prompt 14 — Roster Optimizer
```
Write src/models/roster_optimizer.py with a class RosterOptimizer:

1. optimize_nil_budget(school, total_budget, roster_df, win_target=None) method:
   - Given a fixed NIL budget, recommend optimal allocation across players/positions
   - Uses linear programming (PuLP) to maximize total projected wins subject to:
     - Total spend <= budget
     - Each player has a minimum NIL floor (you can't pay a scholarship player $0)
     - Key retention targets have minimum amounts (don't lose your best players)
     - Position group minimums (need at least X starters at each position)
   - If win_target is specified, find the minimum budget needed to hit that target
   - Returns: allocation by player, allocation by position group, projected wins, budget remaining

2. portal_shopping_list(school, roster_df, budget_remaining, positions_of_need=None) method:
   - Uses roster gap analysis + portal fit model to rank portal targets
   - For each target: projected NIL cost, projected win impact, fit score, overall value score
   - Returns a ranked shopping list with estimated total cost to hit win target
   - Can filter by positions_of_need

3. recruiting_roi_analysis(school, recruiting_history, player_outcomes) method:
   - Analyzes historical recruiting: which star ratings produce the best ROI at this specific school?
   - Are 5-stars worth the NIL premium over 4-stars? (varies by school and development program)
   - Which positions has this school developed best?
   - Returns recommendations for recruiting strategy

4. full_roster_report(school) method:
   - Combines everything into one comprehensive report:
     - Current roster valuation (NIL per player)
     - Win projection for next season
     - Flight risk for every player
     - Position-by-position strength assessment
     - Recommended NIL allocation
     - Top portal targets
     - Recruiting priorities
     - Scenario modeling for different strategies
   - Saves to outputs/reports/{school}_full_roster_report.json and .csv
```

---

## Phase 5: API Layer (Integration-Ready for PlaymakerVC)

### Prompt 15 — FastAPI Backend
```
Write src/api/app.py and src/api/routes.py as a FastAPI application:

app.py:
- FastAPI app initialization with title "Portal IQ API", version "1.0.0"
- CORS middleware (allow all origins for development, restrict in production)
- Load all models on startup using @app.on_event("startup")
- Health check endpoint at GET /
- Include router from routes.py

src/api/schemas.py:
- Pydantic models for every request and response body
- Use clear, documented field descriptions
- Include example values

routes.py endpoints:

POST /api/nil/predict
- Input: player profile (name, school, position, stats, social media, recruiting info)
- Output: NIL valuation prediction with full breakdown
- This is the endpoint PlaymakerVC would call to show NIL data on a client profile

POST /api/nil/transfer-impact
- Input: player profile + target school name
- Output: current value, projected value at new school, change

POST /api/nil/market-report
- Input: position group (optional), conference (optional)
- Output: market overview, top players, average values by tier

POST /api/portal/flight-risk
- Input: player profile with team context
- Output: flight risk score and factors

POST /api/portal/team-report
- Input: school name
- Output: full roster flight risk report

POST /api/portal/fit-score
- Input: portal player profile + target school
- Output: fit score and breakdown

POST /api/portal/recommendations
- Input: school name, budget, positions of need
- Output: ranked portal targets

POST /api/draft/project
- Input: player profile
- Output: draft projection with NFL earnings estimate

POST /api/draft/mock
- Input: season year, number of rounds
- Output: full mock draft board

POST /api/roster/optimize
- Input: school name, total NIL budget, win target (optional)
- Output: optimal budget allocation

POST /api/roster/scenario
- Input: school name, list of player adds/removes
- Output: win impact analysis

GET /api/roster/{school}/report
- Output: comprehensive roster report

All endpoints should:
- Return consistent JSON response format: {"status": "success", "data": {...}}
- Handle errors with proper HTTP codes and messages
- Log all requests
- Include response time in headers
- Have OpenAPI documentation with examples

Add API key authentication middleware:
- Check for X-API-Key header
- Validate against keys stored in .env
- Return 401 if missing or invalid
- Skip auth for GET / health check

This API is designed so that PlaymakerVC can integrate it with minimal effort — just HTTP calls with JSON payloads.
```

---

## Phase 6: Dashboard

### Prompt 16 — Streamlit Dashboard
```
Build dashboard/streamlit_app.py as a multi-page Streamlit app:

MAIN PAGE — "Portal IQ"
- Logo area at top (placeholder for now)
- Tagline: "AI-Powered Transfer Portal & NIL Intelligence"
- Quick stats: total players in database, models last updated date, current season
- Navigation to all pages via sidebar

PAGE 1 — dashboard/pages/nil_valuator.py — "NIL Valuator"
- Two modes: "Search Existing Player" (dropdown/search from our data) or "Custom Player Profile" (manual input)
- For custom input: form fields for school, position, stats (position-appropriate), social media follower counts, recruiting stars
- On submit, display:
  - Big number: Predicted NIL Value with confidence range
  - Tier badge: color-coded (Mega=gold, Premium=purple, Solid=blue, Moderate=green, Entry=gray)
  - Donut chart: value breakdown (performance vs social vs school brand vs recruiting vs draft)
  - SHAP waterfall chart: top 10 features
  - Comparable players table
- "Transfer Impact Simulator": dropdown to select a different school, instantly see how value changes. Show a bar chart comparing current vs projected value.
- "Social Media Growth Simulator": sliders for follower growth, show NIL impact in real-time

PAGE 2 — dashboard/pages/portal_intelligence.py — "Portal Intelligence"
- Tab 1: "Roster Flight Risk"
  - Select a school from dropdown
  - Display sortable table of all players: name, position, flight risk score (color-coded red/yellow/green), production score, estimated NIL value
  - Highlight "critical retention targets" in red
  - Summary metrics: number of high-risk players, estimated production at risk, recommended retention budget
- Tab 2: "Portal Player Search"
  - Filter portal players by: position, star rating range, school tier origin, conference
  - For a selected school, show fit scores for each portal player
  - Sortable by: fit score, production score, estimated NIL cost, value score (production per NIL dollar)
- Tab 3: "Portal Fit Analyzer"
  - Select a portal player and a target school
  - Show detailed fit breakdown: positional need, production upgrade, tier match, NIL budget fit, geographic proximity
  - Show comparable past transfers and their outcomes

PAGE 3 — dashboard/pages/draft_tracker.py — "Draft Stock Tracker"
- Search/select a player
- Show: projected round, pick range, NFL position, comparable historical draft picks
- Show projected rookie contract and career earnings estimate
- Show how draft projection connects to NIL value: "This player's NFL earning potential supports a top-tier NIL valuation"
- Table of top draft prospects by position with projected rounds

PAGE 4 — dashboard/pages/roster_builder.py — "Roster Builder"
- Select a school
- Full roster overview with win projection
- "NIL Budget Optimizer": input total budget, see recommended allocation by player and position
- "What If" scenario builder:
  - Add/remove players from the roster
  - See real-time win projection changes
  - See budget impact
- "Shopping List": auto-generated portal and recruiting targets based on roster gaps
- "Roster Report": downloadable full report button (generates CSV and PDF summary)

STYLING:
- Dark theme with green (#00C853) and white accents on dark gray (#1a1a2e) background
- Clean, modern typography
- Use plotly for all interactive charts
- Use st.metric() for big numbers
- Loading spinners during model inference
- Cache model loading with @st.cache_resource
- Cache data loading with @st.cache_data
- Responsive layout using st.columns()
- Sidebar: Portal IQ logo, navigation, "Powered by Elite Sports Solutions" at bottom, data freshness timestamp
```

---

## Phase 7: Testing & Polish

### Prompt 17 — Testing
```
Write comprehensive tests:

tests/conftest.py:
- Pytest fixtures that create sample data for all models
- Sample player features, sample roster, sample team data
- Fixture that loads a small trained model (train on sample data during test setup)

tests/test_data_collection/test_cfb_stats.py:
- Test that CFBStatsCollector initializes without error
- Test that collect_all returns expected dataframe structure (correct columns, no crashes)
- Test caching works (second call uses cache)
- Mock API calls so tests don't hit real API

tests/test_models/test_nil_valuator.py:
- Test that model trains without error on sample data
- Test that predict() returns expected format with all required keys
- Test that predictions are in reasonable ranges (not negative, not billions)
- Test transfer_impact returns valid comparison
- Test what_if_social returns valid output

tests/test_models/test_portal_predictor.py:
- Test flight risk predictions are between 0-100
- Test team report generates for a valid school
- Test portal fit score is between 0-100

tests/test_models/test_draft_projector.py:
- Test draft round predictions are between 1-7
- Test career earnings projections are positive
- Test mock draft generates correct number of picks

tests/test_api/test_routes.py:
- Test all API endpoints return 200 with valid input
- Test all endpoints return proper error codes with invalid input
- Test authentication middleware blocks requests without API key
- Use FastAPI's TestClient

Run with: pytest tests/ -v --tb=short

Also add a scripts/run_pipeline.py that runs the entire pipeline end to end:
1. Collect data (or use cached)
2. Engineer features
3. Train all models
4. Generate sample predictions
5. Save all outputs
6. Print summary of model performance
7. Launch dashboard (optional flag)

Use argparse for flags: --collect-data, --train-models, --predict, --dashboard, --all
```

### Prompt 18 — Documentation & Final Polish
```
Finalize the project:

1. Update README.md with:
   - Project overview and value proposition
   - Architecture diagram (text-based)
   - Screenshots placeholder (TODO)
   - Complete setup instructions:
     a. Clone repo
     b. Create virtual environment
     c. pip install -r requirements.txt
     d. Copy .env.example to .env and add API keys
     e. Run data collection: python scripts/run_pipeline.py --collect-data
     f. Train models: python scripts/run_pipeline.py --train-models
     g. Launch dashboard: python scripts/run_pipeline.py --dashboard
     h. Or run everything: python scripts/run_pipeline.py --all
   - API documentation summary with example curl commands
   - Model performance summary table (placeholder until real training)
   - Integration guide for PlaymakerVC: how to call the API endpoints
   - Future roadmap: real-time portal alerts, automated data refresh, mobile app, PlaymakerVC integration, Cap IQ cross-product features

2. Write METHODOLOGY.md:
   - Data sources and collection methods
   - Feature engineering rationale (why each feature was chosen)
   - Model selection process
   - Known limitations: small training data for NIL, self-reported NIL values may be inaccurate, model assumes past patterns continue
   - Bias considerations: school brand bias in NIL (model may overvalue big-school players), position bias
   - How to update models with new data

3. Add type hints to ALL functions
4. Add Google-style docstrings to ALL classes and public methods
5. Run a linter pass and fix any issues
6. Make sure all file paths use pathlib
7. Make sure all config is loaded from config.yaml (no hardcoded values)
8. Add proper __init__.py files that expose the main classes for clean imports:
   from src.models import NILValuator, PortalPredictor, DraftProjector, WinImpactModel, RosterOptimizer
9. Verify .gitignore covers: .env, data/raw/*, data/cache/*, models/*.joblib, __pycache__, .pytest_cache
10. Create a LICENSE file (choose MIT or Apache 2.0 — your call, but I'd suggest keeping it proprietary since this is a commercial product, so just add "All Rights Reserved - Elite Sports Solutions")
```

---

## Build Order (Do These In This Exact Sequence)

1. **Prompt 1** — Scaffold (10 min)
2. **Prompt 2** — CFB stats collection (test that your API key works)
3. **Prompt 5** — NIL data templates with sample data (so you have something to model against)
4. **Prompt 7** — NIL feature engineering
5. **Prompt 10** — NIL valuation model (your first working model!)
6. **Prompt 16** — Dashboard Page 1 only (see your model in action)
7. **Prompt 3** — Recruiting data
8. **Prompt 4** — Portal data
9. **Prompt 8** — Portal features
10. **Prompt 11** — Portal predictor
11. **Prompt 16** — Dashboard Page 2
12. **Prompt 6** — Draft history
13. **Prompt 9** — Draft features
14. **Prompt 12** — Draft projector
15. **Prompt 13** — Win model
16. **Prompt 14** — Roster optimizer
17. **Prompt 15** — API layer
18. **Prompt 16** — Full dashboard
19. **Prompt 17** — Tests
20. **Prompt 18** — Polish

## Tips for Working in Cursor with Claude Code

- Feed ONE prompt at a time. Don't paste multiple.
- After each prompt, RUN the code and fix any errors before moving to the next.
- If a prompt is too long and Claude Code loses track, split it — give it the method signatures first, then fill in implementations one method at a time.
- Commit to git after each working prompt. You'll want to roll back.
- When you get to the models (Prompts 10-14), you'll need sample data first. That's why Prompt 5 (sample data) comes before the models in the build order.
- The dashboard prompt (16) is long. Feed it one page at a time.
- If data collection scripts fail (API issues, scraping blocked), don't get stuck. Create manual CSV templates and move on to modeling. You can always improve data collection later.
