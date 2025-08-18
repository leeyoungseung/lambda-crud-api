# Lambda CRUD API

A serverless CRUD API implementation using AWS Lambda, API Gateway, and DynamoDB.

## Project Structure

```
lambda-crud-api/
├── shared/                    # Shared modules used by all Lambda functions
│   ├── __init__.py
│   ├── validation.py         # Data validation logic
│   ├── dynamodb_client.py    # DynamoDB operations
│   └── response_handler.py   # Response formatting
├── lambdas/                  # Individual Lambda function handlers
│   ├── __init__.py
│   ├── create_handler.py     # Create operation
│   ├── read_handler.py       # Read operations (single item & all items)
│   ├── update_handler.py     # Update operation
│   └── delete_handler.py     # Delete operation
├── tests/                    # Test modules
│   ├── __init__.py
│   ├── test_validation.py
│   ├── test_dynamodb_client.py
│   ├── test_response_handler.py
│   └── test_lambda_handlers.py
├── infrastructure/           # AWS infrastructure configuration
│   └── terraform/           # Terraform configuration files
│       ├── main.tf          # Main infrastructure resources
│       ├── api-gateway.tf   # API Gateway configuration
│       ├── variables.tf     # Input variables
│       ├── outputs.tf       # Output values
│       └── terraform.tfvars # Variable values
├── scripts/                 # Deployment and utility scripts
│   ├── deploy.sh           # Main deployment script
│   └── test-api.sh         # API testing script
├── docs/                   # Documentation and examples
├── examples/               # Usage examples
├── requirements.txt        # Python dependencies
└── README.md
```

## Features

- **Complete CRUD Operations**: Create, Read (single & all), Update, Delete
- **Independent Lambda Functions**: Each operation runs in its own Lambda function
- **Comprehensive JSON Validation**: Support for all JSON data types with validation
- **DynamoDB Integration**: Serverless database with pay-per-request billing
- **API Gateway Integration**: RESTful API with proper HTTP methods and status codes
- **Standardized Error Handling**: Consistent error responses across all endpoints
- **Infrastructure as Code**: Complete Terraform configuration for AWS resources
- **Automated Deployment**: Scripts for easy deployment and testing
- **Unit and Integration Tests**: Comprehensive test coverage

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/items` | Create a new item |
| GET | `/items` | Get all items (supports query parameters for filtering) |
| GET | `/items/{id}` | Get a specific item by ID |
| PUT | `/items/{id}` | Update an existing item |
| DELETE | `/items/{id}` | Delete an item |

### Query Parameters for GET /items

- `is_active=true/false` - Filter by active status
- `min_price=X` - Filter items with price >= X
- `max_price=X` - Filter items with price <= X
- `tag=tagname` - Filter items containing the specified tag

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.3.0
- Python 3.12
- curl (for API testing)

## Quick Start

### 1. Deploy the Infrastructure

```bash
# Make the deployment script executable
chmod +x scripts/deploy.sh

# Deploy to dev environment (default)
./scripts/deploy.sh

# Deploy to specific environment and region
./scripts/deploy.sh -e prod -r us-east-1

# Deploy without running tests
./scripts/deploy.sh --skip-tests
```

### 2. Test the API

After deployment, use the API URL from Terraform outputs:

```bash
# Make the test script executable
chmod +x scripts/test-api.sh

# Test the API (replace with your actual API Gateway URL)
./scripts/test-api.sh -u https://abc123.execute-api.ap-northeast-1.amazonaws.com/dev
```

### 3. Manual Testing

You can also test individual endpoints manually:

```bash
# Set your API Gateway URL
API_URL="https://your-api-id.execute-api.region.amazonaws.com/environment"

# Create an item
curl -X POST "$API_URL/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Item",
    "description": "A test item",
    "price": 29.99,
    "quantity": 100,
    "is_active": true,
    "tags": ["test", "demo"],
    "metadata": {
      "category": "electronics",
      "weight": 1.5
    }
  }'

# Get all items
curl -X GET "$API_URL/items"

# Get all active items with price between 20 and 50
curl -X GET "$API_URL/items?is_active=true&min_price=20&max_price=50"

# Get specific item
curl -X GET "$API_URL/items/your-item-id"

# Update an item
curl -X PUT "$API_URL/items/your-item-id" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Item",
    "price": 39.99
  }'

# Delete an item
curl -X DELETE "$API_URL/items/your-item-id"
```

## Configuration

### Environment Variables

The Lambda functions use the following environment variables:

- `DYNAMODB_TABLE_NAME`: Name of the DynamoDB table
- `REGION`: AWS region
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)

### Terraform Variables

You can customize the deployment by modifying `infrastructure/terraform/terraform.tfvars`:

```hcl
project_name = "lambda-crud-api"
environment  = "dev"
aws_region   = "ap-northeast-1"

# DynamoDB configuration
table_name = "items"

# Lambda configuration
lambda_runtime     = "python3.12"
lambda_timeout     = 30
lambda_memory_size = 256

# Logging configuration
log_retention_days = 14
```

## Data Model

The API works with items that have the following structure:

```json
{
  "id": "string (UUID, auto-generated)",
  "name": "string (required)",
  "description": "string (optional)",
  "price": 99.99,
  "quantity": 100,
  "is_active": true,
  "tags": ["tag1", "tag2"],
  "metadata": {
    "category": "electronics",
    "weight": 1.5,
    "dimensions": {
      "length": 10,
      "width": 5,
      "height": 3
    }
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Development

### Running Tests Locally

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov moto[dynamodb]

# Run tests
python -m pytest tests/ -v --cov=shared --cov=lambdas
```

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd lambda-crud-api

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## Cleanup

To destroy the infrastructure:

```bash
./scripts/deploy.sh --destroy
```

## Dependencies

- **boto3**: AWS SDK for Python
- **pytest**: Testing framework
- **moto**: AWS service mocking for tests
- **terraform**: Infrastructure as Code
- **aws-cli**: AWS command line interface