# Bug Report Accuracy Analyzer - Technical Documentation

## 1. Introduction

### 1.1 Problem Statement

In software QA, regression testing cycles generate large volumes of bug reports. However, not all reported bugs are genuine defects — many are **duplicates** of existing reports, **invalid** (caused by user error, environment issues, or misunderstandings), or **misclassified** (e.g., feature requests filed as bugs). Without measuring this, QA managers have no visibility into their team's *testing accuracy* — the ratio of valid defects to total reports.

Manual classification is time-consuming and inconsistent. Teams need an automated, data-driven way to:
- Classify bug reports as valid, invalid, or duplicate
- Measure testing accuracy per cycle, per tester, and per component
- Track quality trends across regression cycles
- Identify testers who need coaching and components with recurring issues

### 1.2 Solution Overview

The Bug Report Accuracy Analyzer is a web application that automates bug report classification using a machine learning ensemble (SVM + Logistic Regression on TF-IDF features) combined with cosine-similarity duplicate detection. It provides an interactive dashboard for QA teams to upload data, review classifications, override ML predictions, and analyze accuracy metrics over time.

### 1.3 Research Foundation

The system's design draws from 5 key areas of bug report classification research:

1. **Text-based classification** — TF-IDF vectorization captures the semantic content of bug summaries and descriptions, enabling statistical classifiers to distinguish valid defects from noise.
2. **Ensemble methods** — Combining SVM (good at margin-based separation) with Logistic Regression (good at probability estimation) produces more robust predictions than either model alone.
3. **Duplicate detection** — Cosine similarity on TF-IDF vectors identifies semantically similar reports, a well-established technique in information retrieval.
4. **Active learning** — Human-in-the-loop overrides feed back into the model, improving accuracy over time with minimal labeling effort.
5. **Confidence-based triage** — Routing low-confidence predictions to human reviewers optimizes the trade-off between automation and accuracy.

---

## 2. Architecture

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser                             │
│  Dashboard │ Upload │ Cycle Detail │ Review │ Analytics      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────┴──────────────────────────────────┐
│                    FastAPI Application                        │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Jinja2       │  │ API Routes   │  │ Static Files      │   │
│  │ Templates    │  │ (7 modules)  │  │ (CSS, JS, Charts) │   │
│  └─────────────┘  └──────┬───────┘  └───────────────────┘   │
│                          │                                    │
│  ┌───────────────────────┴────────────────────────────────┐  │
│  │                    Pipeline Orchestrator                │  │
│  │  Ingest → Preprocess → Feature Extract → Classify      │  │
│  └───────────────────────┬────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────┐  ┌────────┴────────┐  ┌───────────────────┐   │
│  │ SQLite   │  │ ML Components   │  │ Metrics Engine    │   │
│  │ Database │  │ (6 modules)     │  │                   │   │
│  └──────────┘  └─────────────────┘  └───────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | FastAPI 0.104+ | REST API + page routes |
| **Templating** | Jinja2 3.1+ | Server-side HTML rendering |
| **Database** | SQLite + SQLAlchemy 2.0 | Persistent storage with ORM |
| **ML Framework** | scikit-learn 1.3+ | Classification and feature extraction |
| **Text Processing** | NLTK (optional), BeautifulSoup | Lemmatization, HTML stripping |
| **Data Parsing** | pandas 2.1+ | CSV/Excel file parsing |
| **Frontend** | Bootstrap 5.3, Chart.js 4.4 | UI components and charts |
| **Server** | Uvicorn | ASGI server with hot reload |

### 2.3 Directory Structure

