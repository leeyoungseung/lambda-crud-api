#!/bin/bash

# API Testing Script for Lambda CRUD API
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
API_URL=""
ENVIRONMENT="dev"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test Lambda CRUD API endpoints.

OPTIONS:
    -u, --url URL           API Gateway base URL (required)
    -e, --environment ENV   Environment [default: dev]
    -h, --help             Show this help message

EXAMPLES:
    $0 -u https://abc123.execute-api.ap-northeast-1.amazonaws.com/dev
    $0 --url https://abc123.execute-api.ap-northeast-1.amazonaws.com/dev --environment dev

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$API_URL" ]]; then
    print_error "API URL is required. Use -u or --url option."
    show_usage
    exit 1
fi

# Remove trailing slash from URL
API_URL="${API_URL%/}"

print_status "Testing API at: $API_URL"

# Test data
ITEM_ID="test-item-$(date +%s)"
ITEM_DATA='{
    "name": "Test Item",
    "description": "This is a test item created by the API test script",
    "price": 29.99,
    "quantity": 100,
    "is_active": true,
    "tags": ["test", "api", "demo"],
    "metadata": {
        "category": "electronics",
        "weight": 1.5,
        "dimensions": {
            "length": 10,
            "width": 5,
            "height": 3
        }
    }
}'

UPDATE_DATA='{
    "name": "Updated Test Item",
    "description": "This item has been updated",
    "price": 39.99,
    "quantity": 75,
    "is_active": true,
    "tags": ["test", "api", "demo", "updated"],
    "metadata": {
        "category": "electronics",
        "weight": 1.8,
        "dimensions": {
            "length": 12,
            "width": 6,
            "height": 4
        }
    }
}'

# Function to make HTTP request and check response
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    print_status "Testing: $description"
    echo "  Method: $method"
    echo "  Endpoint: $endpoint"
    
    if [[ -n "$data" ]]; then
        echo "  Data: $data"
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            "$API_URL$endpoint")
    fi
    
    # Split response body and status code
    response_body=$(echo "$response" | head -n -1)
    status_code=$(echo "$response" | tail -n 1)
    
    echo "  Status Code: $status_code"
    echo "  Response: $response_body"
    
    if [[ "$status_code" == "$expected_status" ]]; then
        print_success "✓ Test passed"
    else
        print_error "✗ Test failed - Expected status $expected_status, got $status_code"
        return 1
    fi
    
    echo ""
    return 0
}

# Function to run all tests
run_tests() {
    local failed_tests=0
    
    print_status "Starting API tests..."
    echo ""
    
    # Test 1: Create item
    if ! make_request "POST" "/items" "$ITEM_DATA" "201" "Create new item"; then
        ((failed_tests++))
    fi
    
    # Test 2: Get all items
    if ! make_request "GET" "/items" "" "200" "Get all items"; then
        ((failed_tests++))
    fi
    
    # Test 3: Get specific item
    if ! make_request "GET" "/items/$ITEM_ID" "" "200" "Get specific item"; then
        ((failed_tests++))
    fi
    
    # Test 4: Update item
    if ! make_request "PUT" "/items/$ITEM_ID" "$UPDATE_DATA" "200" "Update item"; then
        ((failed_tests++))
    fi
    
    # Test 5: Get updated item
    if ! make_request "GET" "/items/$ITEM_ID" "" "200" "Get updated item"; then
        ((failed_tests++))
    fi
    
    # Test 6: Delete item
    if ! make_request "DELETE" "/items/$ITEM_ID" "" "200" "Delete item"; then
        ((failed_tests++))
    fi
    
    # Test 7: Try to get deleted item (should return 404)
    if ! make_request "GET" "/items/$ITEM_ID" "" "404" "Get deleted item (should fail)"; then
        ((failed_tests++))
    fi
    
    # Test 8: Test error cases
    print_status "Testing error cases..."
    
    # Invalid JSON
    if ! make_request "POST" "/items" '{"invalid": json}' "400" "Create item with invalid JSON"; then
        ((failed_tests++))
    fi
    
    # Missing required fields
    if ! make_request "POST" "/items" '{"description": "Missing required fields"}' "400" "Create item with missing required fields"; then
        ((failed_tests++))
    fi
    
    # Invalid item ID
    if ! make_request "GET" "/items/invalid-id-format" "" "400" "Get item with invalid ID format"; then
        ((failed_tests++))
    fi
    
    # Non-existent item
    if ! make_request "GET" "/items/non-existent-item-12345" "" "404" "Get non-existent item"; then
        ((failed_tests++))
    fi
    
    # Test query parameters for GET /items
    print_status "Testing query parameters..."
    
    # Create a test item for filtering
    TEST_FILTER_ITEM='{
        "name": "Filter Test Item",
        "description": "Item for testing filters",
        "price": 15.99,
        "quantity": 50,
        "is_active": true,
        "tags": ["filter", "test"]
    }'
    
    if ! make_request "POST" "/items" "$TEST_FILTER_ITEM" "201" "Create item for filter testing"; then
        ((failed_tests++))
    fi
    
    # Test filtering by is_active
    if ! make_request "GET" "/items?is_active=true" "" "200" "Filter items by is_active=true"; then
        ((failed_tests++))
    fi
    
    # Test filtering by price range
    if ! make_request "GET" "/items?min_price=10&max_price=20" "" "200" "Filter items by price range"; then
        ((failed_tests++))
    fi
    
    # Test filtering by tag
    if ! make_request "GET" "/items?tag=filter" "" "200" "Filter items by tag"; then
        ((failed_tests++))
    fi
    
    # Summary
    echo ""
    if [[ $failed_tests -eq 0 ]]; then
        print_success "All tests passed! 🎉"
    else
        print_error "$failed_tests test(s) failed"
        exit 1
    fi
}

# Check if curl is available
if ! command -v curl &> /dev/null; then
    print_error "curl is not installed. Please install it first."
    exit 1
fi

# Run the tests
run_tests