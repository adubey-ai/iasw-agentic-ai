#!/bin/bash
# Start IASW Frontend Server

echo "=============================================="
echo "Starting IASW Frontend Server"
echo "=============================================="
echo ""

# Get script directory and cd to it
cd "$(dirname "$0")"

# Change to frontend directory
cd frontend

echo "Starting server on http://localhost:3000"
echo ""
echo "Test credentials:"
echo "  Customer ID: C001"
echo "  Old Name: Priya Sharma"
echo "  New Name: Priya Mehta"
echo "  Document: data/documents/test_marriage_certificate.png"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Start frontend server
python3 -m http.server 3000
