# Portal IQ NIL Valuation Algorithm
## How We Predict What Players Are Really Worth

---

## The Problem With Existing NIL Valuations

On3 and other platforms base their valuations heavily on **social media followers**. This creates problems:

- A player with 500K TikTok followers but average on-field production gets valued higher than an elite lineman
- It rewards viral moments over actual football ability
- It doesn't help you find *undervalued* players in the transfer portal
- Social media can be gamed with purchased followers

**Our approach is different.** We focus on the factors that actually predict on-field impact and long-term NIL earning potential.

---

## What Our Algorithm Uses (And Why It Matters)

### 1. School/Program Tier (Weight: ~25%)

**What it is:** We rank every FBS program into tiers (1-6) based on portal class strength, historical performance, and NIL collective investment.

**Why it matters:**
- Players at top programs have more exposure (national TV games, bigger stadiums)
- Blue blood schools have stronger NIL collectives with more money to spend
- Brand association matters - an Alabama QB vs. a MAC QB doing the same NIL deal

**Example:** A 4-star WR at Ohio State has a higher floor than the same player at Bowling Green, simply because of media market and NIL infrastructure.

---

### 2. Position Value (Weight: ~20%)

**What it is:** A position-specific multiplier based on market demand and win impact.

| Position | Value Factor | Reasoning |
|----------|--------------|-----------|
| QB | 1.0 (highest) | Touches ball every play, face of the franchise |
| EDGE | 0.8 | Premier pass rushers are game-changers |
| WR | 0.8 | High-profile, highlight-reel positions |
| CB | 0.7 | Elite corners shutdown half the field |
| OT | 0.7 | Protect the QB, critical for passing game |
| RB | 0.6 | High production but shorter shelf life |
| LB | 0.55 | Important but less position scarcity |
| K/P | 0.2 | Limited marketability despite game impact |

**Why it matters:**
- Quarterbacks earn 5-10x more NIL than other positions
- Position scarcity drives value - elite EDGE rushers are rare
- This reflects what NIL collectives actually pay

---

### 3. Recruiting Pedigree (Weight: ~20%)

**What it is:** 247Sports composite star rating (2-5 stars) and national ranking.

**Why it matters:**
- High school recruiting rankings are the best predictor of NFL draft success
- 5-star players have proven they can perform against elite competition
- Even if a player transfers, their recruiting ranking follows them
- It's a talent indicator independent of current team performance

**The data backs this up:**
- 5-star recruits are drafted at 10x the rate of 3-stars
- 4-5 star transfers command higher NIL deals at their destination school

---

### 4. Social Media / Marketability (Weight: ~15%)

**What it is:** Follower counts, engagement, and platform presence.

**Why it matters:**
- NIL deals often include social media obligations
- Follower count indicates existing audience for sponsors
- BUT we weight this LESS than On3 does

**Our twist:** We approximate social reach from school tier and recruiting status for players without known social data. A 5-star at Georgia probably has more followers than a 3-star at Tulane, even if we can't verify exact counts.

---

### 5. Performance/Rank Score (Weight: ~20%)

**What it is:** National ranking among all players (for known NIL-ranked players) or implied ranking based on school + position + stars.

**Why it matters:**
- Top-100 national players get more attention from NIL collectives
- On-field production validates recruiting hype
- Helps identify breakout players who've exceeded expectations

---

## How The Algorithm Works Together

```
NIL Valuation = Base Value (from position)
              × School Tier Multiplier
              × Recruiting Star Multiplier
              × Social/Rank Bonus
              + Adjustments
```

**Example: 4-Star QB at Georgia**
- Position: QB = 1.0 (highest base)
- School Tier: 6 (top tier)
- Stars: 4 = 1.3x multiplier
- Result: High-6-figure to 7-figure valuation

**Example: 3-Star OL at MAC school**
- Position: OL = 0.55 (lower base)
- School Tier: 2 (lower tier)
- Stars: 3 = 1.0x multiplier
- Result: Low 5-figure valuation

---

## Why This Beats Social Media-Only Models

### 1. **Finds Undervalued Players**
Our model can identify players whose NIL value doesn't match their on-field impact. A dominant left tackle might only have 2,000 Instagram followers but could be worth $200K+ in actual NIL.

### 2. **Predicts Future Value**
Social media lags performance. A true freshman who becomes a starter will see their NIL value increase - we can project this before it happens.

### 3. **Helps You Budget**
If you're an NIL collective, you need to know what players are *actually worth* in the market - not what their follower count suggests. Our model helps you make competitive offers without overpaying.

### 4. **Transfer Portal Advantage**
When a player enters the portal, you need to know their value quickly. Our model considers their origin school, recruiting profile, and likely destinations to give you actionable valuations.

---

## Model Accuracy & Validation

We trained our model on **real On3 NIL valuations** for thousands of players, then tested it on players the model hadn't seen.

| Metric | Value | What It Means |
|--------|-------|---------------|
| R² Score | 0.745 | Model explains ~75% of NIL value variance |
| Mean Absolute Error | $134,880 | Average prediction is within $135K |
| Tier Accuracy | >80% | Correctly classifies mega/premium/solid/moderate/entry |

**Why these numbers matter:**
- R² of 0.75 is strong for predicting market behavior
- $135K MAE is acceptable when valuations range from $10K to $10M+
- Tier classification is what matters for decision-making - you need to know if a player is a $500K or $50K guy

---

## What Makes Us Different From On3

| Factor | On3 | Portal IQ |
|--------|-----|-----------|
| **Social Media Weight** | Heavy (~50%+) | Moderate (~15%) |
| **On-Field Factors** | Light | Heavy (~40%+) |
| **School/Market** | Included | Heavily weighted |
| **Transfer Portal Focus** | General | Specialized |
| **Custom Predictions** | No | Yes - for any player |
| **Actionable for NIL Ops** | Limited | Built for this |

---

## Use Cases

### For NIL Collectives
"We need to know what to offer a 4-star WR transferring from Oregon. What's the market rate?"

Our model gives you a data-backed number based on comparable players, position value, and destination school factors.

### For Athletic Departments
"Which of our current players are undervalued vs. the market? Who's a flight risk?"

Compare our valuations against what players are actually earning to identify retention risks.

### For Agents/Representatives
"What should my client realistically expect for NIL deals?"

Get market-rate estimates based on factors sponsors and collectives actually care about.

---

## Summary: Why Our Algorithm Is Defensible

1. **Based on Real Data** - Trained on actual On3 valuations from thousands of players
2. **Uses Proven Factors** - Position value, recruiting rankings, and school tier are established predictors
3. **Less Gameable** - You can't buy a higher star rating like you can buy followers
4. **Validated** - 75% explanatory power with real-world backtesting
5. **Actionable** - Designed for NIL operations, not just rankings

---

*Portal IQ - AI-Powered Transfer Portal & NIL Intelligence*
*Elite Sports Solutions*
