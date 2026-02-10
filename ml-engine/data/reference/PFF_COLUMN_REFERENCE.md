# PFF Data Column Reference

**Source**: PFF Data Key Reference Guide (9 Tables)
**Date**: February 10, 2026

This document maps all PFF column headers to their definitions for use in the NIL valuation algorithm.

## Table 1: Basic Identifiers

| Column | Definition |
|--------|------------|
| `#` | Player jersey number (assigned per game/season) |
| `POS` | Primary season position based on snap plurality |
| `#G` | Games Played: Total number of games with at least one snap |
| `SNP` | Total Snaps: Cumulative count of plays where player was on field |
| `TOT` | Total Snaps: Foundational volume metric for participation |
| `PEN` | Total Penalties: Aggregate of all accepted, declined, and offsetting penalties |

## Table 2: Passing Stats (QB)

| Column | Definition | Notes |
|--------|------------|-------|
| `DB` | Dropbacks: Total pass attempts + sacks + scrambles | |
| `ATT` | Attempts: Total forward pass attempts | |
| `COM` | Completions: Total successful pass completions | |
| `COM%` | Completion Percentage: (Completions / Pass Attempts) | |
| `YDS` | Passing Yards: Gross yardage gained via the pass | |
| `YPA` | Yards per Attempt: Mean passing yardage per pass attempt | |
| `TD` | Passing Touchdowns | |
| `INT` | Interceptions | |
| `BTT` | Big-Time Throw: Pass with excellent ball location/timing | PFF Signature Stat |
| `BTT%` | Big-Time Throw Rate: Frequency of BTTs vs total attempts | |
| `TWP` | Turnover-Worthy Play: High chance of INT or fumble | PFF Signature Stat |
| `TWP%` | Turnover-Worthy Play Rate: Frequency vs total dropbacks | |
| `aDoT` | Average Depth of Target: Mean distance downfield | |
| `ADJ%` | Adjusted Completion %: (Completions + Drops) / Aimed Passes | |
| `DRP` | Drops: On-target passes dropped by receiver | |
| `DRP%` | Drop Rate: Frequency of drops | |
| `BAT` | Batted Passes: Deflected by defender at/near LOS | |
| `HAT` | Hit As Thrown: QB contacted during release | |
| `TA` | Thrown Away: Intentionally discarded passes | |
| `DPR` | Total Pressures: Cumulative Sacks + Hits + Hurries | |
| `SK` | Sacks: Times tackled behind LOS | |

## Table 3: Receiving Stats (WR/TE/RB)

| Column | Category | Definition |
|--------|----------|------------|
| `TGT` | Volume | Targets: Total passing attempts aimed at receiver |
| `REC` | Volume | Receptions: Total successful catches |
| `REC%` | Efficiency | Catch Rate: % of targets resulting in reception |
| `YDS` | Volume | Receiving Yards: Total yardage accumulated |
| `Y/REC` | Efficiency | Yards per Reception: Average yardage per catch |
| `YAC` | Efficiency | Yards After Catch: Yardage after securing ball |
| `YAC/REC` | Efficiency | YAC per Reception: Average post-catch yardage |
| `Y/RR` | Efficiency | Yards per Route Run: Total yards / total routes |
| `aDoT` | Efficiency | Average Depth of Target: Mean depth of targeted throws |
| `LNG` | Volume | Longest: Yardage of longest single reception |
| `RTG` | Efficiency | Passer Rating when Targeted: QB rating on throws to receiver |
| `RT%` | Volume | Route Percentage: Frequency of snaps running a route |
| `PB%` | Volume | Pass Block %: % of pass snaps used as blocker |
| `CTT` | Contested | Contested Targets: Targets where defender can play ball |
| `CTC` | Contested | Contested Catches: Catches made in contested situations |
| `CTC%` | Contested | Contested Catch Rate: Efficiency in securing contested targets |
| `MTF` | Efficiency | Missed Tackles Forced: Tackles evaded after catch |
| `SLOT` | Alignment | Total snaps lined up in the slot |
| `SLT%` | Alignment | Percentage of snaps in slot |
| `WIDE` | Alignment | Total snaps lined up as outside receiver |
| `WID%` | Alignment | Percentage of snaps wide |

## Table 4: Rushing Stats (RB/QB)