```
BugReportAnalyzer/
├── run.py                          # Entry point — starts Uvicorn on port 8001
├── setup_db.py                     # Creates tables + seeds default data
├── generate_synthetic_data.py      # Generates 3 demo CSV files
├── requirements.txt                # Python dependencies
│
├── configs/
│   └── config.py                   # Centralized configuration (dataclasses)
│
├── src/
│   ├── pipeline.py                 # Orchestrator tying all components together
│   │
│   ├── api/
│   │   ├── main.py                 # FastAPI app, middleware, page routes
│   │   ├── dependencies.py         # Shared FastAPI Depends
│   │   └── routes/
│   │       ├── upload.py           # POST /api/upload
│   │       ├── projects.py         # CRUD /api/projects
│   │       ├── cycles.py           # CRUD /api/cycles
│   │       ├── bugs.py             # CRUD /api/bugs
│   │       ├── classification.py   # /api/classify, /api/override, /api/retrain
│   │       ├── analytics.py        # /api/analytics/*
│   │       └── export.py           # /api/export/* (CSV downloads)
│   │
│   ├── db/
│   │   ├── database.py             # Engine, SessionLocal, Base, get_db
│   │   ├── models.py               # 6 ORM models
│   │   └── crud.py                 # All database operations
│   │
│   ├── ml/
│   │   ├── preprocessor.py         # Text cleaning pipeline
│   │   ├── feature_extractor.py    # TF-IDF vectorizer wrapper
│   │   ├── duplicate_detector.py   # Cosine similarity detection
│   │   ├── classifier.py           # SVM + LR ensemble
│   │   ├── explainer.py            # Human-readable classification explanations
│   │   └── active_learner.py       # Retrain trigger on human overrides
│   │
│   ├── ingest/
│   │   ├── parser.py               # CSV/Excel parsing + column auto-mapping
│   │   └── normalizer.py           # Field standardization
│   │
│   └── metrics/
│       └── calculator.py           # All metric computations
│
├── templates/                      # 7 Jinja2 HTML templates
│   ├── base.html                   # Shared layout (nav, footer, scripts)
│   ├── dashboard.html              # Main dashboard with global summary
│   ├── upload.html                 # File upload with drag-drop
│   ├── cycle_detail.html           # Per-cycle metrics and bug table
│   ├── bug_detail.html             # Individual bug info + override form
│   ├── review_queue.html           # Low-confidence bugs for human review
│   └── analytics.html              # Cross-cycle trend charts
│
├── static/
│   ├── css/style.css               # Custom styles
│   └── js/
│       ├── chart.umd.min.js        # Chart.js 4.4.1 (local copy)
│       ├── charts.js               # Chart rendering functions
│       └── upload.js               # Upload page interactivity
│
├── data/
│   ├── synthetic/                  # 3 generated demo CSV files
│   │   ├── regression_cycle_1.csv  # 120 bugs (~30% invalid, ~12% duplicate)
│   │   ├── regression_cycle_2.csv  # 100 bugs (~20% invalid, ~10% duplicate)
│   │   └── regression_cycle_3.csv  #  90 bugs (~15% invalid, ~8% duplicate)
│   └── models/                     # Persisted ML models (.joblib)
│
└── tests/                          # 65 pytest tests across 9 files
```

---

## 3. Database Schema

### 3.1 Entity Relationship Diagram

```
┌──────────┐       ┌───────────────────┐       ┌──────────────┐
│ projects │──1:N──│ regression_cycles  │──1:N──│ bug_reports   │
└──────────┘       └───────────────────┘       └───────┬──────┘
                                                       │
                                                 1:N   │  self-FK
                                                       │  (duplicate_of)
                                            ┌──────────┴─────────┐
                                            │ classification_    │
                                            │ audit_log          │
                                            └────────────────────┘

┌─────────────────┐     ┌──────────┐
│ model_versions  │     │  users   │
└─────────────────┘     └──────────┘
```

### 3.2 Table Definitions

#### projects
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| name | VARCHAR(255) | Unique project name |
| description | TEXT | Optional description |
| created_at | DATETIME | UTC timestamp |
| updated_at | DATETIME | Auto-updated on change |

#### regression_cycles
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| project_id | INTEGER FK | References projects.id |
| name | VARCHAR(255) | Cycle name (e.g., "Sprint 23 Regression") |
| start_date | DATETIME | Optional cycle start |
| end_date | DATETIME | Optional cycle end |
| source_system | VARCHAR(50) | "jira", "azure_devops", or "generic" |
| upload_file_name | VARCHAR(255) | Original filename |
| created_at | DATETIME | UTC timestamp |

