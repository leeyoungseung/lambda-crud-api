# Lambda CRUD API

A serverless CRUD API implementation using AWS Lambda, API Gateway, and DynamoDB.

## Project Structure

```
lambda-crud-api/
├── shared/                 # Shared modules used by all Lambda functions
│   ├── __init__.py
│   ├── validation.py      # Data validation logic
│   ├── dynamodb_client.py # DynamoDB operations
│   └── response_handler.py # Response formatting
├── lambdas/               # Individual Lambda function handlers
│   ├── __init__.py
│   ├── create_handler.py  # Create operation
│   ├── read_handler.py    # Read operations
│   ├── update_handler.py  # Update operation
│   └── delete_handler.py  # Delete operation
├── tests/                 # Test modules
│   ├── __init__.py
│   ├── test_validation.py
│   ├── test_dynamodb_client.py
│   ├── test_response_handler.py
│   └── test_lambda_handlers.py
├── infrastructure/        # AWS infrastructure configuration
├── requirements.txt       # Python dependencies
└── README.md
```

## Features

- Independent Lambda functions for each CRUD operation
- Comprehensive JSON data validation
- Support for all JSON data types
- DynamoDB integration
- Standardized error handling
- Unit and integration tests

## Dependencies

- boto3: AWS SDK for Python
- pytest: Testing framework
- moto: AWS service mocking for tests