| Column | Definition | Notes |
|--------|------------|-------|
| `ATT` | Designed Attempts: Rushing attempts scripted by play call | |
| `YDS` | Rushing Yards: Total yardage gained on rushing attempts | |
| `YPA` | Yards per Attempt: Mean yardage per rush | |
| `YCO` | Yards After Contact: Total yardage after first contact | |
| `YCO/A` | Yards After Contact per Attempt: Mean yardage post-contact | |
| `MTF` | Missed Tackles Forced: Number of tackles evaded | |
| `LNG` | Longest: Yardage of longest single run | |
| `10+` | Explosive Runs: Rushing attempts gaining 10+ yards | |
| `D15+` | Breakaway Attempts: Runs of 15+ yards | |
| `BAY` | Breakaway Yardage: Total yardage on 15+ yard runs | |
| `BAY%` | Breakaway Percentage: Portion of yardage from 15+ yard runs | |
| `ELU` | Elusive Rating: Success of runner independent of blocking | PFF Signature Stat |
| `ZONE` | Designed rushing attempts within zone blocking scheme | |
| `GAP` | Designed rushing attempts within gap blocking scheme | |

## Table 5: Blocking Stats (OL/TE)

| Column | Definition |
|--------|------------|
| `BLK` | Total Blocking Snaps: Combined pass and run blocking |
| `RBLK` | Run Block Snaps: Snaps in run blocking role |
| `PBLK` | Pass Block Snaps: Snaps in pass blocking role |
| `OPP` | Allowed Pressure Opportunities: Non-spike, non-penalty pass block snaps |
| `SK` | Sacks Allowed: Sacks attributed to blocker |
| `HIT` | Hits Allowed: QB hits attributed to blocker |
| `HUR` | Hurries Allowed: QB hurries attributed to blocker |
| `PR` | Total Pressures Allowed: Sum of sacks + hits + hurries |
| `EFF` | Pass Blocking Efficiency: Pressure allowed per snap (weighted for sacks) |
| `LT` | Snaps at Left Tackle |
| `LG` | Snaps at Left Guard |
| `C` | Snaps at Center |
| `RG` | Snaps at Right Guard |
| `RT` | Snaps at Right Tackle |
| `ITE` | Snaps at Inline Tight End |

## Table 6: Defensive Stats (DL/LB/DB)

| Column | Definition |
|--------|------------|
| `TOT (Snaps)` | Total Snaps: Cumulative defensive participation |
| `TOT (Pressures)` | Total Pressures: Cumulative Sacks + Hits + Hurries |
| `SK` | Sacks: QB tackles behind LOS |
| `HIT` | Hits: QB hits |
| `HUR` | Hurries: QB hurries |
| `TKL` | Tackles: Total individual tackles |
| `AST` | Assisted Tackles: Total shared defensive stops |
| `MIS` | Missed Tackles: Failed tackle attempts |
| `MIS%` | Missed Tackle Rate: Frequency of missed tackles |
| `STOP` | Defensive Stops: Tackles that constitute offensive "failure" |
| `PBU` | Pass Breakups: Passes deflected or disrupted |
| `LNG` | Longest: Longest reception allowed in primary coverage |
| `FFM` | Forced Fumbles: Total fumbles caused |

## Table 7: Defensive Alignment

| Column | Role | Definition |
|--------|------|------------|
| `DL` | Defensive Line | Snaps on LOS (Interior or Edge) |
| `Box` | Linebacker/Box | Snaps in second level or "box" area |
| `FS` | Free Safety | Snaps in deep safety alignment |
| `Slot` | Nickel | Snaps aligned over slot receiver |
| `Cnr` | Corner | Snaps aligned over outside receiver |
| `AGP` | A-Gap | Nose Tackle alignment (Center-Guard gap) |
| `BGP` | B-Gap | Defensive Tackle alignment (Guard-Tackle gap) |
| `OVT` | Over Tackle | Directly over Offensive Tackle |
| `OUT` | Outside Tackle | Edge defender outside Tackle's frame |

## Table 8: Special Teams

| Phase | Column | Definition |
|-------|--------|------------|
| Return | `KRET` | Kickoff Return Snaps |
| Return | `PRET` | Punt Return Snaps |
| Coverage | `KCOV` | Kickoff Coverage Snaps |
| Coverage | `PCOV` | Punt Coverage Snaps |
| Specialist | `FGBLK` | Field Goal / PAT Block or Rush Snaps |
| Specialist | `FGK` | Field Goal / PAT Kicking Snaps |
| Grades | `SPEC` | PFF Grade for Miscellaneous Special Teams |
| Grades | `KOFF` | PFF Grade for Kicker (kickoffs) or Returner |
| Grades | `PUNT` | PFF Grade for Punter or Returner |
| Grades | `FG` | PFF Grade for Kicker (Field Goals) |

## Table 9: PFF Grade Abbreviations