#### bug_reports
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| cycle_id | INTEGER FK | References regression_cycles.id |
| external_id | VARCHAR(100) | ID from source system (e.g., "PROJ-123") |
| summary | TEXT | Bug title/summary (required) |
| description | TEXT | Full description |
| status | VARCHAR(50) | Open, Closed, Resolved, etc. |
| priority | VARCHAR(50) | Critical, Major, Minor, Trivial |
| severity | VARCHAR(50) | Severity level |
| component | VARCHAR(255) | Software component |
| reporter | VARCHAR(255) | Person who filed the bug |
| assignee | VARCHAR(255) | Person assigned to fix |
| created_date | DATETIME | When bug was filed |
| resolved_date | DATETIME | When bug was resolved |
| resolution | VARCHAR(100) | Fixed, Won't Fix, Duplicate, etc. |
| labels | TEXT | Comma-separated tags |
| original_type | VARCHAR(100) | Issue type from source (Bug, Task, etc.) |
| **ml_classification** | VARCHAR(50) | ML prediction: valid/invalid/duplicate |
| **ml_confidence** | FLOAT | Prediction confidence (0.0–1.0) |
| **ml_explanation** | TEXT | Human-readable explanation of the prediction |
| **duplicate_of_id** | INTEGER FK | Self-reference to the original bug |
| **duplicate_similarity** | FLOAT | Cosine similarity score |
| **tfidf_vector_json** | JSON | Stored TF-IDF vector for reuse |
| **final_classification** | VARCHAR(50) | Authoritative label (ML or human override) |
| **classification_source** | VARCHAR(20) | "ml" or "human" |
| **reviewed** | BOOLEAN | Whether a human has reviewed this bug |
| **reviewed_by** | VARCHAR(255) | Reviewer username |
| **override_reason** | TEXT | Why the human disagreed with ML |

**Design note**: `ml_classification` stores the raw ML prediction. `final_classification` stores the authoritative label — it defaults to the ML prediction but can be overridden by a human reviewer. All metrics and display logic read from `final_classification`.

#### classification_audit_log
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| bug_id | INTEGER FK | References bug_reports.id |
| previous_classification | VARCHAR(50) | Before the change |
| new_classification | VARCHAR(50) | After the change |
| source | VARCHAR(20) | "ml" or "human" |
| changed_by | VARCHAR(255) | Username of the changer |
| reason | TEXT | Reason for the override |
| timestamp | DATETIME | UTC timestamp |

#### model_versions
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| version | VARCHAR(50) | Version tag (e.g., "v1", "v2") |
| trained_at | DATETIME | When the model was trained |
| training_samples | INTEGER | Number of samples used |
| accuracy | FLOAT | Cross-validation accuracy |
| f1_score | FLOAT | Weighted F1 score |
| model_path | VARCHAR(500) | Path to .joblib file |
| is_active | BOOLEAN | Whether this is the active model |

#### users
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| username | VARCHAR(100) | Unique login name |
| display_name | VARCHAR(255) | Full name |
| role | VARCHAR(20) | "admin", "reviewer", or "viewer" |
| created_at | DATETIME | UTC timestamp |

---

## 4. ML Pipeline

### 4.1 Pipeline Flow

```
                           ┌─────────────┐
                           │  CSV/Excel  │
                           │   Upload    │
                           └──────┬──────┘
                                  │
                           ┌──────▼──────┐
                           │   Parse &   │
                           │  Normalize  │
                           └──────┬──────┘
                                  │
                           ┌──────▼──────┐
                           │ Preprocess  │
                           │   Text      │
                           └──────┬──────┘
                                  │
                           ┌──────▼──────┐
                           │  TF-IDF     │
                           │ Vectorize   │
                           │ (250-dim)   │
                           └──────┬──────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
             ┌──────▼──────┐            ┌──────▼──────┐
             │  Duplicate   │            │   Classify  │
             │  Detector    │            │  (SVM + LR) │
             │ (cosine sim) │            │  ensemble   │
             └──────┬──────┘            └──────┬──────┘
                    │                           │
             ┌──────▼──────┐            ┌──────▼──────┐
             │   Mark as   │            │ Confidence  │
             │  DUPLICATE  │            │  >= 0.60?   │
             │ (set FK)    │            └──┬──────┬───┘
             └─────────────┘              YES     NO
                                           │      │
                                    ┌──────▼┐  ┌──▼───────┐
                                    │ Auto- │  │  Review  │
                                    │classify│  │  Queue   │
                                    │as final│  │(human)   │
                                    └───────┘  └──┬───────┘
                                                  │
                                           ┌──────▼──────┐
                                           │   Human     │
                                           │  Override   │
                                           └──────┬──────┘
                                                  │
                                           ┌──────▼──────┐
                                           │ 50 overrides│
                                           │  → Retrain  │
                                           └─────────────┘
```

### 4.2 Text Preprocessing (`src/ml/preprocessor.py`)

Each bug's summary and description are combined and processed through:

