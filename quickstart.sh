#!/bin/bash
# IASW Quick Start Script

echo "=============================================="
echo "IASW - Quick Start Setup"
echo "=============================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"
echo ""

# Check Tesseract
echo "Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract --version | head -n 1
    echo "✅ Tesseract found"
else
    echo "❌ Tesseract not found. Please install:"
    echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   macOS: brew install tesseract"
fi
echo ""

# Create directories
echo "Creating required directories..."
mkdir -p data/documents data/pending data/approved logs llama-models
echo "✅ Directories created"
echo ""

# Create test document
echo "Creating test marriage certificate..."
python3 create_test_document.py
echo ""

# Check if Llama model exists
echo "Checking Llama model..."
if [ -d "llama-models/llama-3.2-3b-instruct" ] && [ "$(ls -A llama-models/llama-3.2-3b-instruct)" ]; then
    echo "✅ Llama model found"
else
    echo "⚠️  Llama model not found"
    echo ""
    echo "To download the Llama model:"
    echo "1. Get HuggingFace token: https://huggingface.co/settings/tokens"
    echo "2. Set environment variable: export HF_TOKEN='your_token'"
    echo "3. Run: python download_llama.py"
    echo ""
    echo "NOTE: Model download is ~7GB and may take 10-30 minutes"
fi
echo ""

echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. If Llama model not downloaded:"
echo "   export HF_TOKEN='your_token'"
echo "   python download_llama.py"
echo ""
echo "2. Start backend server:"
echo "   cd backend"
echo "   python -m uvicorn main:app --reload"
echo ""
echo "3. In another terminal, start frontend:"
echo "   cd frontend"
echo "   python3 -m http.server 3000"
echo ""
echo "4. Open browser:"
echo "   http://localhost:3000"
echo ""
echo "Test credentials:"
echo "   Customer ID: C001"
echo "   Old Name: Priya Sharma"
echo "   New Name: Priya Mehta"
echo "   Upload: data/documents/test_marriage_certificate.png"
echo ""
echo "=============================================="