| Grade Column | Measurement Area | Usage in Valuator |
|--------------|------------------|-------------------|
| `pff_overall` | Overall Player Grade | Fallback for all positions |
| `pff_offense` | Overall Offensive Grade | Offensive players fallback |
| `pff_defense` | Overall Defensive Grade | Defensive players fallback |
| `pff_passing` | Passing Performance | **Primary for QB** |
| `pff_rushing` | Rushing Performance | **Primary for RB** |
| `pff_receiving` | Receiving / Route Running | **Primary for WR/TE** |
| `pff_drop` | Catching and drop frequency | Secondary for WR/TE |
| `pff_fumble` | Ball security and fumbles | Secondary for RB |
| `pff_pass_block` | Pass Blocking Grade | **Primary for OL (pass)** |
| `pff_run_block` | Run Blocking Grade | **Primary for OL (run)** |
| `pff_run_defense` | Run Defense Grade | **Primary for LB** |
| `pff_tackling` | Tackling Grade | Secondary for LB/S |
| `pff_pass_rush` | Pass Rush Grade | **Primary for DL/ED** |
| `pff_coverage` | Defensive Coverage Grade | **Primary for CB/S** |
| `pff_special` | Special Teams Grade | Specialists only |

## Column Mapping for NIL Valuator

**Current CSV Columns → Valuator Parameters:**

### Passing (QB)
- `completion_pct` → N/A (not used)
- `passer_rating` → N/A (not used)
- `big_time_throw_pct` → N/A (not used)
- `turnover_worthy_play_pct` → N/A (not used)
- `avg_depth_of_target` → N/A (not used)
- `pressure_grades_pass` → N/A (not used)
- **`yards` → `passing_yards`** (inferred for QB position)
- **`touchdowns` → `passing_tds`** (inferred for QB position)
- **`pff_passing` → `pff_grade`** (primary for QB)

### Rushing (RB)
- `elusive_rating` → N/A (not used)
- `yaco_per_attempt` → N/A (not used)
- `breakaway_pct` → N/A (not used)
- `breakaway_yards` → N/A (not used)
- `missed_tackles_forced` → N/A (not used)
- **`yards` → `rushing_yards`** (inferred for RB position)
- **`touchdowns` → `rushing_tds`** (inferred for RB position)
- **`pff_rushing` → `pff_grade`** (primary for RB)

### Receiving (WR/TE)
- `yards_per_route_run` → N/A (not used)
- `drop_rate` → N/A (not used)
- `contested_catch_rate` → N/A (not used)
- `targeted_qb_rating` → N/A (not used)
- `targets` → N/A (not used)
- `receptions` → N/A (not used)
- **`rec_yards` → `receiving_yards`**
- **`touchdowns` → `receiving_tds`** (inferred for WR/TE position)
- **`pff_receiving` → `pff_grade`** (primary for WR/TE)

### Defensive (DL/LB/CB/S)
- `pass_rush_win_rate` → N/A (not used)
- `pass_rushing_productivity` → N/A (not used)
- `pressures` → N/A (not used)
- **`sacks` → `sacks`**
- `hurries` → N/A (not used)
- `forced_incompletion_rate` → N/A (not used)
- `passer_rating_allowed` → N/A (not used)
- `yards_per_coverage_snap` → N/A (not used)
- **`tackles` → `tackles`**
- `missed_tackle_rate` → N/A (not used)
- **`pff_coverage` → `pff_grade`** (primary for CB/S)
- **`pff_pass_rush` → `pff_grade`** (primary for DL/ED)
- **`pff_run_defense` → `pff_grade`** (primary for LB)

### Blocking (OL)
- `pass_blocking_efficiency` → N/A (not used)
- `pressures_allowed` → N/A (not used)
- `true_pass_set_pbe` → N/A (not used)
- **`pff_pass_block` → `pff_grade`** (primary for OL pass)
- **`pff_run_block` → `pff_grade`** (primary for OL run)

## Notes

1. **Grade Priority Order** (in CustomNILValuator):
   - Position-specific grade (e.g., `pff_passing` for QB)
   - Position group grade (e.g., `pff_offense` for offensive players)
   - Overall grade (`pff_overall`)

2. **Missing Data**:
   - Interceptions: Not available in CSV
   - Social media followers: Not available in CSV
   - Starter status: Not available in CSV
   - Years remaining: Not available in CSV

3. **Position Inference**:
   - Generic `yards` and `touchdowns` columns are interpreted based on position
   - QB: yards = passing, TDs = passing
   - RB: yards = rushing, TDs = rushing
   - WR/TE: yards = receiving (from `rec_yards`), TDs = receiving

4. **PFF Grades Range**: 0-100 scale where:
   - 90+: Elite
   - 80-89: Great
   - 70-79: Good
   - 60-69: Above Average
   - 50-59: Average
   - Below 50: Below Average
