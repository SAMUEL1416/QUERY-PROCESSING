# ReXplore — Intelligent Semantic Research Understanding & Knowledge Discovery

ReXplore analyzes a **complete** research-paper PDF (not just the abstract) and converts it into
short, understandable, searchable research knowledge: structured section summaries, a
paper-grounded Q&A assistant, real public-dataset discovery, and cross-paper analytics.

This is a real, working full-stack application — there are no fake API responses, fake research
results, fake URLs, or fake DOIs anywhere in the codebase. Where a real answer cannot be found,
the system says so explicitly ("Not identified in the available paper content.") rather than
inventing one.

---

## 1. Project Overview

| | |
|---|---|
| **Backend** | Python, FastAPI, SQLAlchemy, SQLite |
| **Frontend** | React 18, Vite, Framer Motion, Recharts |
| **PDF processing** | PyMuPDF (text), Tesseract OCR (scanned-page fallback) |
| **Semantic search** | `sentence-transformers/all-MiniLM-L6-v2` + cosine similarity, with a TF-IDF keyword fallback |
| **Dataset discovery** | Live calls to Hugging Face Datasets, Zenodo, DataCite, UCI ML Repository, and (optionally) Kaggle |

## 2. Objectives

1. Turn a full research paper into structured, study-friendly knowledge (not just an abstract summary).
2. Let a reader ask natural-language questions and get answers grounded strictly in the paper's own text, with page/section citations.
3. Help readers actually obtain the data a paper used — the real dataset if it's public, a real
   relevant alternative if it isn't, and only as a last resort a clearly-labeled synthetic
   stand-in.
4. Surface the paper's underlying problem → objective → method → model → dataset → evaluation →
   results chain, and let multiple papers be compared side by side.

## 3. The Three Modules

### Module 1 — Feature Extraction & Research Understanding
Uploads a PDF → extracts text page-by-page (OCR fallback for scanned pages) → detects standard
research sections (Abstract, Introduction, Methodology, Results, Limitations, Conclusion, Future
Work, etc.) → extracts algorithms/models, datasets, metrics, and concepts/keywords → produces a
short, extractive (never fabricated) key-points / simple-explanation / findings summary per
section.