1. **HTML stripping** — Removes HTML tags (common in Jira descriptions)
2. **URL removal** — Strips embedded URLs
3. **Jira key removal** — Removes patterns like `PROJ-123`
4. **Lowercasing** — Normalizes case
5. **Punctuation removal** — Strips all punctuation characters
6. **Stop word filtering** — Removes 80+ common English words (the, a, is, are, etc.)
7. **Short word removal** — Drops single-character tokens
8. **Lemmatization** — Reduces words to base forms (optional, requires NLTK wordnet data)

**Example**:
```
Input:  "<b>Login fails</b> when clicking https://app.com/login - see PROJ-456"
Output: "login fails clicking see"
```

### 4.3 Feature Extraction (`src/ml/feature_extractor.py`)

Uses scikit-learn's `TfidfVectorizer` with:
- **Max features**: 250 (configurable)
- **N-gram range**: (1, 2) — captures unigrams and bigrams
- **Sublinear TF**: Enabled (applies logarithmic TF scaling)

The vectorizer is fitted on the first training batch and persisted as a `.joblib` file. Subsequent uploads use the same vocabulary for consistent feature spaces.

### 4.4 Duplicate Detection (`src/ml/duplicate_detector.py`)

Detects duplicate bug reports using **cosine similarity** on TF-IDF vectors:

- Computes pairwise cosine similarity matrix across all bugs in a cycle
- Uses **summary-only vectors** (not full descriptions) for more precise matching — descriptions often contain noise that inflates similarity
- **Threshold**: 0.92 (configurable) — only pairs above this threshold are flagged
- **Ordering logic**: Later bugs are compared only against earlier non-duplicate bugs, preventing chain duplication
- When a duplicate is found, `duplicate_of_id` is set as a foreign key to the original

### 4.5 Classification (`src/ml/classifier.py`)

An **ensemble** of two classifiers:

1. **Linear SVM** (wrapped in `CalibratedClassifierCV` for probability estimation)
   - `max_iter=5000`, `class_weight="balanced"`
   - Good at finding optimal decision boundaries between classes

2. **Logistic Regression**
   - `max_iter=1000`, `class_weight="balanced"`
   - Provides well-calibrated probability estimates

**Ensemble method**: Average the predicted probabilities from both models, then take the argmax as the final prediction. Confidence is the probability of the chosen class.

**Evaluation**: Cross-validated F1 scores (weighted) for both models are computed during training and stored with the model version.

### 4.6 Explainability (`src/ml/explainer.py`)

Each classification includes a human-readable explanation:

- **For classified bugs**: Lists the top 5 TF-IDF features that contributed to the prediction, along with their weights and a probability breakdown across classes.
  - Example: *"Classified as 'invalid' (confidence: 78%). Top contributing features: 'ui color' (0.432), 'cosmetic' (0.318), 'suggestion' (0.215). Probability breakdown: invalid: 78%, valid: 15%, duplicate: 7%."*

- **For duplicates**: Shows the similarity score and the original bug's summary.
  - Example: *"Marked as DUPLICATE (similarity: 95%). Similar to: 'Login fails when entering valid credentials'."*

### 4.7 Active Learning (`src/ml/active_learner.py`)

When a human reviewer overrides an ML classification:
1. The override is recorded in `classification_audit_log`
2. `final_classification` is updated, `classification_source` set to "human"
3. After **50 human overrides** (configurable), the system triggers automatic retraining
4. Retraining uses all bugs with `final_classification` set as the labeled dataset
5. A new model version is saved and activated

This creates a feedback loop where the model improves as humans correct its mistakes.

---

## 5. Metrics

All metrics are computed in `src/metrics/calculator.py`.

### 5.1 Core Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Testing Accuracy** | `valid_bugs / total_bugs` | Primary KPI — what % of reports are real defects |
| **Duplicate Rate** | `duplicate_bugs / total_bugs` | Indicates redundancy in testing efforts |
| **Invalid Rate** | `invalid_bugs / total_bugs` | Indicates false positive rate in bug reporting |
| **DDE** (Defect Detection Effectiveness) | `valid_unique / (valid_unique + invalid_unique)` | Quality of non-duplicate reports (excludes duplicates from calculation) |
| **Misclassification Rate** | `ml_disagreements / total_reviewed` | How often the ML model disagrees with human reviewers |

### 5.2 Breakdown Metrics

| Metric | Description |
|--------|-------------|
| **Per-tester accuracy** | Testing accuracy broken down by reporter — identifies testers who need coaching |
| **Component breakdown** | Accuracy per software component — identifies problem areas |
| **Classification distribution** | Count of valid/invalid/duplicate across the cycle |

