# IASW - Quick Start Guide

## ✅ Setup Complete!

Your system is configured with:
- **Python 3.12.3** with virtual environment
- **All dependencies installed** (FastAPI, PyTorch, Transformers, LangChain, etc.)
- **Tesseract OCR 5.3.4**
- **Llama 3.1 8B Instruct** model (ready to use)
- **Test data** created

---

## 🚀 Quick Start

### Option 1: Start Everything (Recommended)
```bash
./start_all.sh
```
This starts both backend and frontend servers together.

### Option 2: Start Separately

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

---

## 🌐 Access Points

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## 🧪 Test the System

Use these credentials to test the Legal Name Change workflow:

- **Customer ID:** `C001`
- **Old Name:** `Priya Sharma`
- **New Name:** `Priya Mehta`
- **Document:** Upload `data/documents/test_marriage_certificate.png`
- **Staff ID:** Any ID (e.g., `STAFF001`)

### Test Workflow:
1. Open http://localhost:3000
2. Fill in the form with test credentials above
3. Upload the test marriage certificate
4. Submit the request
5. View AI processing results with confidence scores
6. Approve/reject as a checker

---

## 📁 Project Structure

```
iasw-project/
├── backend/              # FastAPI backend
│   ├── agents/          # AI agents (validation, OCR, scoring)
│   ├── models/          # Data models
│   ├── services/        # Business services
│   └── utils/           # Utilities (LLM, OCR)
├── frontend/            # HTML/JS frontend
├── data/
│   ├── documents/       # Uploaded documents
│   ├── pending/         # Pending requests
│   └── approved/        # Approved requests
├── llama-models/
│   └── llama-3.1-8b-instruct/  # Llama 3.1 8B model
└── venv/                # Python virtual environment
```

---

## 🤖 AI Model Configuration

**Current Model:** Llama 3.1 8B Instruct
- **Location:** `./llama-models/llama-3.1-8b-instruct`
- **Device:** CPU (CUDA if available)
- **Capabilities:**
  - Document data extraction from OCR text
  - Name change verification
  - Forgery detection
  - Confidence scoring
  - Human-readable summaries

**To change model:** Edit `backend/utils/llm_handler.py` line 19

---

## 📋 System Features

### Maker-Checker Workflow
1. **Maker (Staff):** Initiates change request
2. **AI Agents:** Process and validate
3. **Checker (Supervisor):** Reviews and approves/rejects

### AI Agents
- **Validation Agent:** Checks RPS data
- **Document Processor:** OCR + LLM extraction
- **Confidence Scorer:** Generates confidence card
- **Forgery Detection:** Analyzes document authenticity

### Supported Changes
- Legal Name Change (Marriage Certificate, Deed Poll)
- More types can be added easily

---

## 🔧 Manual Commands

**Activate virtual environment:**
```bash
source venv/bin/activate
```

**Start backend manually:**
```bash
cd backend
python -m uvicorn main:app --reload
```

**Start frontend manually:**
```bash
cd frontend
python3 -m http.server 3000
```

**Check model info:**
```bash
python3 -c "from transformers import AutoTokenizer; t = AutoTokenizer.from_pretrained('./llama-models/llama-3.1-8b-instruct'); print(f'Vocab: {len(t)}')"
```

---

## 📊 Logs

- **Application logs:** `logs/iasw.log`
- **Backend console:** Real-time processing info

---

## 🛠️ Troubleshooting

**Port already in use:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

**Model loading issues:**
- Verify all 4 model shards exist in `llama-models/llama-3.1-8b-instruct/`
- Check available memory (model needs ~8-16GB RAM)

**OCR not working:**
```bash
tesseract --version  # Should show 5.3.4
```

---

## 📝 Next Steps

1. **Test the basic workflow** with provided test data
2. **Add more test documents** to `data/documents/`
3. **Customize confidence thresholds** in agents
4. **Add more change types** (address, phone, etc.)
5. **Connect to real database** (currently using file-based storage)
6. **Deploy with Gunicorn** for production

---

## 💡 Tips

- First request will be slower (model loading ~30-60 seconds)
- Subsequent requests are much faster
- Use GPU if available for better performance
- Check API docs at http://localhost:8000/docs for all endpoints

---

## 📧 Support

Check logs if something doesn't work:
- `logs/iasw.log` for detailed application logs
- Backend console for real-time output

---

**Happy Testing! 🎉**