### Module 2 — Query Processing & Dataset Intelligence
- **Query processing**: cleans and normalizes a question, embeds it with MiniLM, retrieves the
  most relevant chunks of the paper by cosine similarity (or TF-IDF keyword matching if the
  embedding model isn't available), and returns an extractive, paper-grounded answer with
  clickable page/section sources. Never hallucinates — if nothing relevant is found, it says so.
- **Dataset intelligence**: detects dataset names mentioned in the paper, then searches real
  public repositories in priority order:
  1. **Exact original dataset** (if a public match is found)
  2. **Real alternative dataset** (closest public match, clearly labeled as *not* the original)
  3. **Synthetic CSV** — only offered when neither of the above exists, and always labeled
     "SYNTHETIC DATASET — NOT THE ORIGINAL RESEARCH DATA"

### Module 3 — Knowledge Discovery & Research Analytics
Builds a Problem → Objective → Method → Model → Dataset → Evaluation → Results chain from what
was actually extracted (any step with nothing found is simply omitted, never invented), and
aggregates real backend counts/distributions for the Analytics dashboard and multi-paper
Comparison view.

## 4. Architecture

```
Browser (React/Vite, :5173)
        │  axios, proxied to /api
        ▼
FastAPI backend (:8000)
        │
        ├── routers/         → HTTP endpoints
        ├── services/         → all real processing logic (PDF, OCR, extraction,
        │                       embeddings, retrieval, dataset search, synthetic gen)
        └── SQLite (rexplore.db) via SQLAlchemy
```

Paper processing runs as a FastAPI **background task** so upload returns instantly; the frontend
polls `GET /api/papers/{id}` and shows live stage-by-stage status
(Reading → Detecting Sections → Extracting Features → Understanding Research → Detecting
Datasets → Building Semantic Index → Ready).

## 5. Technology Stack

**Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, PyMuPDF, pytesseract,
sentence-transformers, NumPy, Pandas, scikit-learn (TF-IDF fallback), Requests.

**Frontend:** React 18, Vite, React Router, Axios, Framer Motion, Recharts, Lucide React.

## 6. Folder Structure

```
backend/
├── app/            main.py, database.py, models.py, schemas.py, config.py
├── routers/        papers.py, queries.py, datasets.py, analytics.py
├── services/        pdf_processor, ocr_service, section_extractor, feature_extractor,
│                    research_understanding, embedding_service, query_processor,
│                    retrieval_service, dataset_detector, dataset_search,
│                    huggingface_service, zenodo_service, datacite_service, uci_service,
│                    kaggle_service, synthetic_generator, comparison_service,
│                    analytics_service, pipeline_service (orchestrator)
├── tests/
├── uploads/  generated/  indexes/
└── requirements.txt

frontend/
├── src/
│   ├── components/  Sidebar, Header, PaperUpload, PaperOverview, SectionExplanation,
│   │                FeatureList, QueryBox, QueryAnswer, SourceReference, DatasetCard,
│   │                DatasetSearch, DatasetAlternative, SyntheticGenerator,
│   │                PaperComparison, AnalyticsDashboard
│   ├── pages/       Dashboard, LibraryPage, UploadPage, PaperPage, QueryPage,
│   │                DatasetPage, ComparisonPage, AnalyticsPage
│   └── styles/      theme.css (tokens), main.css (everything else)
└── package.json
```

## 7. Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional, for scanned PDFs) Tesseract OCR installed on your system:
  `apt install tesseract-ocr` (Linux) / `brew install tesseract` (macOS) / [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki)
- Internet access on first run (to download the MiniLM embedding model, and for live dataset-API calls)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit if you want to add Kaggle credentials
uvicorn app.main:app --reload
```
Backend: http://localhost:8000 · Swagger docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend: http://localhost:5173 (proxies `/api` to the backend automatically)

## 8. Database

SQLite database `backend/rexplore.db`, created automatically on first backend startup.

| Table | Purpose |
|---|---|
| `papers` | One row per uploaded PDF, with live processing status |
| `paper_sections` | Detected sections + key points / explanation / concepts / findings |
| `paper_features` | Extracted algorithms, metrics, dataset mentions, concepts |
| `datasets` | Dataset search results per mention (original/alternative/synthetic/not_found) |
| `query_history` | Every question asked + its grounded answer |
| `query_sources` | Page/section citations backing each answer |
| `synthetic_datasets` | Metadata + file path for any generated synthetic CSVs |

## 9. API Reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/papers/upload` | Upload a PDF, kicks off background processing |
| GET | `/api/papers` | List all papers |
| GET | `/api/papers/{id}` | Full paper detail (sections + features) |
| GET | `/api/papers/{id}/file` | Download/view the original PDF |
| POST | `/api/papers/compare` | Compare 2–6 papers (`{"paper_ids": [...]}`) |
| POST | `/api/queries` | Ask a question about a paper |
| GET | `/api/queries/paper/{id}` | Query history for a paper |
| GET | `/api/datasets/paper/{id}` | Datasets detected for a paper |
| GET | `/api/datasets/{id}/search` | Re-run a live dataset search |
| POST | `/api/datasets/{id}/synthetic` | Generate a synthetic CSV (last resort only) |
| GET | `/api/datasets/synthetic/{id}/download` | Download a generated synthetic CSV |
| GET | `/api/analytics/overview` | Real aggregate counters |
| GET | `/api/analytics/features` | Chart-ready distributions |

Full interactive docs at `/docs` once the backend is running.

## 10. Dataset Sources

Real public APIs only, called live at request time:
- **Hugging Face Datasets Hub** (`huggingface.co/api/datasets`) — no auth required
- **Zenodo** (`zenodo.org/api/records`) — no auth required
- **DataCite** (`api.datacite.org/dois`) — no auth required
- **UCI Machine Learning Repository** (`archive.ics.uci.edu/api`) — no auth required
- **Kaggle** (`kaggle.com/api/v1/datasets/list`) — requires your own API credentials in `.env`
  (`KAGGLE_USERNAME`, `KAGGLE_KEY`); skipped entirely if not configured, never faked.

## 11. ⚠️ Synthetic Data Warning

Synthetic datasets are generated **only** when both (a) the original dataset cannot be found
publicly and (b) no real, relevant alternative dataset can be found either. Every synthetic file
is stamped with a `# SYNTHETIC DATASET — NOT THE ORIGINAL RESEARCH DATA` header line and every
synthetic dataset card in the UI is labeled accordingly. Synthetic data must never be used as a
substitute for real experimental results.

## 12. Testing

```bash
cd backend
pytest -v
```
Covers: PDF text extraction and validation, section detection, feature extraction (algorithms,
metrics, datasets, concepts), keyword-retrieval fallback ranking, synthetic CSV generation and
reproducibility, database cascade/relationship behavior, and dataset-search fallback priority
(original → alternative → not-found), with external sources mocked so tests run offline.

## 13. Running

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload

# terminal 2
cd frontend && npm run dev
```
Then open http://localhost:5173, upload a PDF, and watch it move through
Uploading → Reading → Sections → Features → Understanding → Datasets → Semantic Index → Ready.

## 14. Research Integrity

ReXplore never fabricates findings, results, authors, DOIs, URLs, algorithms, metrics, or
dataset information. Every piece of output is labeled by its actual provenance:
1. **From the paper** — sections, key points, findings, extracted features
2. **From a public repository** — dataset name, DOI, URL, description
3. **System interpretation** — extractive summaries, similarity-based domain inference
4. **Alternative dataset** — explicitly marked "not the original"
5. **Synthetic data** — explicitly marked "not original research data"
