#!/bin/bash

# Quick test script for tenant screening workflow
# Usage: ./test_tenant_workflow.sh [backend_url]

BACKEND_URL="${1:-http://localhost:8000}"
echo "Testing tenant screening workflow against: $BACKEND_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health check
echo "1. Testing backend health..."
HEALTH=$(curl -s "$BACKEND_URL/health")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Backend is running"
else
    echo -e "${RED}✗${NC} Backend is not responding"
    exit 1
fi
echo ""

# Test 2: Calendar availability
echo "2. Testing calendar availability..."
AVAILABILITY=$(curl -s "$BACKEND_URL/api/calendar/availability?userId=test-user&days=14")
if echo "$AVAILABILITY" | grep -q "success"; then
    echo -e "${GREEN}✓${NC} Calendar availability endpoint works"
else
    echo -e "${YELLOW}⚠${NC} Calendar availability endpoint returned: $AVAILABILITY"
fi
echo ""

# Test 3: Document processing
echo "3. Testing document processing endpoint..."
PROCESS_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/tenant-applications/process-documents" \
  -H "Content-Type: application/json" \
  -d '{
    "applicationId": "test-app-123",
    "driversLicenseUrl": "https://example.com/license.jpg",
    "payStubUrls": ["https://example.com/paystub.jpg"],
    "creditScoreUrl": "https://example.com/credit.jpg"
  }')
if echo "$PROCESS_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓${NC} Document processing endpoint works"
else
    echo -e "${YELLOW}⚠${NC} Document processing response: $PROCESS_RESPONSE"
fi
echo ""

# Test 4: Screening score calculation
echo "4. Testing screening score calculation..."
SCORE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/tenant-applications/test-app/calculate-score" \
  -H "Content-Type: application/json" \
  -d '{
    "creditScore": 720,
    "monthlyIncome": 6000,
    "monthlyRent": 2000,
    "licenseExpiration": "2025-12-31",
    "licenseName": "John Doe",
    "applicantName": "John Doe"
  }')
if echo "$SCORE_RESPONSE" | grep -q "success"; then
    SCORE=$(echo "$SCORE_RESPONSE" | grep -o '"score":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓${NC} Screening score calculated: $SCORE"
else
    echo -e "${YELLOW}⚠${NC} Score calculation response: $SCORE_RESPONSE"
fi
echo ""

# Test 5: Agentmail inbox check
echo "5. Testing Agentmail inbox check..."
INBOX_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/agentmail/check-inbox")
if echo "$INBOX_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓${NC} Inbox check endpoint works"
else
    echo -e "${YELLOW}⚠${NC} Inbox check response: $INBOX_RESPONSE"
    echo "   (This is normal if Agentmail credentials are not configured)"
fi
echo ""

# Summary
echo "=== Test Summary ==="
echo "Backend URL: $BACKEND_URL"
echo ""
echo "Next steps:"
echo "1. Test frontend: http://localhost:3000/applications"
echo "2. Create a test application via the UI"
echo "3. Process documents and verify extraction"
echo "4. Test approval and scheduling workflow"
echo ""
echo "For detailed testing, see: TESTING_GUIDE.md"

