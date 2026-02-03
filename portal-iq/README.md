# Portal IQ

**AI-powered transfer portal and NIL intelligence platform for college football programs, NIL collectives, agents, and analysts.**

Built by Elite Sports Solutions.

---

## Overview

Portal IQ is a comprehensive analytics platform that leverages machine learning to provide actionable intelligence for the modern college football landscape. As the transfer portal and NIL have transformed college athletics, Portal IQ helps stakeholders make data-driven decisions about player valuations, roster construction, and talent acquisition.

The platform integrates data from multiple sources to deliver:
- Real-time NIL market valuations
- Transfer portal predictions and tracking
- NFL draft projections
- Roster optimization recommendations

---

## Features

### NIL Valuation

- **Market-Based Valuations**: ML models trained on actual NIL deals to estimate fair market value for any player
- **Position & School Adjustments**: Accounts for position scarcity and school brand value
- **Social Media Integration**: Incorporates follower counts and engagement rates
- **Tier Classification**: Categorizes players into NIL tiers (Mega, Premium, Solid, Moderate, Entry)
- **Confidence Intervals**: Provides valuation ranges to account for market uncertainty

### Portal Intelligence

- **Entry Prediction**: Identifies players at risk of entering the transfer portal
- **Destination Modeling**: Predicts likely landing spots for portal entrants
- **Risk Factor Analysis**: Highlights factors contributing to portal risk (playing time, coaching changes, NIL gaps)
- **Team Activity Tracking**: Monitors incoming and outgoing transfers by school
- **Real-Time Updates**: Tracks portal entries and commitments as they happen

### Draft Projection

- **Draft Probability**: Estimates likelihood of being drafted
- **Pick Projection**: Predicts draft round and overall pick
- **Historical Comparisons**: Matches prospects to similar historical players
- **Career Value Estimation**: Projects rookie contracts and career earnings potential
- **Combine Integration**: Incorporates athletic testing data when available

### Roster Optimization

- **Budget-Constrained Optimization**: Maximizes roster value within NIL budget
- **Position Need Analysis**: Identifies depth chart gaps and priorities
- **Win Impact Modeling**: Estimates win contribution of roster changes
- **Trade Evaluation**: Assesses potential player swaps and acquisitions
- **Season Projection**: Forecasts team performance based on roster composition

---

## Setup

### Prerequisites

- Python 3.10+
- pip or conda package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/elite-sports-solutions/portal-iq.git
cd portal-iq
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Get a CFBD API key:
   - Visit https://collegefootballdata.com/key
   - Sign up for a free API key
   - Add it to your `.env` file

---

## Usage

### Running the Dashboard

```bash
cd dashboard
streamlit run streamlit_app.py
```

The dashboard will be available at `http://localhost:8501`

### Running the API

```bash
uvicorn src.api.app:app --reload
```

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Using the Python Library

```python
from src.models import NILValuator, PortalPredictor, DraftProjector
from src.utils import Config

# Initialize with config
config = Config()

# NIL Valuation
valuator = NILValuator(config)
valuation = valuator.value_player({
    "player_name": "John Smith",
    "position": "QB",
    "school": "Alabama",
    "social_followers": 150000,
})
print(f"Estimated NIL Value: ${valuation['valuation']:,.0f}")

# Portal Prediction
predictor = PortalPredictor(config)
# ... train model with historical data
risk = predictor.get_at_risk_players(roster_df, threshold=0.5)

# Draft Projection
projector = DraftProjector(config)
# ... train model with draft history
projection = projector.predict(player_features)
```

### Running Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
portal-iq/
├── data/                   # Data storage
│   ├── raw/               # Raw data files
│   ├── processed/         # Processed datasets
│   └── cache/             # Cached API responses
├── models/                 # Trained model artifacts
│   ├── nil_valuation/
│   ├── portal_prediction/
│   ├── draft_projection/
│   └── win_impact/
├── src/                    # Source code
│   ├── data_collection/   # Data collectors
│   ├── feature_engineering/ # Feature pipelines
│   ├── models/            # ML models
│   ├── api/               # FastAPI application
│   └── utils/             # Utilities
├── dashboard/              # Streamlit dashboard
│   └── pages/             # Dashboard pages
├── outputs/                # Generated outputs
│   ├── reports/
│   └── figures/
├── tests/                  # Test suite
├── requirements.txt
├── config.yaml
└── README.md
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/nil/valuate` | POST | Get NIL valuation for a player |
| `/api/v1/nil/leaderboard` | GET | Get top players by NIL value |
| `/api/v1/portal/predict` | POST | Predict portal entry/destination |
| `/api/v1/portal/active` | GET | Get active portal players |
| `/api/v1/draft/project` | POST | Get draft projection |
| `/api/v1/draft/board` | GET | Get draft board rankings |
| `/api/v1/roster/optimize` | POST | Optimize portal targets |
| `/api/v1/roster/{team}` | GET | Get team roster |

---

## Configuration

Edit `config.yaml` to customize:
- School tier classifications
- NIL tier thresholds
- Model hyperparameters
- Data paths

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Proprietary - Elite Sports Solutions. All rights reserved.

---

## Contact

Elite Sports Solutions
- Website: https://elitesportssolutions.com
- Email: info@elitesportssolutions.com

---

*Portal IQ - Making smarter decisions in the NIL era.*
