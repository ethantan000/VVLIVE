#!/bin/bash
# Start VVLIVE services

echo "Starting VVLIVE..."

# Start backend
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Start frontend dev server (optional)
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo "Services running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"

wait