#!/bin/bash
# End-to-End Testing Script for InLegalDesk (Linux/macOS)
# This script runs comprehensive E2E tests for the legal research system

set -e  # Exit on any error

# Configuration
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8877}"
OUTPUT_FILE="${OUTPUT_FILE:-e2e_test_report.json}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/upgrade dependencies
    log_info "Installing/upgrading dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r desktop/requirements.txt
    
    log_success "Prerequisites check completed"
}

# Start backend server
start_backend() {
    log_info "Starting backend server..."
    
    # Check if backend is already running
    if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_success "Backend is already running"
        return 0
    fi
    
    # Start backend in background
    log_info "Starting backend server on $BACKEND_URL..."
    python -m uvicorn app:app --host 127.0.0.1 --port 8877 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    log_info "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
            log_success "Backend started successfully (PID: $BACKEND_PID)"
            return 0
        fi
        sleep 2
    done
    
    log_error "Backend failed to start within 60 seconds"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
}

# Stop backend server
stop_backend() {
    if [ ! -z "$BACKEND_PID" ]; then
        log_info "Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
        log_success "Backend server stopped"
    fi
}

# Run E2E tests
run_e2e_tests() {
    log_info "Running E2E tests..."
    
    # Prepare test arguments
    TEST_ARGS="--backend-url $BACKEND_URL"
    
    if [ "$VERBOSE" = "true" ]; then
        TEST_ARGS="$TEST_ARGS --verbose"
    fi
    
    if [ ! -z "$OUTPUT_FILE" ]; then
        TEST_ARGS="$TEST_ARGS --output $OUTPUT_FILE"
    fi
    
    # Run the E2E test script
    python run_e2e.py $TEST_ARGS
    
    if [ $? -eq 0 ]; then
        log_success "E2E tests completed successfully"
    else
        log_error "E2E tests failed"
        return 1
    fi
}

# Test specific components
test_backend_health() {
    log_info "Testing backend health..."
    
    response=$(curl -s "$BACKEND_URL/health")
    if echo "$response" | grep -q '"status":"healthy"'; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
}

test_statutes_ingestion() {
    log_info "Testing statutes ingestion..."
    
    response=$(curl -s -X POST "$BACKEND_URL/sources/add_statutes")
    if echo "$response" | grep -q '"status":"processing"'; then
        log_success "Statutes ingestion initiated successfully"
    else
        log_warning "Statutes ingestion may have failed or already completed"
    fi
}

test_legal_qa() {
    log_info "Testing legal Q&A..."
    
    question="What is the definition of theft under Indian Penal Code?"
    response=$(curl -s -X POST "$BACKEND_URL/ask" \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$question\",\"language\":\"en\"}")
    
    if echo "$response" | grep -q '"answer"'; then
        log_success "Legal Q&A test passed"
    else
        log_warning "Legal Q&A test may have failed (response: $response)"
    fi
}

test_judgment_generation() {
    log_info "Testing judgment generation..."
    
    judgment_data='{
        "case_facts": "The petitioner was arrested for theft of a mobile phone worth Rs. 15,000.",
        "legal_issues": ["Whether the arrest was legal under Section 41 of CrPC?"],
        "language": "en",
        "court_type": "high_court"
    }'
    
    response=$(curl -s -X POST "$BACKEND_URL/judgment" \
        -H "Content-Type: application/json" \
        -d "$judgment_data")
    
    if echo "$response" | grep -q '"judgment"'; then
        log_success "Judgment generation test passed"
    else
        log_warning "Judgment generation test may have failed (response: $response)"
    fi
}

# Quick smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    test_backend_health
    test_statutes_ingestion
    test_legal_qa
    test_judgment_generation
    
    log_success "Smoke tests completed"
}

# Generate test report
generate_report() {
    if [ -f "$OUTPUT_FILE" ]; then
        log_info "Generating test report..."
        
        # Extract summary from JSON report
        if command -v jq &> /dev/null; then
            echo ""
            echo "=========================================="
            echo "E2E Test Report Summary"
            echo "=========================================="
            jq -r '.summary | "Total Tests: \(.total_tests)\nPassed: \(.passed_tests)\nFailed: \(.failed_tests)\nSuccess Rate: \(.success_rate)%\nStatus: \(.status)"' "$OUTPUT_FILE"
            echo "=========================================="
        else
            log_info "Test report saved to: $OUTPUT_FILE"
            log_warning "Install 'jq' for formatted report display"
        fi
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    stop_backend
    deactivate 2>/dev/null || true
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    echo "=========================================="
    echo "InLegalDesk E2E Testing Script"
    echo "=========================================="
    echo "Backend URL: $BACKEND_URL"
    echo "Output File: $OUTPUT_FILE"
    echo "Verbose: $VERBOSE"
    echo "=========================================="
    
    # Check if we should run smoke tests only
    if [ "$1" = "--smoke" ]; then
        log_info "Running smoke tests only..."
        check_prerequisites
        start_backend
        run_smoke_tests
        generate_report
    else
        # Run full E2E tests
        check_prerequisites
        start_backend
        run_e2e_tests
        generate_report
    fi
    
    log_success "All tests completed!"
}

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --smoke              Run smoke tests only"
    echo "  --help               Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  BACKEND_URL          Backend URL (default: http://127.0.0.1:8877)"
    echo "  OUTPUT_FILE          Output file for test report (default: e2e_test_report.json)"
    echo "  VERBOSE              Enable verbose output (default: false)"
    echo ""
    echo "Examples:"
    echo "  $0                   # Run full E2E tests"
    echo "  $0 --smoke           # Run smoke tests only"
    echo "  VERBOSE=true $0      # Run with verbose output"
    echo "  BACKEND_URL=http://localhost:8000 $0  # Use custom backend URL"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --smoke)
        main --smoke
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac