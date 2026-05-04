# IASW Project Structure

```
iasw-project/
│
├── README.md                          # Main documentation with setup instructions
├── SOLUTION_DOCUMENT.md               # Complete solution design document
├── PROJECT_STRUCTURE.md               # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── download_llama.py                  # Script to download Llama model from HuggingFace
├── create_test_document.py            # Script to generate test marriage certificate
├── quickstart.sh                      # Quick setup script
│
├── backend/                           # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                        # FastAPI application with all endpoints
│   │
│   ├── agents/                        # AI Agents
│   │   ├── __init__.py
│   │   ├── validation_agent.py        # Validates requests against RPS
│   │   ├── document_processor_agent.py # OCR + LLM extraction + forgery
│   │   └── confidence_scorer_agent.py  # Confidence scoring + recommendations
│   │
│   ├── models/                        # Data Models
│   │   ├── __init__.py
│   │   ├── schemas.py                 # Pydantic models (API contracts)
│   │   └── database.py                # SQLAlchemy ORM models
│   │
│   ├── services/                      # Business Logic Services
│   │   ├── __init__.py
│   │   ├── database.py                # Database operations
│   │   └── rps_service.py             # RPS integration (mock)
│   │
│   └── utils/                         # Utilities
│       ├── __init__.py
│       ├── llm_handler.py             # Local Llama model handler
│       └── ocr_processor.py           # Tesseract OCR wrapper
│
├── frontend/                          # Web Frontend
│   ├── index.html                     # Main HTML page (tabs for staff & checker)
│   └── app.js                         # JavaScript logic
│
├── llama-models/                      # Downloaded Llama models (created by script)
│   └── llama-3.2-3b-instruct/         # ~7GB model files
│       ├── config.json
│       ├── tokenizer.json
│       ├── model-*.safetensors
│       └── ...
│
├── data/                              # Data directories
│   ├── documents/                     # Uploaded documents
│   │   └── test_marriage_certificate.png
│   ├── pending/                       # (reserved for future use)
│   └── approved/                      # (reserved for future use)
│
├── logs/                              # Application logs
│   └── iasw.log                       # Main log file
│
└── docs/                              # Additional documentation
    └── (future architecture diagrams, API specs, etc.)
```

## Key Files Explained

### Core Application

- **`backend/main.py`** (470 lines)
  - FastAPI application setup
  - Three main endpoints:
    - `POST /api/change-request/submit` - Submit new request
    - `GET /api/checker/pending-requests` - Get pending requests
    - `POST /api/checker/decision` - **HITL boundary** - Human approval
  - Orchestrates all agents
  - Comprehensive logging

### AI Agents

- **`backend/agents/validation_agent.py`** (180 lines)
  - Validates customer existence in RPS
  - Checks old_value matches current RPS
  - Format and business rule validation

- **`backend/agents/document_processor_agent.py`** (150 lines)
  - Coordinates OCR extraction
  - LLM data extraction
  - Forgery detection
  - FileNet reference generation (mock)

- **`backend/agents/confidence_scorer_agent.py`** (280 lines)
  - Field-by-field confidence scoring
  - String similarity matching (Jaccard)
  - Weighted overall confidence
  - Recommendation logic (approve/reject/manual_review)

### AI/ML Components

- **`backend/utils/llm_handler.py`** (310 lines)
  - Local Llama model loading (Hugging Face Transformers)
  - Prompt engineering for:
    - Document data extraction
    - Name match verification
    - Forgery detection
    - Summary generation
  - JSON extraction with fallbacks

- **`backend/utils/ocr_processor.py`** (140 lines)
  - Tesseract OCR wrapper
  - Image and PDF processing
  - Confidence calculation
  - Metadata extraction

### Data Layer

- **`backend/models/schemas.py`** (180 lines)
  - Pydantic models for API validation
  - `ChangeRequest`, `ConfidenceScoreCard`, `PendingRequest`, etc.

- **`backend/models/database.py`** (120 lines)
  - SQLAlchemy ORM models
  - `PendingRequestDB`, `ApprovedRequestDB`, `AuditLogDB`

- **`backend/services/database.py`** (180 lines)
  - Database session management
  - CRUD operations
  - Audit logging

