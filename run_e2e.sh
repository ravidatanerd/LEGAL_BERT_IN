#!/bin/bash
# E2E Smoke Tests for InLegal Desktop Application
# This script tests the complete functionality of the application

set -e  # Exit on any error

echo "=========================================="
echo "InLegal Desktop E2E Smoke Tests"
echo "=========================================="

# Configuration
BACKEND_URL="http://127.0.0.1:8877"
TEST_PDF_PATH="test_documents/sample_case.pdf"
TEMP_DIR="/tmp/inlegal_test"
JUDGMENT_OUTPUT="$TEMP_DIR/judgment.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create temp directory
mkdir -p "$TEMP_DIR"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC}: $message"
    else
        echo -e "${YELLOW}ℹ INFO${NC}: $message"
    fi
}

# Function to check if backend is running
check_backend() {
    print_status "INFO" "Checking backend health..."
    
    if curl -s "$BACKEND_URL/health" > /dev/null; then
        print_status "PASS" "Backend is running and healthy"
        return 0
    else
        print_status "FAIL" "Backend is not running or not healthy"
        return 1
    fi
}

# Function to test sources status
test_sources_status() {
    print_status "INFO" "Testing sources status endpoint..."
    
    response=$(curl -s "$BACKEND_URL/sources/status")
    if echo "$response" | grep -q "total_documents"; then
        print_status "PASS" "Sources status endpoint working"
        echo "Response: $response"
    else
        print_status "FAIL" "Sources status endpoint failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test statute ingestion
test_statute_ingestion() {
    print_status "INFO" "Testing statute ingestion..."
    
    response=$(curl -s -X POST "$BACKEND_URL/sources/add_statutes")
    if echo "$response" | grep -q "message"; then
        print_status "PASS" "Statute ingestion started successfully"
        echo "Response: $response"
        
        # Wait a bit for ingestion to start
        print_status "INFO" "Waiting for statute ingestion to complete..."
        sleep 30
        
        # Check if documents were ingested
        documents_response=$(curl -s "$BACKEND_URL/documents")
        if echo "$documents_response" | grep -q "documents"; then
            print_status "PASS" "Documents were ingested successfully"
        else
            print_status "FAIL" "No documents found after ingestion"
            return 1
        fi
    else
        print_status "FAIL" "Statute ingestion failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test document upload
test_document_upload() {
    print_status "INFO" "Testing document upload..."
    
    # Create a test PDF if it doesn't exist
    if [ ! -f "$TEST_PDF_PATH" ]; then
        print_status "INFO" "Creating test PDF document..."
        mkdir -p "$(dirname "$TEST_PDF_PATH")"
        
        # Create a simple test PDF using Python
        python3 -c "
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create test PDF
c = canvas.Canvas('$TEST_PDF_PATH', pagesize=letter)
c.drawString(100, 750, 'Test Legal Document')
c.drawString(100, 700, 'This is a test document for InLegal E2E testing.')
c.drawString(100, 650, 'Section 1: Test Case Facts')
c.drawString(100, 600, 'The plaintiff filed a suit against the defendant.')
c.drawString(100, 550, 'Section 2: Legal Issues')
c.drawString(100, 500, '1. Whether the contract is valid?')
c.drawString(100, 450, '2. Whether damages are recoverable?')
c.save()
print('Test PDF created successfully')
" || {
            print_status "FAIL" "Failed to create test PDF"
            return 1
        }
    fi
    
    # Upload the test document
    response=$(curl -s -X POST -F "file=@$TEST_PDF_PATH" "$BACKEND_URL/upload")
    if echo "$response" | grep -q "document_id"; then
        print_status "PASS" "Document upload successful"
        echo "Response: $response"
        
        # Extract document ID for later use
        DOCUMENT_ID=$(echo "$response" | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)
        echo "Document ID: $DOCUMENT_ID"
    else
        print_status "FAIL" "Document upload failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test question answering
test_question_answering() {
    print_status "INFO" "Testing question answering..."
    
    # Test question about Evidence Act
    question='{"question": "What are the provisions regarding confessions in the Evidence Act?", "language": "auto", "max_sources": 5}'
    
    response=$(curl -s -X POST -H "Content-Type: application/json" -d "$question" "$BACKEND_URL/ask")
    if echo "$response" | grep -q "answer"; then
        print_status "PASS" "Question answering working"
        echo "Response preview: $(echo "$response" | head -c 200)..."
    else
        print_status "FAIL" "Question answering failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test judgment generation
test_judgment_generation() {
    print_status "INFO" "Testing judgment generation..."
    
    # Test judgment generation
    judgment_data='{
        "case_facts": "The plaintiff entered into a contract with the defendant for the sale of goods. The defendant failed to deliver the goods as per the contract terms.",
        "issues": ["Whether the contract is valid?", "Whether the defendant is liable for breach of contract?", "What are the damages recoverable?"],
        "language": "auto"
    }'
    
    response=$(curl -s -X POST -H "Content-Type: application/json" -d "$judgment_data" "$BACKEND_URL/judgment")
    if echo "$response" | grep -q "judgment"; then
        print_status "PASS" "Judgment generation working"
        
        # Save judgment to file
        echo "$response" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
judgment = data.get('judgment', {})
with open('$JUDGMENT_OUTPUT', 'w') as f:
    f.write('# Generated Judgment\n\n')
    f.write('## Case Facts\n')
    f.write(judgment.get('framing', '') + '\n\n')
    f.write('## Issues\n')
    for issue in judgment.get('points_for_determination', []):
        f.write(f'- {issue}\n')
    f.write('\n## Analysis\n')
    for analysis in judgment.get('court_analysis', []):
        f.write(f'### {analysis.get(\"issue\", \"\")}\n')
        f.write(f'{analysis.get(\"analysis\", \"\")}\n\n')
    f.write('## Relief\n')
    relief = judgment.get('relief', {})
    f.write(f'**Final Order:** {relief.get(\"final_order\", \"\")}\n')
"
        print_status "PASS" "Judgment saved to $JUDGMENT_OUTPUT"
    else
        print_status "FAIL" "Judgment generation failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test document listing
test_document_listing() {
    print_status "INFO" "Testing document listing..."
    
    response=$(curl -s "$BACKEND_URL/documents")
    if echo "$response" | grep -q "documents"; then
        print_status "PASS" "Document listing working"
        echo "Response: $response"
    else
        print_status "FAIL" "Document listing failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to test summarization
test_summarization() {
    print_status "INFO" "Testing document summarization..."
    
    # Get document IDs first
    documents_response=$(curl -s "$BACKEND_URL/documents")
    document_ids=$(echo "$documents_response" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
docs = data.get('documents', [])
ids = [doc['document_id'] for doc in docs[:2]]  # Take first 2 documents
print(json.dumps(ids))
")
    
    if [ "$document_ids" != "[]" ]; then
        summary_data="{\"document_ids\": $document_ids, \"language\": \"auto\"}"
        response=$(curl -s -X POST -H "Content-Type: application/json" -d "$summary_data" "$BACKEND_URL/summarize")
        
        if echo "$response" | grep -q "summary"; then
            print_status "PASS" "Document summarization working"
            echo "Response preview: $(echo "$response" | head -c 200)..."
        else
            print_status "FAIL" "Document summarization failed"
            echo "Response: $response"
            return 1
        fi
    else
        print_status "INFO" "No documents available for summarization test"
    fi
}

# Main test execution
main() {
    echo "Starting E2E smoke tests..."
    echo "Backend URL: $BACKEND_URL"
    echo "Temp directory: $TEMP_DIR"
    echo ""
    
    # Test counter
    TESTS_PASSED=0
    TESTS_FAILED=0
    
    # Run tests
    if check_backend; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
        echo "Backend not available. Please start the backend first."
        exit 1
    fi
    
    if test_sources_status; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
    
    if test_statute_ingestion; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
    
    if test_document_upload; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
    
    if test_question_answering; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
    
    if test_judgment_generation; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
    
    if test_document_listing; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
    
    if test_summarization; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
    
    # Summary
    echo ""
    echo "=========================================="
    echo "E2E Test Summary"
    echo "=========================================="
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        print_status "PASS" "All E2E tests passed!"
        echo ""
        echo "Generated files:"
        echo "- Judgment: $JUDGMENT_OUTPUT"
        echo "- Test PDF: $TEST_PDF_PATH"
        exit 0
    else
        print_status "FAIL" "$TESTS_FAILED test(s) failed"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    print_status "INFO" "Checking dependencies..."
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        print_status "FAIL" "curl is required but not installed"
        exit 1
    fi
    
    # Check python3
    if ! command -v python3 &> /dev/null; then
        print_status "FAIL" "python3 is required but not installed"
        exit 1
    fi
    
    # Check reportlab (for PDF creation)
    if ! python3 -c "import reportlab" &> /dev/null; then
        print_status "INFO" "Installing reportlab for PDF creation..."
        pip3 install reportlab || {
            print_status "FAIL" "Failed to install reportlab"
            exit 1
        }
    fi
    
    print_status "PASS" "All dependencies available"
}

# Run the tests
check_dependencies
main