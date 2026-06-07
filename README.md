# WikiMod

**Wikipedia Talk Page Toxicity Monitor** - ML-powered analysis of discussion health on Wikipedia talk pages.

*This is a portfolio project built to demonstrate ML model deployment, NLP, third-party API integration, responsible AI practices, and fullstack application development.*

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![React](https://img.shields.io/badge/React-18-61dafb)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Why This Exists

Motivated by research showing that toxic comments make Wikipedia newcomers 1.8x more likely to stop editing (Wulczyn et al., 2023), this project applies NLP techniques to surface discussion health patterns that existing moderation tools miss.

WikiMod fetches Wikipedia talk page content via the MediaWiki API, runs each comment through a toxicity classifier trained on the Jigsaw dataset, and presents the results in an interactive dashboard showing:

- **Page Health Score** - overall discussion health as a percentage
- **Per-comment Toxicity Scores** - with word-level attribution highlighting trigger words
- **Conversation Escalation Detection** - identifies sections where toxicity is trending upward
- **Section Comparison** - highlights the healthiest vs. most heated sections
- **Historical Tracking** - monitors how page health changes over time
- **Model Transparency** - full disclosure of model metrics, limitations, and biases

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy, PostgreSQL |
| ML | scikit-learn (Logistic Regression + TF-IDF) |
| Data Source | MediaWiki API, mwparserfromhell |
| Frontend | React 18, TypeScript, Recharts, TailwindCSS |
| Infrastructure | Docker Compose, Vite |

## Architecture

```
Wikipedia Article URL
        |
        v
  MediaWiki API Client -----> Talk Page Wikitext
        |
        v
  Comment Parser (mwparserfromhell / DiscussionTools API)
        |
        v
  Toxicity Classifier (LogReg + TF-IDF)
        |
        v
  Analysis Orchestrator
   /    |    \
  v     v     v
Health  Escalation  Word
Score   Detection   Attribution
  \     |     /
   v    v    v
  PostgreSQL Storage
        |
        v
  REST API (FastAPI)
        |
        v
  React Dashboard
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, for full setup)

### Quick Start (Docker)

```bash
git clone https://github.com/naeema-scopes/wikimod.git
cd wikimod
docker compose up
```

The Docker entrypoint automatically downloads pre-trained model artifacts from the GitHub Release.

### Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Download or train the model
bash scripts/download_model.sh
# OR train on synthetic data for development:
python -m app.ml.train --synthetic

# Run the server
uvicorn app.main:app --reload

# Run tests
pytest
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev    # Development server
npm test       # Run tests
```

### Training the Model

The toxicity classifier can be trained in two modes:

1. **Synthetic data** (for development/demo):
   ```bash
   python -m app.ml.train --synthetic
   ```

2. **Full Jigsaw dataset** (for production):
   - Download from [Kaggle](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge)
   - Place `train.csv` in `backend/data/`
   - Run: `python -m app.ml.train --data-path backend/data/`

## API Documentation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/analyze` | POST | Analyze a Wikipedia talk page |
| `/api/analyze/{id}` | GET | Retrieve a stored analysis |
| `/api/history` | GET | List all historical scans |
| `/api/history/{page_title}` | GET | History for a specific page |
| `/api/model/metrics` | GET | Model evaluation metrics |
| `/api/model/limitations` | GET | Known limitations and biases |

### Example Request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change"}'
```

## Model Transparency

The toxicity classifier is a logistic regression model with TF-IDF features. Key details:

- **Training data**: Jigsaw Toxic Comment Classification dataset (2015-2017 Wikipedia discussions)
- **Binary classification**: Comments are labeled toxic if any of the six Jigsaw labels (toxic, severe_toxic, obscene, threat, insult, identity_hate) is positive
- **Word attribution**: Uses model coefficients * TF-IDF weights to identify trigger words

### Known Limitations

- **Identity term bias**: May flag comments containing identity terms (e.g., "gay", "Muslim") as toxic
- **Adversarial evasion**: Obfuscated slurs (leetspeak, Unicode substitutions) likely evade detection
- **Temporal bias**: Training data from 2015-2017 may not reflect current language patterns
- **Context blindness**: Each comment is scored in isolation, without conversational context
- **False positive harm**: Incorrect flags can discourage good-faith contributors

See the in-app Model Info page for complete details.

## References

- Jigsaw Toxic Comment Classification Challenge: https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge
- Wulczyn, E., Thain, N., & Dixon, L. (2023). *Ex Machina: Personal Attacks Seen at Scale*
- Borkan, D., et al. (2019). *Nuanced Metrics for Measuring Unintended Bias with Real Data for Text Classification*

## License

MIT