### 5.3 Trend Metrics

`project_trends()` computes all metrics for each cycle in chronological order, enabling visualization of how testing quality evolves over time. Expected pattern for a maturing team:
- Testing accuracy increases (more valid bugs found)
- Duplicate rate decreases (better coordination)
- Invalid rate decreases (better understanding of the product)

---

## 6. Data Ingestion

### 6.1 Supported Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| CSV | `.csv` | UTF-8 or Latin-1 encoding auto-detected |
| Excel | `.xlsx`, `.xls` | Reads first sheet via openpyxl |

### 6.2 Source System Auto-Detection

The parser auto-detects the source system by checking column names:

| Source | Detection columns | Key mappings |
|--------|------------------|--------------|
| **Jira** | `Issue key`, `Summary`, `Component/s` | `Issue key` → external_id, `Component/s` → component |
| **Azure DevOps** | `ID`, `Title`, `Repro Steps`, `Area Path` | `Repro Steps` → description, `Area Path` → component |
| **Generic** | `id`, `summary`, `description` | Direct 1:1 mapping |

### 6.3 Field Normalization

After parsing, fields are normalized:
- **Priority**: Mapped to standard levels (Critical, Major, Minor, Trivial)
- **Severity**: Same standardization as priority
- **Dates**: Parsed from 7 common formats (ISO 8601, US, EU, etc.)
- **Strings**: Trimmed of whitespace, empty strings replaced with defaults

---

## 7. API Reference

### 7.1 Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload CSV/Excel file for a project |

**Parameters** (multipart form):
- `file` (required): CSV or Excel file
- `project_id` (required): Target project ID
- `cycle_name` (required): Name for the new cycle
- `source_system` (optional): "jira", "azure_devops", "generic", or "auto" (default)

**Response**:
```json
{
  "status": "success",
  "cycle_id": 1,
  "total_bugs": 120,
  "source_system": "jira",
  "classified": 95,
  "duplicates_found": 25,
  "low_confidence": 3
}
```

### 7.2 Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a new project |
| `GET` | `/api/projects/{id}` | Get project with its cycles |

### 7.3 Cycles

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cycles/{project_id}` | List cycles for a project |

### 7.4 Bugs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/bugs/cycle/{cycle_id}` | List bugs in a cycle |
| `GET` | `/api/bugs/{id}` | Get bug details with explanation |

### 7.5 Classification

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/classify/{cycle_id}` | Run ML classification on a cycle |
| `POST` | `/api/override/{bug_id}` | Human override of a classification |
| `POST` | `/api/retrain` | Trigger model retraining |

**Override parameters** (JSON):
```json
{
  "new_classification": "valid",
  "reason": "This is a real defect, ML was wrong",
  "reviewed_by": "admin"
}
```

### 7.6 Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/cycle/{id}` | Full metrics for a cycle |
| `GET` | `/api/analytics/project/{id}/trends` | Trend data across all cycles |

### 7.7 Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/export/cycle/{id}` | Download classified bugs as CSV |

---

## 8. Dashboard Pages

### 8.1 Main Dashboard (`/` or `/dashboard`)

- **Global summary cards**: Total bugs, valid count, invalid count, duplicate count
- **Classification donut chart**: Overall valid/invalid/duplicate distribution
- **Accuracy bar chart**: Testing accuracy across all cycles
- **Project cards**: Each project shows cycle count, latest accuracy, links to recent cycles

### 8.2 Upload Page (`/upload`)

- Project selector dropdown (with option to create new)
- Cycle name input
- Source system selector (auto, Jira, Azure DevOps, generic)
- Drag-and-drop file upload zone
- Column preview after file selection

### 8.3 Cycle Detail (`/cycles/{id}`)

- **6 metric cards**: Total bugs, testing accuracy, duplicate rate, invalid rate, DDE, misclassification rate
- **Classification donut chart**: Distribution for this cycle
- **Per-tester bar chart**: Accuracy per reporter
- **Searchable bug table**: Sortable columns, color-coded classifications, confidence bars, clickable rows

### 8.4 Bug Detail (`/bugs/{id}`)

- Full bug information (summary, description, status, priority, component, reporter)
- ML classification with confidence and explanation
- Similar bugs (if duplicate, shows the original)
- **Override form**: Change classification with reason
- **Audit log**: Full history of classification changes

