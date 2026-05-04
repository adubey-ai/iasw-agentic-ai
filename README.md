# IASW - Intelligent Account Servicing Workflow

**AI Product Engineer Technical Challenge Solution**

An agentic AI application that automates document verification and data validation for core banking account change requests while maintaining strict Human-in-the-Loop (HITL) approval.

---

## 🎯 Executive Summary

This solution implements an **Intelligent Account Servicing Workflow (IASW)** that replaces the manual "Maker" role in banking operations with AI agents, while preserving the human "Checker" as the final decision authority. The system processes account change requests (name changes, address updates, etc.) through:

1. **AI-Augmented Intake** - Validates requests and processes documents via OCR + LLM
2. **Automated Verification** - Generates confidence scores and forgery detection
3. **Human-in-the-Loop Approval** - Checker reviews AI analysis before RPS update

### Key Achievement
✅ **Complete end-to-end working prototype** of Legal Name Change flow  
✅ **Local Qwen2.5-VL model** from Hugging Face (no API calls)  
✅ **Strict HITL boundary** - AI never writes to RPS autonomously  
✅ **Full observability** - Comprehensive logging and audit trail  

---

## 📋 Table of Contents

1. [Problem Understanding & Scope](#problem-understanding--scope)
2. [Solution Architecture](#solution-architecture)
3. [Agent Design](#agent-design)
4. [Technology Stack](#technology-stack)
5. [Setup Instructions](#setup-instructions)
6. [Running the Application](#running-the-application)
7. [Working Flow Demo](#working-flow-demo)
8. [HITL Boundary Design](#hitl-boundary-design)
9. [Observability & Logging](#observability--logging)
10. [Assumptions & Limitations](#assumptions--limitations)

---

## 🎯 Problem Understanding & Scope

### Current Pain Points
- **Manual data entry** prone to human error
- **Document verification** is time-consuming and inconsistent
- **Dual-check process** (Maker + Checker) creates bottlenecks
- **Document archival** is manual and inconsistent

### Solution Scope
This prototype implements:
- ✅ **Legal Name Change** flow (complete end-to-end)
- ✅ AI-powered document processing with **local Qwen2.5-VL-7B-Instruct**
- ✅ OCR extraction using Tesseract
- ✅ Confidence scoring and forgery detection
- ✅ Human checker approval interface
- ✅ Mock RPS integration (ready for production)
- ✅ Mock FileNet archival (ready for production)
- ✅ SQLite database with audit logging

### Out of Scope (Production Enhancements)
- Address/DOB/Email change types (architecture supports, not implemented)
- Real FileNet integration
- Real RPS API integration
- Advanced forgery detection (computer vision models)
- Production authentication/authorization
- Horizontal scaling and load balancing

---

## 🏗️ Solution Architecture

### High-Level Architecture

```
┌─────────────────┐
│  Frontend UI    │  (React/HTML - Staff & Checker interfaces)
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  API Endpoints                               │  │
│  │  - POST /change-request/submit              │  │
│  │  - GET  /checker/pending-requests           │  │
│  │  - POST /checker/decision                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Agent Orchestration Layer                   │  │
│  │  ┌────────────┐  ┌───────────────┐         │  │
│  │  │ Validation │  │   Document    │         │  │
│  │  │   Agent    │  │   Processor   │         │  │
│  │  └────────────┘  └───────────────┘         │  │
│  │  ┌────────────┐  ┌───────────────┐         │  │
│  │  │ Confidence │  │    Summary    │         │  │
│  │  │   Scorer   │  │     Agent     │         │  │
│  │  └────────────┘  └───────────────┘         │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  AI/ML Layer                                 │  │
│  │  ┌───────────────────────────────────────┐  │  │
│  │  │  Local Qwen2.5-VL-7B-Instruct        │  │  │
│  │  │  (Hugging Face Transformers)         │  │  │
│  │  └───────────────────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────┐  │  │
│  │  │  Tesseract OCR Engine                │  │  │
│  │  └───────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Services Layer                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────┐ │  │
│  │  │ Database │  │   RPS    │  │  FileNet  │ │  │
│  │  │ Service  │  │ Service  │  │  (Mock)   │ │  │
│  │  │ (SQLite) │  │  (Mock)  │  │           │ │  │
│  │  └──────────┘  └──────────┘  └───────────┘ │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │                    │
    ┌────▼────┐         ┌────▼────┐
    │ SQLite  │         │  Logs   │
    │ Database│         │ (File)  │
    └─────────┘         └─────────┘
```

### Component Interaction Flow

```
Staff Submission → Validation Agent → Document Processor Agent
                                              ↓
                                         OCR Engine
                                              ↓
                                      Local Qwen2.5-VL (multimodal)
                                              ↓
                                   Confidence Scorer Agent
                                              ↓
                                    Pending Table (SQLite)
                                              ↓
                               Human Checker Review UI
                                              ↓
                                  [HITL BOUNDARY HERE]
                                              ↓
                              Checker Approves/Rejects
                                              ↓
                      (If Approved) → RPS Service Update
                                              ↓
                                    Approved Table + Audit Log
```

### Synchronous vs Asynchronous Boundaries

- **Synchronous**: API request → Validation → Document Processing → Scoring → DB write
- **Asynchronous (Production Ready)**: Document processing and LLM inference can be moved to task queue (Celery/RabbitMQ) for heavy loads
- **Real-time**: Checker UI polls for pending requests (can be upgraded to WebSockets)

---

## 🤖 Agent Design

### 1. Validation Agent

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Validate intake fields against RPS + document forgery check |
| **Input** | ChangeRequest (customer_id, change_type, old_value, new_value) |
| **Output** | ValidationResult (valid: bool, errors: List, warnings: List) |
| **Logic** | • Check customer exists in RPS<br>• Verify old_value matches current RPS value<br>• Validate format of new_value<br>• Check business rules |

**Implementation**: `backend/agents/validation_agent.py`

### 2. Document Processor Agent

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | OCR + extraction + forgery detection + FileNet archival |
| **Input** | Uploaded document (file_path), change_type, document_type |
| **Output** | DocumentProcessingResult (extracted_data, ocr_confidence, forgery_detected, filenet_reference) |
| **Logic** | • Perform OCR with Tesseract<br>• Extract structured data with Qwen2.5-VL<br>• Run forgery detection<br>• Generate FileNet reference |

**Implementation**: `backend/agents/document_processor_agent.py`

### 3. Confidence Scorer Agent

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Score each field match and generate overall confidence |
| **Input** | ChangeRequest + DocumentProcessingResult |
| **Output** | ConfidenceScoreCard (overall_confidence, field_scores, recommendation) |
| **Logic** | • Compare extracted_data with requested changes<br>• Calculate string similarity scores<br>• Weight critical fields (old_name, new_name)<br>• Penalize for forgery detection<br>• Recommend: approve/reject/manual_review |

**Implementation**: `backend/agents/confidence_scorer_agent.py`

### 4. Summary Agent (Embedded in Confidence Scorer)

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Generate human-readable summary for checker |
| **Input** | ConfidenceScoreCard + extracted data |
| **Output** | Natural language summary + recommended action |
| **Logic** | • Use Qwen2.5-VL to generate 2-3 sentence summary<br>• Fallback to template if LLM fails |

**Implementation**: Within `ConfidenceScorerAgent._generate_summary()`

---

## 🛠️ Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Frontend** | HTML + Vanilla JavaScript | • Simple, no build step required<br>• Easy to demo and test<br>• Production would use React/Next.js |
| **Backend API** | FastAPI | • Fast, modern Python framework<br>• Automatic OpenAPI docs<br>• Async support for scalability<br>• Type hints with Pydantic |
| **Orchestration** | Native Python (no framework) | • Agents are simple enough to not require LangChain overhead<br>• Production could add LangGraph for complex workflows<br>• Keeps dependencies minimal |
| **LLM** | **Qwen2.5-VL-7B-Instruct** (local, multimodal) | • Downloaded from Hugging Face<br>• Runs locally without API calls<br>• Handles text **and** document images in one pass<br>• Instruction-tuned for structured extraction<br>• `IASW_FAST_MODE=1` bypasses the model for instant demo submissions |
| **LLM Runtime** | Hugging Face Transformers + PyTorch | • Industry standard for local LLM inference<br>• GPU acceleration when available<br>• Easy model loading and management |
| **OCR** | Tesseract | • Free, open-source, production-ready<br>• Supports 100+ languages<br>• Production upgrade: AWS Textract or Google Document AI |
| **Database** | SQLite | • Zero-config for prototype<br>• Production: PostgreSQL with connection pooling |
| **Document Store** | Local filesystem | • Mock implementation<br>• Production: S3 or FileNet integration |
| **Observability** | Python logging + structured logs | • File-based logs with rotation<br>• Production: ELK stack or Datadog |

### Why a Local Qwen2.5-VL Model over API-based LLMs?

1. **Cost**: No per-token charges, unlimited inference
2. **Privacy**: Sensitive banking data stays on-premises
3. **Latency**: No network round-trip to external APIs
4. **Compliance**: Meets regulatory requirements for data locality
5. **Scalability**: Can deploy multiple instances without API rate limits

### Trade-offs Considered

| Decision | Alternative | Why Chosen |
|----------|------------|------------|
| Qwen2.5-VL-7B-Instruct | GPT-4, Claude | Local deployment, multimodal, no API costs, data privacy |
| Tesseract OCR | AWS Textract | Free, good quality, sufficient for prototype |
| SQLite | PostgreSQL | Simpler setup, production-ready migration path |
| Vanilla JS | React | Faster prototype, no build complexity |

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9+
- pip
- Git
- Tesseract OCR
- (Optional) CUDA-compatible GPU for faster inference

### Step 1: Clone Repository

```bash
cd /home/adubey
# Repository is already in iasw-project/
cd iasw-project
```

### Step 2: Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

#### macOS
```bash
brew install tesseract poppler
```

### Step 3: Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 4: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Download the Qwen2.5-VL Model (optional)

Fast mode is **on by default** (`IASW_FAST_MODE=1`) and skips the model entirely, so the app runs end-to-end without any download. Only follow this step if you want the full VL pipeline.

```bash
# Set your Hugging Face token (get from https://huggingface.co/settings/tokens)
export HF_TOKEN="your_huggingface_token_here"

# Download Qwen2.5-VL-7B-Instruct (~15 GB; saved to llama-models/qwen2.5-vl-7b-instruct/
# — the legacy folder name is preserved to avoid breaking existing paths)
huggingface-cli download Qwen/Qwen2.5-VL-7B-Instruct --local-dir llama-models/qwen2.5-vl-7b-instruct
```

**Note**: the model is ~15 GB. Download takes 20-60 minutes depending on connection. Then start the backend with `IASW_FAST_MODE=0` to use it.

### Step 6: Verify Installation

```bash
# Check Tesseract
tesseract --version

# Check Python packages
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
```

---

## ▶️ Running the Application

### Start Backend Server

```bash
# From project root
source venv/bin/activate  # If not already activated

# Start FastAPI server
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server will start at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### Start Frontend

Open another terminal:

```bash
cd frontend

# Start simple HTTP server
python3 -m http.server 3000
```

Frontend will be available at: **http://localhost:3000**

---

## 🎬 Working Flow Demo: Legal Name Change

### Test Scenario
**Customer**: Priya Sharma (Customer ID: C001)  
**Request**: Legal name change to "Priya Mehta" (post-marriage)  
**Document**: Marriage Certificate  

### Step-by-Step Execution

#### 1. Prepare Test Document

Create a sample marriage certificate image or PDF with text like:

```
GOVERNMENT OF INDIA
MARRIAGE CERTIFICATE

This is to certify that the marriage between:

Bride Name: Priya Sharma
Date of Birth: 15-May-1990

AND

Groom Name: Rahul Mehta
Date of Birth: 10-March-1988

Was solemnized on 12th June 2025

Married Name: Priya Mehta

Certificate No: MC-2025-12345
Issued By: Municipal Corporation
```

Save as `test_marriage_cert.pdf` or `test_marriage_cert.jpg`

#### 2. Submit Request via Frontend

1. Open http://localhost:3000
2. Go to "Submit Request" tab
3. Fill form:
   - Customer ID: `C001`
   - Change Type: `Legal Name Change`
   - Current Value: `Priya Sharma`
   - New Value: `Priya Mehta`
   - Staff ID: `STAFF001`
   - Notes: `Post-marriage name change`
   - Upload document: `test_marriage_cert.pdf`
4. Click "Submit Request"

#### 3. Backend Processing (Automatic)

Check backend console for logs:

```
================================================================================
NEW CHANGE REQUEST RECEIVED
================================================================================
Customer: C001
Change Type: legal_name
Old Value: Priya Sharma
New Value: Priya Mehta

🔍 STEP 1: Validating request against RPS...
✅ Validation passed

📝 STEP 2: Processing document with AI...
   OCR confidence: 87.3%
   Extracted: old_name=Priya Sharma, new_name=Priya Mehta
✅ Document processed

📊 STEP 3: Generating confidence score card...
   Overall confidence: 97.2%
   Recommendation: approve
✅ Score card generated

💾 STEP 4: Staging request for checker approval...
✅ Request staged: REQ-1735564800-a1b2c3d4
================================================================================
```

#### 4. Checker Review

1. Switch to "Checker Review" tab
2. Click "Refresh" to load pending requests
3. Review the request card showing:
   - Confidence score: **97.2%**
   - AI recommendation: **APPROVE**
   - Field scores:
     - old_name: **PASS** (99%)
     - new_name: **PASS** (99%)
     - document_number: **PASS** (90%)
     - ocr_quality: **PASS** (87.3%)
   - Forgery check: **✅ PASSED**
   - AI Summary: *"Marriage Certificate verified. Old name matches bride field. New name matches married name field. Confidence: 97%. Recommended: Approve."*

#### 5. Human Approval (HITL)

1. Click "✅ Approve & Execute"
2. Enter Checker ID: `CHECKER001`
3. Optional notes: `Verified marriage certificate. All checks passed.`
4. Click "Confirm"

#### 6. RPS Update (Only After Human Approval)

Backend console logs:

```
================================================================================
CHECKER DECISION RECEIVED
================================================================================
Request ID: REQ-1735564800-a1b2c3d4
Checker: CHECKER001
Decision: approve

✅ APPROVED - Initiating RPS update...

================================================================================
RPS UPDATE INITIATED
================================================================================
Customer ID: C001
Field: legal_name
Old Value: Priya Sharma
New Value: Priya Mehta
Approved By: CHECKER001
Request ID: REQ-1735564800-a1b2c3d4
================================================================================
✅ RPS UPDATE SUCCESSFUL: RPS-TXN-1735564850
================================================================================
```

#### 7. Verification

Check database:

```bash
sqlite3 backend/iasw.db

SELECT request_id, status, overall_confidence, ai_recommendation 
FROM pending_requests;

SELECT request_id, rps_updated, rps_transaction_id 
FROM approved_requests;

SELECT action, actor, timestamp 
FROM audit_logs 
WHERE request_id = 'REQ-1735564800-a1b2c3d4';
```

---

## 🔒 HITL Boundary Design

### Critical Constraint

**The AI must NEVER perform the final write-call to the core banking system (RPS) autonomously.**

### Enforcement Mechanisms

#### 1. Code-Level Enforcement

```python
# backend/main.py - Checker Decision Endpoint

@app.post("/api/checker/decision")
async def submit_checker_decision(decision: CheckerDecision):
    """
    CRITICAL: This is the HUMAN-IN-THE-LOOP boundary.
    Only upon explicit human approval will the RPS write-call be triggered.
    """
    
    if decision.decision.lower() == "approve":
        # ONLY NOW do we call RPS
        rps_response = rps_service.update_customer_record(...)
```

**Key Point**: The `rps_service.update_customer_record()` function is ONLY called inside the `submit_checker_decision` endpoint, which requires explicit human input.

#### 2. Database Status Workflow

```
Status Flow:
initiated → ai_processing → ai_verified_pending_human → [HITL GATE] → approved/rejected
                                                              ↑
                                                      Human Decision Required
```

#### 3. API Design

- **AI Agents**: Can only write to `pending_requests` table with status `AI_VERIFIED_PENDING_HUMAN`
- **Checker Endpoint**: Only endpoint that can trigger RPS update
- **Audit Trail**: Every action logged with `actor` field (`ai_agent` vs `CHECKER_ID`)

#### 4. UI Design

The Checker UI explicitly shows:
- "Approve & Execute" button makes clear that clicking executes RPS update
- Modal confirmation before final action
- No auto-approval even for 100% confidence

### What AI Can Do Autonomously

✅ OCR extraction  
✅ Data extraction  
✅ Confidence scoring  
✅ Forgery detection  
✅ Recommendation generation  
✅ Writing to `pending_requests` table  

### What AI Cannot Do

❌ **Approve requests** - Only human checker  
❌ **Update RPS** - Only after human approval  
❌ **Auto-execute high-confidence requests** - Always requires human  
❌ **Skip checker review** - Mandatory for all requests  

### Production Enhancements

- **Multi-level approval** for high-value changes
- **Regulatory compliance logs** (immutable, signed)
- **API key separation** (AI agents cannot access RPS API keys)
- **Network segmentation** (AI inference servers cannot reach RPS)

---

## 📊 Observability & Logging

### Logging Strategy

#### 1. Structured Logging

```python
# All agents log with:
logger.info(f"Action: {action}, Actor: {actor}, Request: {request_id}, Result: {result}")
```

#### 2. Log Levels

- **INFO**: Normal workflow steps
- **WARNING**: Confidence flags, validation warnings
- **ERROR**: Processing failures, API errors
- **DEBUG**: Detailed AI responses (disabled in production)

#### 3. Log Files

```
logs/
  ├── iasw.log          # Main application log
  └── [rotating backups]
```

#### 4. Audit Database

Every significant action logged to `audit_logs` table:

```sql
CREATE TABLE audit_logs (
    id VARCHAR PRIMARY KEY,
    request_id VARCHAR NOT NULL,
    action VARCHAR NOT NULL,           -- "request_submitted", "approved", etc.
    actor VARCHAR NOT NULL,            -- "STAFF001", "CHECKER001", "ai_agent"
    details JSON,
    timestamp DATETIME DEFAULT NOW
);
```

### Observability Features

| Feature | Implementation | Production Upgrade |
|---------|---------------|-------------------|
| **Request Tracing** | Unique request_id in all logs | OpenTelemetry distributed tracing |
| **Confidence Tracking** | Field-level scores in database | Prometheus metrics dashboard |
| **Agent Performance** | Processing time logged | APM tools (Datadog, New Relic) |
| **Error Tracking** | Exception logs with stack traces | Sentry error tracking |
| **Audit Trail** | Immutable audit_logs table | Blockchain-based audit log |

### Monitoring Queries

```python
# Average confidence score
SELECT AVG(overall_confidence) FROM pending_requests;

# Approval rate
SELECT 
    COUNT(CASE WHEN status = 'approved' THEN 1 END) * 100.0 / COUNT(*) as approval_rate
FROM pending_requests 
WHERE status IN ('approved', 'rejected');

# Processing time by agent
SELECT action, AVG(processing_time_ms) FROM audit_logs GROUP BY action;

# Forgery detection rate
SELECT 
    COUNT(CASE WHEN forgery_check_passed = 0 THEN 1 END) * 100.0 / COUNT(*) as forgery_rate
FROM pending_requests;
```

---

## ⚠️ Assumptions, Constraints & Known Limitations

### Assumptions

1. **Document Quality**: OCR assumes reasonable image quality (300+ DPI recommended)
2. **Customer Pre-existence**: All customers exist in RPS before change requests
3. **Single Document**: One supporting document per request (production may need multiple)
4. **English Language**: OCR and LLM optimized for English (can be extended)
5. **Synchronous Processing**: Entire workflow completes in single HTTP request (production should use async)
6. **Network Availability**: Frontend and backend on same network

### Constraints

1. **Model Size**: Qwen2.5-VL 7B is smaller than GPT-4 / Claude Opus, less nuanced understanding
2. **OCR Accuracy**: Tesseract may struggle with handwritten text or poor scans
3. **Forgery Detection**: Rule-based, not deep learning (production needs CV models)
4. **Scalability**: Single-process server, not horizontally scaled
5. **Authentication**: No auth layer (production needs OAuth/SAML)

### Known Limitations

#### 1. Qwen2.5-VL Model Performance

- **Issue**: 7B multimodal model on CPU is slow (~10 min per submission) and may miss subtle context
- **Mitigation**: `IASW_FAST_MODE=1` (default) bypasses the model and uses regex-over-OCR for demo speed; JSON extraction has fallback parsing
- **Production Fix**: Upgrade to a larger VL model, run on GPU, or fine-tune on banking documents

#### 2. OCR Quality

- **Issue**: Tesseract accuracy varies with document quality
- **Mitigation**: OCR confidence score flagged below 80%
- **Production Fix**: AWS Textract or Google Document AI (99%+ accuracy)

#### 3. Forgery Detection

- **Issue**: Current implementation is basic (text pattern analysis)
- **Mitigation**: Flags suspicious patterns for manual review
- **Production Fix**: Integrate CV models (ResNet, EfficientNet) trained on fake documents

#### 4. Concurrency

- **Issue**: SQLite doesn't handle high concurrent writes well
- **Mitigation**: Sufficient for prototype and testing
- **Production Fix**: PostgreSQL with connection pooling

#### 5. Document Types

- **Issue**: Only marriage certificate logic implemented
- **Mitigation**: Architecture supports adding new document types
- **Production Fix**: Document type detection + type-specific extractors

#### 6. Error Recovery

- **Issue**: No retry logic for transient failures
- **Mitigation**: Errors logged for manual review
- **Production Fix**: Celery task queue with automatic retries

#### 7. Data Privacy

- **Issue**: No encryption at rest
- **Mitigation**: Local deployment limits exposure
- **Production Fix**: Database encryption + document encryption in FileNet

---

## 📐 Data Model

### Pending Requests Table

```sql
CREATE TABLE pending_requests (
    request_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR NOT NULL,
    change_type ENUM('legal_name', 'address', 'date_of_birth', 'contact_email'),
    old_value VARCHAR(500),
    new_value VARCHAR(500),
    document_id VARCHAR,
    filenet_reference VARCHAR,
    overall_confidence FLOAT,
    field_scores JSON,              -- Array of FieldConfidence objects
    forgery_check_passed BOOLEAN,
    forgery_confidence FLOAT,
    ai_recommendation VARCHAR(50),  -- 'approve', 'reject', 'manual_review'
    ai_summary TEXT,
    status ENUM(...),
    checker_id VARCHAR,
    checker_decision VARCHAR,
    checker_notes TEXT,
    created_at TIMESTAMP,
    processed_at TIMESTAMP,
    updated_at TIMESTAMP,
    staff_id VARCHAR,
    request_notes TEXT
);
```

### Approved Requests Table

```sql
CREATE TABLE approved_requests (
    request_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR,
    change_type ENUM(...),
    old_value VARCHAR,
    new_value VARCHAR,
    checker_id VARCHAR,
    checker_decision VARCHAR,
    checker_notes TEXT,
    filenet_reference VARCHAR,
    confidence_score FLOAT,
    rps_updated BOOLEAN,
    rps_update_timestamp TIMESTAMP,
    rps_response JSON,
    approved_at TIMESTAMP,
    created_at TIMESTAMP
);
```

---

## 🧪 Testing

### Manual Test Cases

#### Test Case 1: Happy Path (Name Change)
- **Input**: Valid customer, matching document, high OCR quality
- **Expected**: 90%+ confidence, AI recommends approve, checker approves, RPS updated
- **Status**: ✅ Implemented

#### Test Case 2: Low Confidence
- **Input**: Poor document quality, OCR confidence <60%
- **Expected**: Low confidence score, AI recommends manual review
- **Status**: ✅ Implemented (flagging logic)

#### Test Case 3: Forgery Detection
- **Input**: Document with suspicious patterns
- **Expected**: Forgery flag raised, AI recommends reject
- **Status**: ⚠️ Basic implementation (needs CV model)

#### Test Case 4: Validation Failure
- **Input**: Customer ID not in RPS, or old_value mismatch
- **Expected**: Request rejected at validation stage
- **Status**: ✅ Implemented

#### Test Case 5: Checker Rejection
- **Input**: Valid request but checker rejects
- **Expected**: No RPS update, status=rejected, audit logged
- **Status**: ✅ Implemented

### Future Automated Testing

```python
# pytest test suite (skeleton)
def test_validation_agent():
    """Test validation against mock RPS"""
    pass

def test_ocr_extraction():
    """Test OCR on sample documents"""
    pass

def test_confidence_scoring():
    """Test confidence calculation logic"""
    pass

def test_hitl_boundary():
    """Verify RPS never called without checker approval"""
    pass
```

---

## 📦 Deliverables Checklist

- [✅] Working prototype code
- [✅] README.md with setup instructions
- [✅] Architecture diagram (ASCII art + description)
- [✅] Agent design documentation
- [✅] Complete Legal Name Change flow
- [✅] Local Qwen2.5-VL model integration
- [✅] Frontend for staff and checker
- [✅] Database schema with audit logs
- [✅] Mock RPS and FileNet services
- [✅] Comprehensive logging
- [✅] HITL boundary enforcement
- [✅] Assumptions and limitations documented

---

## 🚀 Future Enhancements

### Phase 2 Features
1. Support for Address, DOB, Contact changes
2. Multi-document requests
3. Real FileNet integration
4. Real RPS integration
5. Advanced forgery detection (CV models)

### Phase 3 Features
1. Batch processing
2. Scheduled reports
3. Analytics dashboard
4. API rate limiting
5. Multi-tenancy support

### Phase 4 Features
1. Mobile app for document upload
2. Real-time notifications
3. Integration with CRM systems
4. Machine learning model retraining pipeline
5. Compliance reporting automation

---

## 📞 Support & Questions

For questions or issues:
- Check logs in `logs/iasw.log`
- Review database with `sqlite3 backend/iasw.db`
- Verify Qwen2.5-VL model: `ls -lh llama-models/qwen2.5-vl-7b-instruct/` (folder kept under `llama-models/` for backward compatibility)

---

## 📄 License

This is a technical challenge solution for educational purposes.

---

**Built with 💙 for AI Product Engineer Position**

*Demonstrating production-grade agentic AI architecture with strict HITL compliance.*
