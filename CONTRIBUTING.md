# Contributing to Bug Report Accuracy Analyzer

Thank you for your interest in contributing! This guide covers everything you need to get started — from setting up your dev environment to submitting a pull request.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Architecture](#project-architecture)
- [Code Style & Conventions](#code-style--conventions)
- [Adding New Features](#adding-new-features)
- [Writing Tests](#writing-tests)
- [Database Migrations](#database-migrations)
- [ML Pipeline Changes](#ml-pipeline-changes)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Issues](#reporting-issues)

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/BugReportAnalyzer.git
   cd BugReportAnalyzer
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Generate synthetic demo data
python3 generate_synthetic_data.py

# Initialize the database
python3 setup_db.py

# Run tests to verify everything works
pytest tests/ -v

# Start the development server (port 8001, auto-reload enabled)
python3 run.py
```

### Useful Commands

| Command | Purpose |
|---------|---------|
| `python3 run.py` | Start dev server on port 8001 with hot reload |
| `pytest tests/ -v` | Run all 65 tests with verbose output |
| `pytest tests/test_api.py -v` | Run a specific test file |
| `pytest tests/ -k "test_create_project"` | Run a specific test by name |
| `python3 generate_synthetic_data.py` | Regenerate synthetic CSV files |
| `python3 setup_db.py` | Reset and reinitialize the database |

---

## Project Architecture

### Directory Layout

```
BugReportAnalyzer/
├── configs/config.py          # All configuration (dataclass-based)
├── src/
│   ├── pipeline.py            # Orchestrator: upload → preprocess → classify → store
│   ├── api/
│   │   ├── main.py            # FastAPI app setup, page routes
│   │   ├── dependencies.py    # Shared FastAPI dependencies
│   │   └── routes/            # API route modules (one per resource)
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine and session
│   │   ├── models.py          # 6 ORM models
│   │   └── crud.py            # All database query functions
│   ├── ml/                    # Machine learning components
│   ├── ingest/                # CSV/Excel parsing and normalization
│   └── metrics/               # Metric calculations
├── templates/                 # Jinja2 HTML templates (7 files)
├── static/                    # CSS, JavaScript, Chart.js
├── tests/                     # pytest test suite (9 files, 65 tests)
└── data/
    ├── synthetic/             # Generated demo CSVs
    └── models/                # Persisted .joblib ML models
```

### Key Design Patterns

- **Configuration**: All settings live in `configs/config.py` as Python dataclasses. No `.env` files — modify the dataclass defaults directly.
- **Database access**: All DB operations go through `src/db/crud.py`. Route handlers never write raw SQL or ORM queries directly.
- **Classification flow**: `ml_classification` holds the ML prediction. `final_classification` holds the authoritative label (defaults to ML, overridable by humans). Always read `final_classification` for display.
- **ML pipeline**: The `src/pipeline.py` orchestrator ties together preprocessing, feature extraction, duplicate detection, and classification. Individual ML components are stateless and testable in isolation.
- **Templates**: All templates extend `base.html`. Chart rendering uses `waitForChart()` wrappers since Chart.js loads asynchronously.

### Database Schema

The 6 tables and their relationships:

```
projects  ──1:N──  regression_cycles  ──1:N──  bug_reports  ──1:N──  classification_audit_log
                                                    │
                                                    └── duplicate_of (self-referencing FK)

model_versions (standalone)
users (standalone)
```

---

## Code Style & Conventions

### Python

- **Imports**: Standard library first, third-party second, local imports third, separated by blank lines.
- **Docstrings**: Module-level docstrings on every file. Function docstrings for public functions.
- **Type hints**: Use them for function signatures in API routes and public interfaces.
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Line length**: Keep lines under 120 characters.

### API Routes

- Each resource gets its own file in `src/api/routes/`.
- Use `APIRouter` with a `/api/<resource>` prefix and appropriate tags.
- Request/response schemas use Pydantic `BaseModel` classes defined at the top of the route file.
- All DB access goes through `crud.py` functions — never query the ORM directly in route handlers.

```python
# Example route pattern
router = APIRouter(prefix="/api/widgets", tags=["widgets"])

class WidgetCreate(BaseModel):
    name: str
    description: str = ""

@router.post("")
def create_widget(data: WidgetCreate, db: Session = Depends(get_db)):
    widget = crud.create_widget(db, data.name, data.description)
    return {"id": widget.id, "name": widget.name}
```

### Templates

- All pages extend `templates/base.html`.
- Use Bootstrap 5 utility classes for layout — avoid custom CSS unless necessary.
- Chart.js rendering goes in `{% block scripts %}` and must be wrapped in `waitForChart()`.
- Keep Jinja2 logic minimal — compute data in Python, not in templates.

### JavaScript

- No build tools or bundlers. Plain JavaScript only.
- Chart.js is served locally from `static/js/chart.umd.min.js`.
- Shared chart functions live in `static/js/charts.js`.
- Page-specific scripts go in the template's `{% block scripts %}`.

---

## Adding New Features

### Adding a New API Endpoint

1. **CRUD function** — Add the database operation to `src/db/crud.py`
2. **Route handler** — Add the endpoint to the appropriate file in `src/api/routes/`, or create a new route file
3. **Include router** — If you created a new route file, register it in `src/api/main.py`
4. **Tests** — Add tests in `tests/test_api.py` or a new test file

### Adding a New Page

1. **Template** — Create `templates/your_page.html` extending `base.html`
2. **Page route** — Add a `@app.get("/your-page")` handler in `src/api/main.py`
3. **Navigation** — Add a nav link in `templates/base.html` if it belongs in the main nav
4. **Tests** — Add a page route test in `tests/test_api.py`

### Adding a New Metric

1. **Calculator** — Add the computation function to `src/metrics/calculator.py`
2. **Integration** — Include it in `cycle_metrics()` or `project_trends()` as appropriate
3. **Display** — Update the relevant template to show the metric
4. **Tests** — Add unit tests in `tests/test_metrics.py`

### Adding a New Data Source

1. **Column map** — Add a new column mapping to `configs/config.py` under `IngestConfig`
2. **Detection** — Update `src/ingest/parser.py` to auto-detect the new source format
3. **Normalization** — Add any source-specific normalization to `src/ingest/normalizer.py`
4. **Tests** — Add parsing tests in `tests/test_ingest.py`

---

## Writing Tests

### Test Structure

Tests live in `tests/` with one file per module:

| Test File | Covers |
|-----------|--------|
| `test_api.py` | API endpoints and page routes |
| `test_crud.py` | Database CRUD operations |
| `test_ingest.py` | CSV/Excel parsing and normalization |
| `test_preprocessor.py` | Text preprocessing pipeline |
| `test_feature_extractor.py` | TF-IDF vectorization |
| `test_duplicate_detector.py` | Cosine similarity detection |
| `test_classifier.py` | SVM/LR ensemble classifier |
| `test_metrics.py` | Metric calculations |
| `test_active_learner.py` | Active learning / retrain logic |

### Shared Fixtures

Common fixtures are defined in `tests/conftest.py`:

- **`db_session`** — In-memory SQLite session (auto-creates all tables, auto-closes)
- **`sample_project`** — A pre-created project
- **`sample_cycle`** — A pre-created cycle linked to the sample project
- **`sample_bugs`** — 5 pre-created bugs with varied classifications
- **`sample_csv_path`** — A temporary CSV file in Jira format

### Guidelines

- Use `db_session` for all database tests — never touch the real database.
- API tests use a standalone `TestClient` with `StaticPool` in-memory SQLite. See `test_api.py` for the pattern.
- Each test should be independent — don't rely on execution order.
- Test both success and error cases (e.g., 404 for nonexistent resources, 400 for invalid input).
- For metrics tests, use the `FakeBug` dataclass pattern instead of constructing ORM objects directly.

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage (install pytest-cov first)
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing

# Stop on first failure
pytest tests/ -x

# Run tests matching a pattern
pytest tests/ -k "duplicate"
```

---

## Database Migrations

This project uses SQLite with SQLAlchemy ORM. There is no migration framework (like Alembic) currently configured.

### Adding a New Column

1. Add the column to the model in `src/db/models.py`
2. Update `setup_db.py` if the column needs seed data
3. For development, the easiest approach is to delete `data/bug_analyzer.db` and rerun `python3 setup_db.py`
4. Update any affected CRUD functions, routes, and templates

### Adding a New Table

1. Define the model in `src/db/models.py` (extend `Base`)
2. Import it in `tests/conftest.py` (so `create_all` picks it up)
3. Add CRUD functions in `src/db/crud.py`
4. Rerun `python3 setup_db.py`

---

## ML Pipeline Changes

### Tuning Parameters

All ML parameters are in `configs/config.py` under `MLConfig`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tfidf_max_features` | 250 | Number of TF-IDF features |
| `tfidf_ngram_range` | (1, 2) | Unigrams and bigrams |
| `duplicate_threshold` | 0.92 | Cosine similarity threshold for duplicate detection |
| `confidence_threshold` | 0.60 | Minimum confidence for auto-classification |
| `retrain_override_count` | 50 | Human overrides before automatic retraining |

### Modifying the Classifier

The classifier lives in `src/ml/classifier.py` and uses a `CalibratedClassifierCV`-wrapped SVM + Logistic Regression ensemble. If you change the model architecture:

1. Update `classifier.py` with your new model
2. Delete any existing `.joblib` files in `data/models/`
3. Run the pipeline on test data to retrain
4. Update `tests/test_classifier.py` with appropriate assertions
5. Verify duplicate detection still works (`tests/test_duplicate_detector.py`)

### Adding a New ML Component

1. Create a new module in `src/ml/`
2. Wire it into `src/pipeline.py`
3. Add a dedicated test file in `tests/`
4. Update the README ML pipeline diagram if the flow changes

---

## Submitting a Pull Request

### Before You Submit

1. **Run the full test suite** and ensure all tests pass:
   ```bash
   pytest tests/ -v
   ```
2. **Test manually** — start the server and verify your changes work in the browser:
   ```bash
   python3 run.py
   # Visit http://localhost:8001
   ```
3. **Check for leftover debug code** — remove any `print()` statements, `console.log()`, or test HTML files.

### PR Process

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a pull request against `main` on the upstream repository.
3. In the PR description, include:
   - **What** the change does
   - **Why** it's needed
   - **How** to test it (manual steps or specific test commands)
   - Screenshots if the change affects the UI
4. Wait for review. Address any feedback by pushing additional commits to your branch.

### Commit Messages

- Use the imperative mood: "Add feature" not "Added feature"
- Keep the first line under 70 characters
- Add a blank line and a longer description for non-trivial changes
- Reference issue numbers where applicable: "Fix #42 — handle empty CSV upload"

---

## Reporting Issues

When opening an issue, please include:

- **Description** — What happened vs. what you expected
- **Steps to reproduce** — Minimal steps to trigger the issue
- **Environment** — Python version, OS, browser (if UI-related)
- **Error output** — Full traceback or browser console errors
- **Sample data** — A minimal CSV that triggers the issue (if applicable)

---

## Questions?

If you're unsure about an approach or need guidance, open an issue with the **question** label and describe what you're trying to do. We're happy to help!
