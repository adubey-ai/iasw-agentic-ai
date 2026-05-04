#!/bin/bash
# Start IASW Backend Server

echo "=============================================="
echo "Starting IASW Backend Server"
echo "=============================================="
echo ""

# Get script directory and cd to it
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

echo "✅ Using Qwen2.5-VL-7B-Instruct (multimodal, CPU/GPU auto-detect)"
echo "✅ Device: $(python3 -c 'import torch; print("CUDA" if torch.cuda.is_available() else "CPU")')"
echo ""
echo "Starting server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Start server from project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
