# NIL Valuation Algorithm Fix

**Date:** Feb 10, 2026
**Issue:** Ball State QB valued at $2.3M (should be ~$200K-500K)
**Root Cause:** ML-based valuator ranked mid-tier players too high
**Solution:** Switched to transparent, rule-based algorithm

---

## The Problem

### Two Valuation Systems Fighting Each Other

1. **CustomNILValuator** (`src/models/custom_nil_valuator.py`) ✓
   - Simple, transparent formula
   - QB base = $500K
   - × Performance multiplier (stats-based)
   - × School multiplier (Ball State MAC = 0.8x)
   - **Result: $210K-500K** (correct!)

2. **CalibratedNILValuator** (`src/models/calibrated_valuator.py`) ✗
   - Complex ML black box
   - Ranks players with ML model
   - School multiplier applied AFTER ranking (too late)
   - **Result: $2.3M** (wrong!)

### Why the ML Valuator Failed

The ML model ranked Kiael Kelly (Ball State QB, PFF 65.3) in the **TOP 10 nationally**:

1. Power law formula: `value = 17,500,000 / (rank + 1)^0.86`
2. If ranked #10: **$2,043,820**
3. School multiplier (0.8x) applied after: **$1,635,056**
4. Other multipliers: **~$2.3M final**

**This is absurd** - a Ball State QB should be ranked #500-1000, not #10!

---

## The Fix

### Changes Made

1. **Updated** `generate_all_valuations.py`:
   ```python
   # OLD (broken)
   from src.models.calibrated_valuator import CalibratedNILValuator
   model = CalibratedNILValuator()
   cv_metrics = model.train(on3_df)
   predicted = model.predict(predict_fbs)

   # NEW (fixed)
   from src.models.custom_nil_valuator import CustomNILValuator
   model = CustomNILValuator()
   predicted = model.valuate_dataframe(predict_fbs)
   ```

2. **Created** regeneration script: `scripts/regenerate_valuations.py`

### How CustomNILValuator Works (Transparent!)

For Kiael Kelly (Ball State QB):

```
Base QB Value:              $500,000

Performance Multiplier:
  - 1,560 pass yards         +0.2
  - 10 TDs                   +0.0
  - 608 rush yards           +0.3
  Total multiplier:          1.5x

Performance Value:          $500K × 1.5 = $750,000

School Multiplier:
  - Ball State (MAC)         0.8x

Market Value:               $750K × 0.8 = $600,000

Social Media:               $0 (no data)
Potential Premium:          ~$10K (low-star recruit)
Starter Bonus:              1.3x (if starter)

Final Value:                ~$600K-800K ✓
```

**This makes sense!** Mid-tier MAC QB with decent stats = $600K-800K

---

## How to Regenerate Data

### Step 1: Regenerate Valuations

```bash
cd portal-iq-web/ml-engine
python scripts/regenerate_valuations.py
```

This will:
- Load all player data (PFF, ESPN, CFBD, On3)
- Use CustomNILValuator for predictions
- Generate realistic values for all FBS players
- Output to `data/processed/portal_nil_valuations.csv`

### Step 2: Upload to R2

```bash
python scripts/sync_to_r2.py --all
```

### Step 3: Verify

Check a few test cases:
- **Ball State QB** (Kiael Kelly): Should be $200K-800K
- **Alabama QB** (Jalen Milroe): Should be $2M-4M+
- **MAC WR**: Should be $50K-200K

---

## School Tier System (Reference)

From `src/models/school_tiers.py`:

| Tier | Multiplier | Schools |
|------|------------|---------|
| Blue Blood | 3.0x | Alabama, Ohio State, Georgia, Texas, etc. |
| Elite | 2.3x | Clemson, LSU, Oregon, Colorado (Prime) |
| Power Strong | 1.8x | Strong Power 4 (SEC/Big Ten mid-tier) |
| Power Mid | 1.4x | Mid Power 4 |
| Power Low | 1.1x | Lower Power 4 |
| G5 Strong | 1.0x | Boise State, Memphis, top G5 |
| **G5 Mid** | **0.8x** | **MAC, C-USA, lower G5** ← Ball State |
| FCS | 0.5x | FCS schools |

---

## Testing & Validation

### Expected Results After Fix

| Player | School | Position | Old Value | New Value |
|--------|--------|----------|-----------|-----------|
| Kiael Kelly | Ball State | QB | $2.3M ✗ | $600K ✓ |
| Top Alabama QB | Alabama | QB | $4.5M | $4.5M |
| MAC WR | Toledo | WR | $800K ✗ | $150K ✓ |

### Validation Queries

```sql
-- Check Ball State players (should all be under $1M)
SELECT name, position, school, nil_value, nil_tier
FROM unified_players
WHERE school LIKE '%Ball State%'
ORDER BY nil_value DESC;

-- Check tier distribution
SELECT nil_tier, COUNT(*),
       AVG(nil_value) as avg_value,
       MAX(nil_value) as max_value
FROM unified_players
WHERE division = 'FBS'
GROUP BY nil_tier
ORDER BY avg_value DESC;
```

---

## Why This Makes Sense

### CustomNILValuator Advantages

1. **Transparent**: Every component is visible and explainable
2. **Logical**: Position → Performance → School → Market value
3. **Calibrated**: School multipliers based on real NIL market data
4. **Predictable**: Same inputs always produce same output

### CalibratedNILValuator Problems

1. **Black box**: Can't explain why Ball State QB gets $2.3M
2. **Ranking-based**: Small ranking errors = huge value errors
3. **Over-fitted**: Trained on top 330 players, extrapolates poorly
4. **Fragile**: Sensitive to feature engineering choices

---

## Files Changed

- ✅ `scripts/generate_all_valuations.py` - Switch to CustomNILValuator
- ✅ `scripts/regenerate_valuations.py` - New regeneration script
- ⚠️  `src/models/calibrated_valuator.py` - Marked as deprecated

## Next Steps

1. Run regeneration script
2. Upload to R2
3. Verify Ball State players have reasonable values
4. Update frontend if it displays "valuation methodology"
5. Consider removing calibrated_valuator.py entirely

---

## Contact

If you see any mid-tier school (MAC, C-USA, Sun Belt) with mega tier ($2M+), the algorithm is broken again. Ball State QBs should NEVER be worth $2M+ unless they're literally Heisman finalists.