### 8.5 Review Queue (`/review/{cycle_id}`)

- **Low-confidence bugs**: Sorted by confidence (lowest first)
- **Unreviewed bugs**: Not yet seen by a human
- Inline override forms for quick batch review

### 8.6 Analytics (`/analytics/{project_id}`)

- **Trend line chart**: Testing accuracy, duplicate rate, invalid rate across cycles
- **Stacked bar chart**: Classification distribution per cycle
- **Component heatmap**: Accuracy by component across cycles
- **Cycle summary table**: All metrics in tabular form

---

## 9. Configuration

All configuration lives in `configs/config.py` as Python dataclasses.

### 9.1 Database Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `url` | `sqlite:///data/bug_analyzer.db` | SQLAlchemy connection URL |
| `echo` | `False` | Log all SQL queries |

### 9.2 ML Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tfidf_max_features` | `250` | Number of TF-IDF features |
| `tfidf_ngram_range` | `(1, 2)` | Unigram + bigram features |
| `duplicate_threshold` | `0.92` | Cosine similarity threshold for duplicate detection |
| `confidence_threshold` | `0.60` | Minimum confidence for auto-classification |
| `retrain_override_count` | `50` | Human overrides before automatic retraining |
| `model_dir` | `data/models/` | Where .joblib models are stored |

### 9.3 Ingest Configuration

Contains column mappings for Jira, Azure DevOps, and generic CSV formats. See `configs/config.py` for full mapping details.

### 9.4 App Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `title` | `Bug Report Accuracy Analyzer` | Application title |
| `host` | `0.0.0.0` | Server bind address |
| `port` | `8001` | Server port |
| `debug` | `True` | Enable hot reload |

---

## 10. Synthetic Data

The `generate_synthetic_data.py` script creates 3 CSV files simulating a QA team improving over 3 regression cycles:

| Cycle | Bugs | Valid % | Invalid % | Duplicate % | Narrative |
|-------|------|---------|-----------|-------------|-----------|
| Cycle 1 | 120 | ~48% | ~20% | ~32% | Early/messy testing — high noise |
| Cycle 2 | 100 | ~62% | ~18% | ~20% | Improving — team learning |
| Cycle 3 | 90 | ~69% | ~13% | ~18% | Mature — higher quality reports |

### Data characteristics:
- **6 testers** with varying accuracy profiles (e.g., alice.johnson is consistently good, frank.miller is inconsistent)
- **10 software components** (Authentication, Payment, Dashboard, etc.)
- **96 unique valid** and **40 unique invalid** bug summary templates
- **Paraphrased duplicates** to test cosine similarity detection at the 0.92 threshold
- **Jira-format columns** for realistic ingestion testing

---

## 11. Testing

### 11.1 Test Suite Overview

65 tests across 9 files, all using pytest:

| File | Tests | Covers |
|------|-------|--------|
| `test_api.py` | 13 | API endpoints, page routes, upload |
| `test_crud.py` | 11 | All database CRUD operations |
| `test_ingest.py` | 10 | CSV parsing, source detection, normalization |
| `test_preprocessor.py` | 8 | Text cleaning pipeline |
| `test_feature_extractor.py` | 4 | TF-IDF fit/transform/persistence |
| `test_duplicate_detector.py` | 5 | Cosine similarity duplicate detection |
| `test_classifier.py` | 4 | SVM+LR ensemble training/prediction |
| `test_metrics.py` | 10 | All metric calculations |
| `test_active_learner.py` | 3 | Retrain trigger logic |

### 11.2 Test Infrastructure

- **Database**: All tests use in-memory SQLite (`sqlite:///:memory:`) — never touches the real database
- **API tests**: Create a standalone FastAPI test app with `StaticPool` to ensure connection sharing in the same in-memory database
- **Fixtures**: Shared fixtures in `conftest.py` provide pre-created projects, cycles, bugs, and CSV files
- **Independence**: Each test is fully independent — no reliance on execution order

---

## 12. Deployment Notes

### Development
```bash
python3 run.py  # Starts with hot reload on port 8001
```

### Production Considerations
- Replace SQLite with PostgreSQL for concurrent access
- Set `debug=False` in `configs/config.py`
- Run with `gunicorn` + `uvicorn` workers:
  ```bash
  gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
  ```
- Add authentication middleware (currently no auth)
- Configure CORS to specific origins (currently allows all)
- Set up periodic model retraining as a background job
- Back up the SQLite database or migrate to PostgreSQL