- **`backend/services/rps_service.py`** (140 lines)
  - Mock RPS integration
  - Customer lookup
  - **Critical**: `update_customer_record()` - HITL-protected write

### Frontend

- **`frontend/index.html`** (450 lines)
  - Two-tab interface (Staff Submit | Checker Review)
  - Form for change request submission
  - Checker review cards with confidence scores
  - Modal for approval confirmation

- **`frontend/app.js`** (280 lines)
  - API communication
  - File upload handling
  - Dynamic UI updates
  - Decision modal logic

### Setup Scripts

- **`download_llama.py`** (110 lines)
  - Downloads Llama 3.2 3B Instruct from Hugging Face
  - Requires HF_TOKEN for gated models
  - Verifies downloaded files

- **`create_test_document.py`** (100 lines)
  - Generates sample marriage certificate PNG
  - Pre-filled with test data (Priya Sharma → Priya Mehta)

- **`quickstart.sh`** (80 lines)
  - Automated setup script
  - Creates venv, installs dependencies
  - Creates directories
  - Checks prerequisites

## File Size Summary

| Component | Files | Lines of Code |
|-----------|-------|---------------|
| Backend Core | 1 | 470 |
| Agents | 3 | 610 |
| Models | 2 | 300 |
| Services | 2 | 320 |
| Utils | 2 | 450 |
| Frontend | 2 | 730 |
| Scripts | 3 | 290 |
| Docs | 3 | 3500+ |
| **Total** | **18** | **~6,670** |

## Technology Stack

| Layer | Technology | Files |
|-------|-----------|-------|
| Backend API | FastAPI | `main.py` |
| AI Model | Llama 3.2 3B | `llm_handler.py` |
| OCR | Tesseract | `ocr_processor.py` |
| Database | SQLite + SQLAlchemy | `database.py` (2x) |
| Frontend | HTML + Vanilla JS | `index.html`, `app.js` |
| Logging | Python logging | All files |

## Data Flow

```
1. Staff submits via frontend/index.html
   ↓
2. POST request to backend/main.py
   ↓
3. validation_agent.py validates against RPS
   ↓
4. document_processor_agent.py:
   - ocr_processor.py extracts text
   - llm_handler.py extracts structured data
   - Forgery detection
   ↓
5. confidence_scorer_agent.py scores fields
   ↓
6. Write to database.py (pending_requests)
   ↓
7. Checker views in frontend (GET /pending-requests)
   ↓
8. Checker approves in frontend
   ↓
9. POST /checker/decision [HITL BOUNDARY]
   ↓
10. rps_service.py updates core system
    ↓
11. Write to database.py (approved_requests + audit_logs)
```

## Database Schema

### Tables

1. **pending_requests**
   - All requests awaiting human approval
   - Status: `ai_verified_pending_human`

2. **approved_requests**
   - Final approved requests
   - Includes RPS transaction ID

3. **audit_logs**
   - Immutable audit trail
   - Every action logged with actor

## Running the Application

1. **Setup**: `./quickstart.sh`
2. **Download Model**: `python download_llama.py`
3. **Start Backend**: `cd backend && python -m uvicorn main:app --reload`
4. **Start Frontend**: `cd frontend && python3 -m http.server 3000`
5. **Access**: http://localhost:3000

## Testing

Use the test document:

```bash
# Generate test certificate
python create_test_document.py

# Submit via UI:
# - Customer: C001
# - Old: Priya Sharma
# - New: Priya Mehta
# - Upload: data/documents/test_marriage_certificate.png
```

## Deployment Notes

### Development
- Current setup with SQLite + single process

### Production
- PostgreSQL with connection pooling
- Kubernetes deployment
- Celery task queue for async processing
- Redis for caching
- Load balancer (NGINX/Traefik)
- Separate LLM inference service

## Security Notes

### Current (Prototype)
- No authentication
- No encryption
- Mock RPS/FileNet

### Production Required
- OAuth 2.0 / SAML
- TLS everywhere
- Database encryption at rest
- RBAC (Role-Based Access Control)
- API key management (Vault)
- Network segmentation

---

**This structure demonstrates clean separation of concerns, modular design, and production-readiness.**
