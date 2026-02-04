# Portal IQ Data Update Guide

## Quick Commands

```bash
# Full update (health check + PFF + CFBD + validation)
python scripts/update_portal_iq_data.py

# Or use the batch file (Windows)
scripts\update_data.bat

# Dry run - see what would happen without changes
python scripts/update_portal_iq_data.py --dry-run

# Just check data health
python scripts/update_portal_iq_data.py --check

# Only PFF import (after downloading new CSV)
python scripts/update_portal_iq_data.py --pff-only

# Only CFBD roster refresh
python scripts/update_portal_iq_data.py --cfbd-only
```

---

## What Gets Automated

| Task | Automated? | Notes |
|------|------------|-------|
| PFF import to PocketBase | ✅ Yes | Requires CSV to be downloaded first |
| CFBD roster refresh | ✅ Yes | Uses API key from .env |
| Data validation | ✅ Yes | Checks integrity and freshness |
| Health checks | ✅ Yes | PocketBase connection, file ages |

---

## Manual Tasks Checklist

### Weekly (During Season)
- [ ] Download PFF grades CSV from https://premium.pff.com/
- [ ] Save to: `ml-engine/data/processed/pff_player_grades.csv`
- [ ] Run: `python scripts/update_portal_iq_data.py`

### Monthly (Off-Season)
- [ ] Check On3 NIL rankings for updates
- [ ] Download fresh PFF CSV if available
- [ ] Run update script

### Pre-Season (July-August)
- [ ] Download full PFF archive for new season
- [ ] Verify all data sources are current
- [ ] Full data refresh

---

## Logs

All update logs are saved to:
```
logs/data_update_YYYYMMDD_HHMMSS.log
logs/update_results_YYYYMMDD_HHMMSS.json
```

---

## Windows Task Scheduler (Optional)

To run automatically every week:

1. Open Task Scheduler
2. Create Basic Task → Name: "Portal IQ Data Update"
3. Trigger: Weekly (pick a day like Tuesday)
4. Action: Start a Program
5. Program: `python`
6. Arguments: `scripts/update_portal_iq_data.py`
7. Start in: `C:\Users\kerra\Downloads\files`

Note: This will run the automated parts. You still need to manually download PFF CSV.
