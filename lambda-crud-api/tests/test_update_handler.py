"""
Unit tests for Update Lambda handler.
Tests item update functionality and error handling.
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

from update_handler import (
    lambda_handler,
    prepare_update_data,
    validate_update_data,
    check_item_exists,
    merge_update_data,
    validate_partial_update
)
from dynamodb_client import DynamoDBError


@mock_dynamodb
class TestUpdateHandler:
    """Test Update Lambda handler."""
    
    def setup_method(self):
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
        
        # Sample existing item
        self.existing_item = {
            "id": "test-item-123",
            "name": "Original Item",
            "description": "Original description",
            "price": 99.99,
            "quantity": 10,
            "is_active": True,
            "tags": ["electronics", "gadget"],
            "metadata": {
                "category": "electronics",
                "weight": 1.5
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        # Add existing item to table
        self.table.put_item(Item=self.existing_item)
        
        # Mock context
        self.context = MagicMock()
        self.context.aws_request_id = "test-request-id"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_update_item_success(self):
        """Test successful item update."""
        update_data = {
            "name": "Updated Item",
            "price": 149.99,
            "description": "Updated description"
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["name"] == "Updated Item"
        assert body["data"]["price"] == 149.99
        assert body["data"]["description"] == "Updated description"
        # Original fields should be preserved
        assert body["data"]["quantity"] == 10
        assert body["data"]["is_active"] is True
        # Timestamps should be updated
        assert body["data"]["created_at"] == "2024-01-01T00:00:00Z"
        assert body["data"]["updated_at"] != "2024-01-01T00:00:00Z"
        assert "updated successfully" in body["message"]
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_update_item_partial(self):
        """Test partial item update."""
        update_data = {
            "name": "Partially Updated Item"
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["data"]["name"] == "Partially Updated Item"
        # All other fields should remain unchanged
        assert body["data"]["price"] == 99.99
        assert body["data"]["quantity"] == 10
        assert body["data"]["description"] == "Original description"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_update_item_not_found(self):
        """Test updating non-existent item."""
        update_data = {
            "name": "Updated Item"
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "non-existent-item"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 404
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"
        assert "not found" in body["error"]["message"]
    
    def test_update_item_missing_id(self):
        """Test update with missing ID parameter."""
        update_data = {
            "name": "Updated Item"
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "required" in body["error"]["message"]
    
    def test_update_item_invalid_id_format(self):
        """Test update with invalid ID format."""
        update_data = {
            "name": "Updated Item"
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "invalid@id!"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "Invalid item ID format" in body["error"]["message"]
    
    def test_update_item_missing_body(self):
        """Test update with missing request body."""
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "required" in body["error"]["message"]
    
    def test_update_item_invalid_json(self):
        """Test update with invalid JSON."""
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": '{"name": "Updated Item"'  # Missing closing brace
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "Invalid JSON format" in body["error"]["message"]
    
    def test_update_item_validation_errors(self):
        """Test update with validation errors."""
        update_data = {
            "name": "",  # Too short
            "price": -10.00,  # Negative price
            "quantity": "not a number",  # Wrong type
            "is_active": "not a boolean"  # Wrong type
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert len(body["error"]["details"]) > 0
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_update_item_id_protection(self):
        """Test that ID cannot be changed during update."""
        update_data = {
            "id": "different-id",
            "name": "Updated Item"
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        # ID should remain the same
        assert body["data"]["id"] == "test-item-123"
        assert body["data"]["name"] == "Updated Item"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_update_item_created_at_protection(self):
        """Test that created_at timestamp cannot be changed."""
        update_data = {
            "created_at": "2024-12-31T23:59:59Z",
            "name": "Updated Item"
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        # created_at should remain the same
        assert body["data"]["created_at"] == "2024-01-01T00:00:00Z"
        assert body["data"]["name"] == "Updated Item"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_update_item_all_json_types(self):
        """Test update with all JSON data types."""
        update_data = {
            "name": "Comprehensive Update",  # string
            "price": 199.99,  # float
            "quantity": 25,  # integer
            "is_active": False,  # boolean
            "tags": ["updated", "comprehensive"],  # array
            "metadata": {  # object
                "category": "updated",
                "weight": 2.0,
                "features": ["feature1", "feature2"]
            },
            "description": None  # null (optional field)
        }
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps(update_data)
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["data"]["name"] == "Comprehensive Update"
        assert body["data"]["price"] == 199.99
        assert body["data"]["quantity"] == 25
        assert body["data"]["is_active"] is False
        assert body["data"]["tags"] == ["updated", "comprehensive"]
        assert body["data"]["metadata"]["category"] == "updated"
        assert body["data"]["description"] is None
    
    def test_update_item_cors_preflight(self):
        """Test CORS preflight OPTIONS request."""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["body"] == ""
    
    @patch('update_handler.update_item')
    def test_update_item_dynamodb_error(self, mock_update_item):
        """Test handling of DynamoDB errors."""
        mock_update_item.side_effect = DynamoDBError("Database connection failed", "CONNECTION_ERROR")
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps({"name": "Updated Item"})
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "Database connection failed" in body["error"]["message"]
    
    @patch('update_handler.validate_item_data')
    def test_update_item_unexpected_error(self, mock_validate):
        """Test handling of unexpected errors."""
        mock_validate.side_effect = Exception("Unexpected error")
        
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item-123"},
            "body": json.dumps({"name": "Updated Item"})
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert "Unexpected error" in body["error"]["message"]


class TestPrepareUpdateData:
    """Test prepare_update_data function."""
    
    def test_prepare_update_data_basic(self):
        """Test basic update data preparation."""
        update_data = {
            "name": "Updated Item",
            "price": 149.99
        }
        
        result = prepare_update_data(update_data, "test-item-123")
        
        assert result["name"] == "Updated Item"
        assert result["price"] == 149.99
        assert "updated_at" in result
        assert "id" not in result
    
    def test_prepare_update_data_removes_id(self):
        """Test that ID is removed from update data."""
        update_data = {
            "id": "different-id",
            "name": "Updated Item"
        }
        
        result = prepare_update_data(update_data, "test-item-123")
        
        assert "id" not in result
        assert result["name"] == "Updated Item"
    
    def test_prepare_update_data_removes_created_at(self):
        """Test that created_at is removed from update data."""
        update_data = {
            "created_at": "2024-12-31T23:59:59Z",
            "name": "Updated Item"
        }
        
        result = prepare_update_data(update_data, "test-item-123")
        
        assert "created_at" not in result
        assert result["name"] == "Updated Item"
    
    def test_prepare_update_data_adds_updated_at(self):
        """Test that updated_at timestamp is added."""
        update_data = {
            "name": "Updated Item"
        }
        
        result = prepare_update_data(update_data, "test-item-123")
        
        assert "updated_at" in result
        assert result["updated_at"].endswith("Z")
    
    def test_prepare_update_data_preserves_other_fields(self):
        """Test that other fields are preserved."""
        update_data = {
            "name": "Updated Item",
            "price": 149.99,
            "tags": ["updated"],
            "metadata": {"category": "updated"}
        }
        
        result = prepare_update_data(update_data, "test-item-123")
        
        assert result["name"] == "Updated Item"
        assert result["price"] == 149.99
        assert result["tags"] == ["updated"]
        assert result["metadata"] == {"category": "updated"}


class TestValidateUpdateData:
    """Test validate_update_data function."""
    
    def test_validate_update_data_valid(self):
        """Test validation with valid update data."""
        update_data = {
            "name": "Updated Item",
            "price": 149.99
        }
        
        result = validate_update_data(update_data, "test-item-123")
        assert result is None
    
    def test_validate_update_data_empty(self):
        """Test validation with empty update data."""
        result = validate_update_data({}, "test-item-123")
        
        assert result is not None
        assert result["statusCode"] == 400
        
        body = json.loads(result["body"])
        assert "cannot be empty" in body["error"]["message"]
    
    def test_validate_update_data_only_system_fields(self):
        """Test validation with only system fields."""
        update_data = {
            "id": "different-id",
            "created_at": "2024-12-31T23:59:59Z"
        }
        
        result = validate_update_data(update_data, "test-item-123")
        
        assert result is not None
        body = json.loads(result["body"])
        assert "No valid fields to update" in body["error"]["message"]
    
    def test_validate_update_data_invalid_fields(self):
        """Test validation with invalid field values."""
        update_data = {
            "name": "",  # Too short
            "price": -10.00  # Negative
        }
        
        result = validate_update_data(update_data, "test-item-123")
        
        assert result is not None
        assert result["statusCode"] == 400
        
        body = json.loads(result["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"


class TestCheckItemExists:
    """Test check_item_exists function."""
    
    @patch('update_handler.get_item')
    def test_check_item_exists_true(self, mock_get_item):
        """Test checking existing item."""
        mock_get_item.return_value = {"id": "test-item", "name": "Test Item"}
        
        result = check_item_exists("test-item")
        assert result is True
    
    @patch('update_handler.get_item')
    def test_check_item_exists_false(self, mock_get_item):
        """Test checking non-existent item."""
        mock_get_item.return_value = None
        
        result = check_item_exists("non-existent-item")
        assert result is False
    
    @patch('update_handler.get_item')
    def test_check_item_exists_error(self, mock_get_item):
        """Test checking item with DynamoDB error."""
        mock_get_item.side_effect = DynamoDBError("Connection failed", "CONNECTION_ERROR")
        
        result = check_item_exists("test-item")
        assert result is False


class TestMergeUpdateData:
    """Test merge_update_data function."""
    
    def test_merge_update_data_basic(self):
        """Test basic data merging."""
        existing_item = {
            "id": "test-item",
            "name": "Original Item",
            "price": 99.99,
            "quantity": 10,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        update_data = {
            "name": "Updated Item",
            "price": 149.99
        }
        
        result = merge_update_data(existing_item, update_data)
        
        assert result["id"] == "test-item"  # Preserved
        assert result["name"] == "Updated Item"  # Updated
        assert result["price"] == 149.99  # Updated
        assert result["quantity"] == 10  # Preserved
        assert result["created_at"] == "2024-01-01T00:00:00Z"  # Preserved
        assert result["updated_at"] != "2024-01-01T00:00:00Z"  # Updated
    
    def test_merge_update_data_protects_system_fields(self):
        """Test that system fields are protected during merge."""
        existing_item = {
            "id": "test-item",
            "name": "Original Item",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        update_data = {
            "id": "different-id",
            "name": "Updated Item",
            "created_at": "2024-12-31T23:59:59Z"
        }
        
        result = merge_update_data(existing_item, update_data)
        
        assert result["id"] == "test-item"  # Protected
        assert result["name"] == "Updated Item"  # Updated
        assert result["created_at"] == "2024-01-01T00:00:00Z"  # Protected


class TestValidatePartialUpdate:
    """Test validate_partial_update function."""
    
    def test_validate_partial_update_valid(self):
        """Test validation with valid partial update."""
        update_data = {
            "name": "Updated Item"
        }
        
        result = validate_partial_update(update_data)
        assert result is None
    
    def test_validate_partial_update_empty(self):
        """Test validation with empty update data."""
        result = validate_partial_update({})
        
        assert result is not None
        body = json.loads(result["body"])
        assert "Update data is required" in body["error"]["message"]
    
    def test_validate_partial_update_no_updatable_fields(self):
        """Test validation with no updatable fields."""
        update_data = {
            "id": "different-id",
            "created_at": "2024-12-31T23:59:59Z"
        }
        
        result = validate_partial_update(update_data)
        
        assert result is not None
        body = json.loads(result["body"])
        assert "No updatable fields provided" in body["error"]["message"]
    
    def test_validate_partial_update_null_required_field(self):
        """Test validation with null required field."""
        update_data = {
            "name": None  # Required field set to null
        }
        
        result = validate_partial_update(update_data)
        
        assert result is not None
        body = json.loads(result["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "cannot be set to null" in body["error"]["details"][0]["message"]


if __name__ == "__main__":
    pytest.main([__file__])