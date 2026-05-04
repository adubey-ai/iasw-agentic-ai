#!/bin/bash
# Start both IASW Backend and Frontend servers

echo "=============================================="
echo "IASW - Starting All Services"
echo "=============================================="
echo ""
echo "This will start:"
echo "  - Backend API server on http://localhost:8000"
echo "  - Frontend UI server on http://localhost:3000"
echo ""
echo "Using Qwen2.5-VL-7B-Instruct (multimodal)"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=============================================="
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    wait
    echo "All servers stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo "Starting backend server..."
./start_backend.sh &
BACKEND_PID=$!

# Wait a bit for backend to initialize
sleep 3

# Start frontend in background
echo "Starting frontend server..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "=============================================="
echo "✅ All servers started!"
echo "=============================================="
echo ""
echo "Backend API: http://localhost:8000"
echo "Backend Docs: http://localhost:8000/docs"
echo "Frontend UI: http://localhost:3000"
echo ""
echo "Test credentials:"
echo "  Customer ID: C001"
echo "  Old Name: Priya Sharma"
echo "  New Name: Priya Mehta"
echo "  Document: Upload test_marriage_certificate.png"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=============================================="
echo ""

# Wait for both processes
wait
