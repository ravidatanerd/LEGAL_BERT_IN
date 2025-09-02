#!/bin/bash
# End-to-end smoke tests for InLegalDesk backend

set -e

echo "Starting InLegalDesk E2E Tests..."

# Check if backend is running
echo "Checking if backend is running..."
if ! curl -s http://127.0.0.1:8877/health > /dev/null; then
    echo "Backend not running. Please start it first with:"
    echo "cd backend && python app.py"
    exit 1
fi

echo "Backend is running. Starting tests..."

# Run Python E2E tests
python run_e2e.py

echo "E2E tests completed successfully!"
echo "Check %TEMP%/judgment.md for generated judgment output"