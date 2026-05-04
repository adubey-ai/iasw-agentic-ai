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

export IASW_FAST_MODE="${IASW_FAST_MODE:-1}"
if [ "$IASW_FAST_MODE" = "1" ]; then
    echo "✅ Fast mode ON — skipping Qwen2.5-VL for sub-second submissions"
    echo "   Set IASW_FAST_MODE=0 to enable full VL pipeline"
else
    echo "✅ Using Qwen2.5-VL-7B-Instruct (multimodal, CPU/GPU auto-detect)"
    echo "✅ Device: $(python3 -c 'import torch; print("CUDA" if torch.cuda.is_available() else "CPU")')"
fi
echo ""
echo "Starting server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Start server from project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
