#!/bin/bash
set -e

# Start the backend server
echo "Starting backend server..."
cd /app
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start the frontend server
echo "Starting frontend server..."
cd /app
# Use the --single flag to support client-side routing
npx serve -s frontend/dist -l 5173 --single &
FRONTEND_PID=$!

# Function to handle script termination
cleanup() {
  echo "Shutting down servers..."
  kill $BACKEND_PID
  kill $FRONTEND_PID
  exit 0
}

# Register the cleanup function for when the script is terminated
trap cleanup SIGINT SIGTERM

# Keep the script running
echo "Both servers are running."
echo "Backend: http://0.0.0.0:8000"
echo "Frontend: http://0.0.0.0:5173"
echo "Press Ctrl+C to stop."
wait 