# IASW - Demo Guide

**Step-by-Step Guide to Running the Complete Demo**

---

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.9+ installed
- [ ] pip installed
- [ ] Tesseract OCR installed
- [ ] 8GB+ RAM available (for Llama model)
- [ ] 10GB+ free disk space (for model download)
- [ ] Internet connection (for model download)

### Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

#### macOS
```bash
brew install tesseract poppler
```

---

## Setup (15-30 minutes)

### Step 1: Quick Setup

```bash
cd /home/adubey/iasw-project

# Run automated setup
./quickstart.sh
```

This will:
- Create virtual environment
- Install Python dependencies
- Create required directories
- Generate test certificate
- Check prerequisites

### Step 2: Download Llama Model (~10-20 minutes)

**Important**: You need a Hugging Face account and token.

1. Create account: https://huggingface.co/join
2. Generate token: https://huggingface.co/settings/tokens
3. Accept Llama license: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct

Then:

```bash
# Set your token
export HF_TOKEN="hf_your_token_here"

# Download model (~7GB)
python download_llama.py
```

**Expected Output**:
```
================================================================================
IASW - Llama Model Download Script
================================================================================

📥 Downloading model: meta-llama/Llama-3.2-3B-Instruct
📁 Target directory: ./llama-models/llama-3.2-3b-instruct

This may take several minutes depending on your connection...
--------------------------------------------------------------------------------
[Progress bar...]

================================================================================
✅ Model downloaded successfully!
📁 Location: /home/adubey/iasw-project/llama-models/llama-3.2-3b-instruct
================================================================================
```

---

## Running the Application

### Terminal 1: Backend Server

