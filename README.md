# Bug Report Accuracy Analyzer

A full-stack web application that helps QA teams measure **testing accuracy** — what percentage of reported bugs in regression testing cycles are actually valid defects vs. duplicates, invalid, or misclassified.

Uses an ML ensemble (TF-IDF + SVM/Logistic Regression) to automatically classify bug reports and detect duplicates via cosine similarity, with a human-in-the-loop review workflow and active learning retraining.

## Features

- **CSV/Excel upload** with auto-detection of Jira, Azure DevOps, or generic column formats
- **ML classification** — SVM + Logistic Regression ensemble with calibrated confidence scores
- **Duplicate detection** — cosine similarity on TF-IDF vectors (threshold 0.92)
- **Review queue** — low-confidence bugs flagged for human review with inline override
- **Active learning** — model retrains automatically after 50 human overrides
- **Interactive dashboard** — global summary, per-project cards, classification donut charts, accuracy bar charts
- **Cycle detail view** — per-tester accuracy, searchable bug table, metrics cards
- **Analytics page** — accuracy/duplicate/invalid trend lines, component breakdown heatmap
- **CSV export** — download classified bug data per cycle

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Jinja2 templates |
| ML | scikit-learn (TF-IDF 250-dim, SVM + LR ensemble) |
| Database | SQLite + SQLAlchemy 2.0 |
| Frontend | Bootstrap 5 + Chart.js |
| Data parsing | pandas (CSV/Excel via openpyxl) |

## Quick Start

```bash
# Clone
git clone https://github.com/Fabiha-9876/BugReportAnalyzer.git
cd BugReportAnalyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate synthetic demo data (3 CSV files)
python3 generate_synthetic_data.py

# Initialize the database
python3 setup_db.py

# Start the server
python3 run.py
```

Open **http://localhost:8001** in your browser.

## Usage

1. **Upload** — Go to `/upload`, select a project (or create one), upload a CSV/Excel file from Jira or Azure DevOps
2. **View results** — The ML pipeline classifies each bug as valid/invalid/duplicate with confidence scores
3. **Review** — Low-confidence bugs appear in the review queue at `/review/{cycle_id}` for human override
4. **Analyze** — View per-cycle metrics at `/cycles/{id}` and cross-cycle trends at `/analytics/{project_id}`
5. **Export** — Download classified results as CSV from the cycle detail page

## Metrics

| Metric | Formula |
|--------|---------|
| Testing Accuracy | valid bugs / total reported |
| Duplicate Rate | duplicate bugs / total |
| Invalid Rate | invalid bugs / total |
| DDE (Defect Detection Effectiveness) | valid unique / (valid + invalid unique) |
| Misclassification Rate | ML disagreements with human / total reviewed |
| Per-tester Accuracy | valid / total per reporter |

## Project Structure

```
BugReportAnalyzer/
├── run.py                       # Uvicorn launcher (port 8001)
├── setup_db.py                  # Database initialization
├── generate_synthetic_data.py   # Demo data generator (3 cycles)
├── requirements.txt
├── configs/
│   └── config.py                # Dataclass config (DB, ML, Ingest, App)
├── src/
│   ├── pipeline.py              # Orchestrator: upload → classify → store
│   ├── api/
│   │   ├── main.py              # FastAPI app, CORS, routes, page handlers
│   │   ├── dependencies.py      # Shared dependencies
│   │   └── routes/              # 7 API route modules
│   ├── db/
│   │   ├── database.py          # Engine, session, Base
│   │   ├── models.py            # 6 ORM tables
│   │   └── crud.py              # Database operations
│   ├── ml/
│   │   ├── preprocessor.py      # Text cleaning (HTML, URLs, stop words)
│   │   ├── feature_extractor.py # TF-IDF vectorizer (250 features)
│   │   ├── duplicate_detector.py# Cosine similarity detection
│   │   ├── classifier.py        # SVM + LR ensemble
│   │   ├── explainer.py         # Feature-importance explanations
│   │   └── active_learner.py    # Retrain after human overrides
│   ├── ingest/
│   │   ├── parser.py            # CSV/Excel with column auto-mapping
│   │   └── normalizer.py        # Field normalization
│   └── metrics/
│       └── calculator.py        # All metric computations
├── templates/                   # 7 Jinja2 HTML templates
├── static/                      # CSS, Chart.js, upload.js
├── data/
│   ├── synthetic/               # Generated demo CSVs
│   └── models/                  # Persisted .joblib models
└── tests/                       # 65 tests (pytest)
```

## Supported Data Sources

| Source | Auto-detected by |
|--------|-----------------|
| **Jira** | `Issue key`, `Summary`, `Component/s` columns |
| **Azure DevOps** | `ID`, `Title`, `Repro Steps`, `Area Path` columns |
| **Generic CSV** | `id`, `summary`, `description` columns |

## ML Pipeline

```
Upload CSV → Parse → Preprocess text → TF-IDF vectorize (250-dim)
                                            │
                         ┌──────────────────┴──────────────────┐
                         │                                      │
                 Duplicate Detector                    Valid/Invalid Classifier
                 (cosine sim ≥ 0.92)                   (SVM + LR ensemble)
                         │                                      │
                    Mark DUPLICATE                     confidence ≥ 0.60?
                                                          ╱         ╲
                                                        YES          NO
                                                         │            │
                                                   Auto-classify   Review Queue
                                                                       │
                                                                 Human overrides
                                                                       │
                                                              50 overrides → Retrain
```

## Running Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

All 65 tests cover: ingestion, preprocessing, feature extraction, duplicate detection, classification, metrics, CRUD operations, API endpoints, active learning, and page routes.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload CSV/Excel file |
| GET/POST | `/api/projects` | List/create projects |
| GET | `/api/projects/{id}` | Get project details |
| GET | `/api/cycles/{project_id}` | List cycles for project |
| GET | `/api/bugs/cycle/{cycle_id}` | List bugs in a cycle |
| GET | `/api/bugs/{id}` | Get bug details |
| POST | `/api/classify/{cycle_id}` | Run ML classification |
| POST | `/api/override/{bug_id}` | Human override classification |
| POST | `/api/retrain` | Trigger model retraining |
| GET | `/api/analytics/cycle/{id}` | Cycle metrics |
| GET | `/api/analytics/project/{id}/trends` | Project trends |
| GET | `/api/export/cycle/{id}` | Export cycle as CSV |

## License

MIT
