"""
Unit tests for Create Lambda handler.
Tests item creation functionality and error handling.
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb
import boto3

# Add the lambdas module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambdas'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from create_handler import lambda_handler, validate_create_data, prepare_item_for_creation
from dynamodb_client import DynamoDBError


@mock_dynamodb
class TestCreateHandler:
    """Test Create Lambda handler."""
    
    def setup_method(self, method):
        """Set up test environment before each test."""
        # Create mock DynamoDB table
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'crud-api-items'
        
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Sample valid item data
        self.valid_item_data = {
            "name": "Test Item",
            "description": "A test item description",
            "price": 99.99,
            "quantity": 10,
            "is_active": True,
            "tags": ["electronics", "gadget"],
            "metadata": {
                "category": "electronics",
                "weight": 1.5,
                "dimensions": {"length": 10, "width": 5, "height": 3}
            }
        }
        
        # Mock context
        self.context = MagicMock()
        self.context.aws_request_id = "test-request-id"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_create_item_success(self):
        """Test successful item creation."""
        event = {
            "httpMethod": "POST",
            "body": json.dumps(self.valid_item_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 201
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["name"] == "Test Item"
        assert body["data"]["price"] == 99.99
        assert "id" in body["data"]
        assert "created_at" in body["data"]
        assert "updated_at" in body["data"]
        assert "created successfully" in body["message"]
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_create_item_with_custom_id(self):
        """Test item creation with custom ID."""
        item_data = self.valid_item_data.copy()
        item_data["id"] = "custom-item-123"
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(item_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 201
        
        body = json.loads(response["body"])
        assert body["data"]["id"] == "custom-item-123"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_create_item_minimal_data(self):
        """Test item creation with minimal required data."""
        minimal_data = {
            "name": "Minimal Item",
            "price": 1.00,
            "quantity": 1,
            "is_active": True
        }
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(minimal_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 201
        
        body = json.loads(response["body"])
        assert body["data"]["name"] == "Minimal Item"
        assert "id" in body["data"]
    
    def test_create_item_missing_body(self):
        """Test creation with missing request body."""
        event = {
            "httpMethod": "POST"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "required" in body["error"]["message"]
    
    def test_create_item_invalid_json(self):
        """Test creation with invalid JSON."""
        event = {
            "httpMethod": "POST",
            "body": '{"name": "Test", "price": 99.99'  # Missing closing brace
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "Invalid JSON format" in body["error"]["message"]
    
    def test_create_item_validation_errors(self):
        """Test creation with validation errors."""
        invalid_data = {
            "name": "",  # Too short
            "price": -10.00,  # Negative price
            "quantity": "not a number",  # Wrong type
            "is_active": "not a boolean",  # Wrong type
            "tags": "not an array"  # Wrong type
        }
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(invalid_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert len(body["error"]["details"]) > 0
    
    def test_create_item_missing_required_fields(self):
        """Test creation with missing required fields."""
        incomplete_data = {
            "name": "Test Item"
            # Missing price, quantity, is_active
        }
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(incomplete_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        
        # Check that all missing required fields are reported
        error_fields = [error["field"] for error in body["error"]["details"]]
        assert "price" in error_fields
        assert "quantity" in error_fields
        assert "is_active" in error_fields
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_create_item_duplicate_id(self):
        """Test creation with duplicate ID."""
        # Create first item
        item_data = self.valid_item_data.copy()
        item_data["id"] = "duplicate-test-123"
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(item_data)
        }
        
        # First creation should succeed
        response1 = lambda_handler(event, self.context)
        assert response1["statusCode"] == 201
        
        # Second creation with same ID should fail
        response2 = lambda_handler(event, self.context)
        assert response2["statusCode"] == 400
        
        body = json.loads(response2["body"])
        assert "already exists" in body["error"]["message"]
    
    def test_create_item_cors_preflight(self):
        """Test CORS preflight OPTIONS request."""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["body"] == ""
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_create_item_all_json_types(self):
        """Test creation with all JSON data types."""
        comprehensive_data = {
            "name": "Comprehensive Test Item",  # string
            "price": 123.45,  # float
            "quantity": 42,  # integer
            "is_active": True,  # boolean
            "tags": ["electronics", "gadget", "test"],  # array
            "metadata": {  # object
                "category": "test",
                "weight": 2.5,
                "dimensions": {
                    "length": 15,
                    "width": 10,
                    "height": 5
                },
                "features": ["feature1", "feature2"]
            },
            "description": None  # null (optional field)
        }
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(comprehensive_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 201
        
        body = json.loads(response["body"])
        assert body["data"]["name"] == "Comprehensive Test Item"
        assert body["data"]["price"] == 123.45
        assert body["data"]["quantity"] == 42
        assert body["data"]["is_active"] is True
        assert body["data"]["tags"] == ["electronics", "gadget", "test"]
        assert body["data"]["metadata"]["category"] == "test"
        assert body["data"]["description"] is None
    
    @patch('create_handler.create_item')
    def test_create_item_dynamodb_error(self, mock_create_item):
        """Test handling of DynamoDB errors."""
        mock_create_item.side_effect = DynamoDBError("Database connection failed", "CONNECTION_ERROR")
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(self.valid_item_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "Database connection failed" in body["error"]["message"]
    
    @patch('create_handler.validate_item_data')
    def test_create_item_unexpected_error(self, mock_validate):
        """Test handling of unexpected errors."""
        mock_validate.side_effect = Exception("Unexpected error")
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps(self.valid_item_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert "Unexpected error" in body["error"]["message"]


class TestValidateCreateData:
    """Test validate_create_data function."""
    
    def test_validate_create_data_valid(self):
        """Test validation with valid data."""
        valid_data = {
            "name": "Test Item",
            "price": 99.99,
            "quantity": 10,
            "is_active": True
        }
        
        result = validate_create_data(valid_data)
        assert result is None  # No validation errors
    
    def test_validate_create_data_invalid(self):
        """Test validation with invalid data."""
        invalid_data = {
            "name": "",  # Too short
            "price": -10.00,  # Negative
            "quantity": "not a number",  # Wrong type
            "is_active": "not a boolean"  # Wrong type
        }
        
        result = validate_create_data(invalid_data)
        
        assert result is not None
        assert result["statusCode"] == 400
        
        body = json.loads(result["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"


class TestPrepareItemForCreation:
    """Test prepare_item_for_creation function."""
    
    def test_prepare_item_without_id(self):
        """Test preparing item without ID."""
        data = {
            "name": "Test Item",
            "price": 99.99,
            "quantity": 10,
            "is_active": True
        }
        
        result = prepare_item_for_creation(data)
        
        assert "id" in result
        assert len(result["id"]) > 0
        assert "created_at" in result
        assert "updated_at" in result
        assert result["created_at"] == result["updated_at"]
    
    def test_prepare_item_with_id(self):
        """Test preparing item with existing ID."""
        data = {
            "id": "existing-id-123",
            "name": "Test Item",
            "price": 99.99,
            "quantity": 10,
            "is_active": True
        }
        
        result = prepare_item_for_creation(data)
        
        assert result["id"] == "existing-id-123"
        assert "created_at" in result
        assert "updated_at" in result
    
    def test_prepare_item_with_empty_id(self):
        """Test preparing item with empty ID."""
        data = {
            "id": "",
            "name": "Test Item",
            "price": 99.99,
            "quantity": 10,
            "is_active": True
        }
        
        result = prepare_item_for_creation(data)
        
        assert result["id"] != ""
        assert len(result["id"]) > 0
    
    def test_prepare_item_preserves_original_data(self):
        """Test that preparation preserves original data."""
        data = {
            "name": "Test Item",
            "price": 99.99,
            "quantity": 10,
            "is_active": True,
            "tags": ["test"],
            "metadata": {"category": "test"}
        }
        
        result = prepare_item_for_creation(data)
        
        # Original data should be preserved
        assert result["name"] == data["name"]
        assert result["price"] == data["price"]
        assert result["quantity"] == data["quantity"]
        assert result["is_active"] == data["is_active"]
        assert result["tags"] == data["tags"]
        assert result["metadata"] == data["metadata"]
        
        # Original data should not be modified
        assert "id" not in data
        assert "created_at" not in data
        assert "updated_at" not in data


class TestResponseHeaders:
    """Test response headers."""
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    @mock_dynamodb
    def test_response_has_cors_headers(self):
        """Test that responses include CORS headers."""
        # Set up DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='crud-api-items',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "name": "Test Item",
                "price": 99.99,
                "quantity": 10,
                "is_active": True
            })
        }
        
        response = lambda_handler(event, MagicMock())
        
        headers = response["headers"]
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "GET,POST,PUT,DELETE,OPTIONS" in headers["Access-Control-Allow-Methods"]
        assert headers["Content-Type"] == "application/json"


if __name__ == "__main__":
    pytest.main([__file__])