```bash
cd /home/adubey/iasw-project
source venv/bin/activate  # Activate virtual environment

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend is ready at**: http://localhost:8000

**API Documentation**: http://localhost:8000/docs (Swagger UI)

### Terminal 2: Frontend Server

```bash
cd /home/adubey/iasw-project/frontend
python3 -m http.server 3000
```

**Expected Output**:
```
Serving HTTP on 0.0.0.0 port 3000 (http://0.0.0.0:3000/) ...
```

**Frontend is ready at**: http://localhost:3000

---

## Complete Demo Flow: Legal Name Change

### Scenario

**Customer**: Priya Sharma (ID: C001)  
**Change**: Legal name change to "Priya Mehta" after marriage  
**Document**: Marriage certificate  

### Part 1: Staff Submission (5 minutes)

1. **Open Frontend**: http://localhost:3000

2. **Select "Submit Request" Tab** (should be active by default)

3. **Fill the Form**:
   - Customer ID: `C001`
   - Change Type: Select `Legal Name Change`
   - Current Value: `Priya Sharma`
   - New Value: `Priya Mehta`
   - Staff ID: `STAFF001`
   - Notes: `Post-marriage name change, verified customer in person`

4. **Upload Document**:
   - Click the upload area or drag-and-drop
   - Select: `data/documents/test_marriage_certificate.png`
   - Confirm file name appears below upload area

5. **Click "Submit Request"**

6. **Watch Backend Console** (Terminal 1):

```
================================================================================
NEW CHANGE REQUEST RECEIVED
================================================================================
Customer: C001
Change Type: legal_name
Old Value: Priya Sharma
New Value: Priya Mehta
Staff: STAFF001
Document: test_marriage_certificate.png

🔍 STEP 1: Validating request against RPS...
✅ Validation passed (warnings: 0)

📄 Document saved: data/documents/REQ-xxx_test_marriage_certificate.png

📝 STEP 2: Processing document with AI...
   OCR confidence: 87.3%
   Extracted: old_name=Priya Sharma, new_name=Priya Mehta
✅ Document processed: confidence=87.3%

📊 STEP 3: Generating confidence score card...
✅ Score card generated: 97.2% confidence
   Recommendation: approve

💾 STEP 4: Staging request for checker approval...
✅ Request staged: REQ-1735564800-a1b2c3d4
================================================================================
```

7. **Verify Success Message** in Frontend:

```
✅ Request submitted successfully!
Request ID: REQ-1735564800-a1b2c3d4
Confidence Score: 97.20%
AI Recommendation: APPROVE
Status: Awaiting checker approval
```

**⏱️ Expected Time**: 5-10 seconds for AI processing

---

### Part 2: Checker Review (3 minutes)

1. **Switch to "Checker Review" Tab**

2. **Click "🔄 Refresh"** to load pending requests

3. **Review the Request Card**:

   **Header**:
   - Request ID: `REQ-1735564800-a1b2c3d4`
   - Confidence Badge: `97.2% Confidence` (green)

   **Request Details**:
   - Customer ID: C001
   - Change Type: LEGAL NAME
   - Old Value: Priya Sharma
   - New Value: **Priya Mehta** (bold)
   - AI Recommendation: **APPROVE**
   - Forgery Check: ✅ PASSED
   - FileNet Reference: FN-xxx
   - Submitted By: STAFF001
   - Created: [timestamp]

   **AI Summary**:
   > 🤖 AI Summary:  
   > Marriage Certificate verified. Old name 'Priya Sharma' matches bride field with 99% confidence. New name 'Priya Mehta' matches married name field with 99% confidence. Overall confidence: 97.2%. Forgery check passed. Recommended: APPROVE.

   **Field-Level Scores**:
   - old_name: PASS - 99.0%
   - new_name: PASS - 99.0%
   - document_number: PASS - 90.0%
   - ocr_quality: PASS - 87.3%

4. **Click "✅ Approve & Execute"**

5. **Confirmation Modal Appears**:
   - Title: "✅ Approve Request"
   - Message: "You are about to APPROVE this request and execute the RPS update..."
   - Checker ID field
   - Notes field (optional)

6. **Enter Details**:
   - Checker ID: `CHECKER001`
   - Notes: `Verified marriage certificate. All checks passed. Approving.`

7. **Click "Confirm"**

8. **Watch Backend Console** (Terminal 1):

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

9. **Verify Success in Frontend**:

```
✅ Decision processed successfully!
Request ID: REQ-1735564800-a1b2c3d4
Status: approved
RPS Transaction: RPS-TXN-1735564850
```

10. **Refresh Checker Tab** - The request should disappear (no longer pending)

---

### Part 3: Verification (2 minutes)

#### Check Database

```bash
cd /home/adubey/iasw-project
sqlite3 backend/iasw.db
```

**Query 1: Pending Request**
```sql
SELECT request_id, status, overall_confidence, ai_recommendation, checker_id
FROM pending_requests
WHERE request_id = 'REQ-1735564800-a1b2c3d4';
```

**Expected**:
```
REQ-1735564800-a1b2c3d4|approved|97.2|approve|CHECKER001
```

**Query 2: Approved Request**
```sql
SELECT request_id, old_value, new_value, rps_updated, checker_id
FROM approved_requests
WHERE request_id = 'REQ-1735564800-a1b2c3d4';
```

**Expected**:
```
REQ-1735564800-a1b2c3d4|Priya Sharma|Priya Mehta|1|CHECKER001
```

**Query 3: Audit Trail**
```sql
SELECT action, actor, timestamp
FROM audit_logs
WHERE request_id = 'REQ-1735564800-a1b2c3d4'
ORDER BY timestamp;
```

**Expected**:
```
request_submitted|STAFF001|2025-06-12 10:15:23
approved_and_executed|CHECKER001|2025-06-12 10:18:46
```

#### Check Logs

```bash
tail -n 50 /home/adubey/iasw-project/logs/iasw.log
```

Look for:
- Validation steps
- OCR processing
- Confidence scoring
- Checker decision
- RPS update

---

## Alternative Test Cases

### Test Case 2: Low Confidence (Manual Review)

Use a poorly scanned document or create one with mismatched names:

```
Old Name: Priya Sharma
New Name: Priya Singh  # Different last name
```

**Expected**:
- Lower confidence score (~60-80%)
- AI recommendation: MANUAL_REVIEW
- Checker must still review

### Test Case 3: Rejection by Checker

Follow normal flow but:
- Checker clicks "❌ Reject" instead
- Enter reason: "Document quality insufficient"

**Expected**:
- Status: REJECTED
- No RPS update
- Audit log shows rejection

### Test Case 4: Validation Failure

Try submitting with:
- Customer ID: `C999` (doesn't exist)

**Expected**:
- Request rejected immediately
- Error message: "Customer C999 not found in RPS"

---

## Troubleshooting

### Issue: Backend won't start

**Error**: `ImportError: No module named 'transformers'`

**Solution**:
```bash
source venv/bin/activate  # Make sure venv is activated
pip install -r requirements.txt
```

---

### Issue: Llama model not found

**Error**: `FileNotFoundError: Model not found at ./llama-models/...`

**Solution**:
```bash
# Download model
export HF_TOKEN="your_token"
python download_llama.py
```

---

### Issue: OCR fails

**Error**: `TesseractNotFoundError`

**Solution**:
```bash
# Ubuntu
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify
tesseract --version
```

---

### Issue: Frontend can't connect to backend

**Error**: Network error in browser console

**Solution**:
1. Check backend is running: http://localhost:8000/health
2. Check CORS settings in `backend/main.py`
3. Check browser console for actual error

---

### Issue: Slow processing (>30 seconds)

**Cause**: Llama model running on CPU

**Solution**:
- **Accept it**: CPU inference is slower but works
- **Upgrade**: Use GPU-enabled machine
- **Optimize**: Use smaller model or quantized version

---

## Performance Expectations

| Operation | Time (CPU) | Time (GPU) |
|-----------|-----------|-----------|
| Model loading | 30-60s | 10-20s |
| OCR extraction | 1-2s | 1-2s |
| LLM inference (single) | 3-5s | 0.5-1s |
| Total request | 5-10s | 2-4s |

---

## Demo Script (For Presentation)

**Opening** (1 min):
> "I'll demonstrate the Intelligent Account Servicing Workflow - an AI system that automates banking document verification while maintaining human oversight."

**Staff Submission** (2 min):
> "A customer, Priya Sharma, wants to change her name to Priya Mehta after marriage. Staff submits the request with a marriage certificate..."
> [Perform submission]
> "The system validated against RPS, performed OCR, extracted data using local Llama, scored confidence at 97%, and recommends approval."

**Checker Review** (2 min):
> "The human checker now reviews the AI's analysis. They see the confidence scores, field-level details, and AI summary..."
> [Show review card]
> "This is the Human-in-the-Loop boundary. The AI cannot update the core banking system without explicit approval."

**Approval** (1 min):
> "The checker approves, enters their ID, and confirms..."
> [Perform approval]
> "Only now does the RPS update occur. The system logs the transaction, updates the database, and creates an immutable audit trail."

**Verification** (1 min):
> "We can verify in the database that the request was approved, RPS was updated, and every action was logged with the responsible actor."
> [Show database queries]

**Closing** (1 min):
> "This demonstrates a production-grade agentic AI system with strict HITL compliance, using a local Llama model for cost-effective, private inference."

---

## Next Steps

After successful demo:

1. **Review Code**: Check `backend/main.py` for orchestration logic
2. **Review Agents**: See `backend/agents/` for AI logic
3. **Review Architecture**: Read `SOLUTION_DOCUMENT.md`
4. **Experiment**: Try different documents, confidence scenarios
5. **Extend**: Add new change types (address, DOB)

---

## Demo Video (Suggested)

If recording a video demo:

1. **Intro** (30s): Show frontend, explain purpose
2. **Submit** (1min): Fill form, upload doc, submit
3. **Process** (30s): Show backend logs processing
4. **Review** (1min): Show checker UI with AI analysis
5. **Approve** (30s): Human approval and RPS update
6. **Verify** (30s): Database queries and logs
7. **Outro** (30s): Summarize HITL compliance

**Total**: ~5 minutes

---

**Good luck with the demo! This system demonstrates production-grade agentic AI with real-world constraints.**
