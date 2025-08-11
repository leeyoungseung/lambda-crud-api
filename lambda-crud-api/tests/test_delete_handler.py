"""
Unit tests for Delete Lambda handler.
Tests item deletion functionality and error handling.
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

from delete_handler import (
    lambda_handler,
    validate_delete_request,
    check_item_exists_for_deletion,
    perform_item_deletion,
    create_deletion_response,
    handle_soft_delete,
    validate_deletion_permissions,
    log_deletion_audit
)
from dynamodb_client import DynamoDBError


@mock_dynamodb
class TestDeleteHandler:
    """Test Delete Lambda handler."""
    
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
            "name": "Test Item",
            "description": "A test item for deletion",
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
    def test_delete_item_success(self):
        """Test successful item deletion."""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "test-item-123"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["id"] == "test-item-123"
        assert body["data"]["deleted"] is True
        assert "deleted_item" in body["data"]
        assert body["data"]["deleted_item"]["name"] == "Test Item"
        assert "deleted successfully" in body["message"]
        
        # Verify item is actually deleted from database
        remaining_item = self.table.get_item(Key={'id': 'test-item-123'})
        assert 'Item' not in remaining_item
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_delete_item_not_found(self):
        """Test deleting non-existent item."""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "non-existent-item"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 404
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"
        assert "non-existent-item" in body["error"]["message"]
        assert "not found" in body["error"]["message"]
    
    def test_delete_item_missing_id(self):
        """Test deletion with missing ID parameter."""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "required" in body["error"]["message"]
    
    def test_delete_item_invalid_id_format(self):
        """Test deletion with invalid ID format."""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "invalid@id!"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "Invalid item ID format" in body["error"]["message"]
    
    def test_delete_item_empty_id(self):
        """Test deletion with empty ID."""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": ""}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "cannot be empty" in body["error"]["details"][0]["message"]
    
    def test_delete_item_whitespace_id(self):
        """Test deletion with whitespace-only ID."""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "   "}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "cannot be empty" in body["error"]["details"][0]["message"]
    
    def test_delete_item_cors_preflight(self):
        """Test CORS preflight OPTIONS request."""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["body"] == ""
    
    @patch('delete_handler.get_item')
    def test_delete_item_get_error(self, mock_get_item):
        """Test handling of DynamoDB error during existence check."""
        mock_get_item.side_effect = DynamoDBError("Database connection failed", "CONNECTION_ERROR")
        
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "test-item-123"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "Database connection failed" in body["error"]["message"]
    
    @patch('delete_handler.delete_item')
    def test_delete_item_delete_error(self, mock_delete_item):
        """Test handling of DynamoDB error during deletion."""
        mock_delete_item.side_effect = DynamoDBError("Delete operation failed", "DELETE_ERROR")
        
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "test-item-123"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert "Delete operation failed" in body["error"]["message"]
    
    @patch('delete_handler.validate_item_id')
    def test_delete_item_unexpected_error(self, mock_validate):
        """Test handling of unexpected errors."""
        mock_validate.side_effect = Exception("Unexpected error")
        
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "test-item-123"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert "Unexpected error" in body["error"]["message"]
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_delete_item_returns_deleted_item_data(self):
        """Test that deletion response includes deleted item data."""
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "test-item-123"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        deleted_item = body["data"]["deleted_item"]
        
        # Verify all original item data is included
        assert deleted_item["name"] == "Test Item"
        assert deleted_item["price"] == 99.99
        assert deleted_item["quantity"] == 10
        assert deleted_item["is_active"] is True
        assert deleted_item["tags"] == ["electronics", "gadget"]
        assert deleted_item["metadata"]["category"] == "electronics"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    @patch('delete_handler.delete_item')
    def test_delete_item_deletion_fails_after_existence_check(self, mock_delete_item):
        """Test handling when deletion fails after existence check passes."""
        mock_delete_item.return_value = False  # Deletion failed
        
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "test-item-123"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 404
        
        body = json.loads(response["body"])
        assert body["error"]["code"] == "NOT_FOUND"


class TestValidateDeleteRequest:
    """Test validate_delete_request function."""
    
    def test_validate_delete_request_valid(self):
        """Test validation with valid item ID."""
        result = validate_delete_request("valid-item-123")
        assert result is None
    
    def test_validate_delete_request_invalid_format(self):
        """Test validation with invalid ID format."""
        result = validate_delete_request("invalid@id!")
        
        assert result is not None
        assert result["statusCode"] == 400
        
        body = json.loads(result["body"])
        assert "Invalid item ID format" in body["error"]["message"]
    
    def test_validate_delete_request_empty_id(self):
        """Test validation with empty ID."""
        result = validate_delete_request("")
        
        assert result is not None
        body = json.loads(result["body"])
        assert "cannot be empty" in body["error"]["details"][0]["message"]


class TestCheckItemExistsForDeletion:
    """Test check_item_exists_for_deletion function."""
    
    @patch('delete_handler.get_item')
    def test_check_item_exists_true(self, mock_get_item):
        """Test checking existing item."""
        mock_item = {"id": "test-item", "name": "Test Item"}
        mock_get_item.return_value = mock_item
        
        exists, item_data, error_response = check_item_exists_for_deletion("test-item")
        
        assert exists is True
        assert item_data == mock_item
        assert error_response is None
    
    @patch('delete_handler.get_item')
    def test_check_item_exists_false(self, mock_get_item):
        """Test checking non-existent item."""
        mock_get_item.return_value = None
        
        exists, item_data, error_response = check_item_exists_for_deletion("non-existent")
        
        assert exists is False
        assert item_data is None
        assert error_response is not None
        assert error_response["statusCode"] == 404
    
    @patch('delete_handler.get_item')
    def test_check_item_exists_dynamodb_error(self, mock_get_item):
        """Test checking item with DynamoDB error."""
        mock_get_item.side_effect = DynamoDBError("Connection failed", "CONNECTION_ERROR")
        
        exists, item_data, error_response = check_item_exists_for_deletion("test-item")
        
        assert exists is False
        assert item_data is None
        assert error_response is not None
        assert error_response["statusCode"] == 500
    
    @patch('delete_handler.get_item')
    def test_check_item_exists_unexpected_error(self, mock_get_item):
        """Test checking item with unexpected error."""
        mock_get_item.side_effect = Exception("Unexpected error")
        
        exists, item_data, error_response = check_item_exists_for_deletion("test-item")
        
        assert exists is False
        assert item_data is None
        assert error_response is not None
        assert error_response["statusCode"] == 500


class TestPerformItemDeletion:
    """Test perform_item_deletion function."""
    
    @patch('delete_handler.delete_item')
    def test_perform_item_deletion_success(self, mock_delete_item):
        """Test successful item deletion."""
        mock_delete_item.return_value = True
        
        success, error_response = perform_item_deletion("test-item")
        
        assert success is True
        assert error_response is None
    
    @patch('delete_handler.delete_item')
    def test_perform_item_deletion_failure(self, mock_delete_item):
        """Test failed item deletion."""
        mock_delete_item.return_value = False
        
        success, error_response = perform_item_deletion("test-item")
        
        assert success is False
        assert error_response is None  # No error, just unsuccessful
    
    @patch('delete_handler.delete_item')
    def test_perform_item_deletion_dynamodb_error(self, mock_delete_item):
        """Test item deletion with DynamoDB error."""
        mock_delete_item.side_effect = DynamoDBError("Delete failed", "DELETE_ERROR")
        
        success, error_response = perform_item_deletion("test-item")
        
        assert success is False
        assert error_response is not None
        assert error_response["statusCode"] == 500
    
    @patch('delete_handler.delete_item')
    def test_perform_item_deletion_unexpected_error(self, mock_delete_item):
        """Test item deletion with unexpected error."""
        mock_delete_item.side_effect = Exception("Unexpected error")
        
        success, error_response = perform_item_deletion("test-item")
        
        assert success is False
        assert error_response is not None
        assert error_response["statusCode"] == 500


class TestCreateDeletionResponse:
    """Test create_deletion_response function."""
    
    def test_create_deletion_response_with_item(self):
        """Test creating deletion response with deleted item data."""
        deleted_item = {
            "id": "test-item",
            "name": "Test Item",
            "price": 99.99
        }
        
        response = create_deletion_response("test-item", deleted_item, True)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["id"] == "test-item"
        assert body["data"]["deleted"] is True
        assert body["data"]["deleted_item"] == deleted_item
        assert "deleted successfully" in body["message"]
    
    def test_create_deletion_response_without_item(self):
        """Test creating deletion response without deleted item data."""
        deleted_item = {"id": "test-item", "name": "Test Item"}
        
        response = create_deletion_response("test-item", deleted_item, False)
        
        body = json.loads(response["body"])
        assert body["data"]["id"] == "test-item"
        assert body["data"]["deleted"] is True
        assert "deleted_item" not in body["data"]
    
    def test_create_deletion_response_null_item(self):
        """Test creating deletion response with null deleted item."""
        response = create_deletion_response("test-item", None, True)
        
        body = json.loads(response["body"])
        assert body["data"]["id"] == "test-item"
        assert body["data"]["deleted"] is True
        assert "deleted_item" not in body["data"]


class TestHandleSoftDelete:
    """Test handle_soft_delete function."""
    
    def test_handle_soft_delete_disabled(self):
        """Test soft delete when disabled."""
        result = handle_soft_delete("test-item", False)
        assert result is None
    
    def test_handle_soft_delete_enabled(self):
        """Test soft delete when enabled (not implemented)."""
        result = handle_soft_delete("test-item", True)
        
        assert result is not None
        assert result["statusCode"] == 400
        
        body = json.loads(result["body"])
        assert "not yet implemented" in body["error"]["message"]


class TestValidateDeletionPermissions:
    """Test validate_deletion_permissions function."""
    
    def test_validate_deletion_permissions_allowed(self):
        """Test deletion permission validation (currently allows all)."""
        result = validate_deletion_permissions("test-item", {"user_id": "user123"})
        assert result is None
    
    def test_validate_deletion_permissions_no_context(self):
        """Test deletion permission validation without user context."""
        result = validate_deletion_permissions("test-item")
        assert result is None


class TestLogDeletionAudit:
    """Test log_deletion_audit function."""
    
    @patch('delete_handler.logging.getLogger')
    def test_log_deletion_audit_with_context(self, mock_get_logger):
        """Test audit logging with user context."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        deleted_item = {
            "id": "test-item",
            "name": "Test Item",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        user_context = {"user_id": "user123"}
        
        log_deletion_audit("test-item", deleted_item, user_context)
        
        mock_logger.setLevel.assert_called_once()
        mock_logger.info.assert_called_once()
        
        # Check that the log message contains expected data
        log_call_args = mock_logger.info.call_args[0][0]
        assert "DELETE" in log_call_args
        assert "test-item" in log_call_args
        assert "user123" in log_call_args
    
    @patch('delete_handler.logging.getLogger')
    def test_log_deletion_audit_without_context(self, mock_get_logger):
        """Test audit logging without user context."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        deleted_item = {"id": "test-item", "name": "Test Item"}
        
        log_deletion_audit("test-item", deleted_item)
        
        mock_logger.info.assert_called_once()
        
        log_call_args = mock_logger.info.call_args[0][0]
        assert "System" in log_call_args  # Default user when no context


class TestResponseHeaders:
    """Test response headers."""
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    @mock_dynamodb
    def test_response_has_cors_headers(self):
        """Test that responses include CORS headers."""
        # Set up DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='crud-api-items',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Add test item
        table.put_item(Item={
            "id": "test-item",
            "name": "Test Item",
            "price": 99.99,
            "quantity": 1,
            "is_active": True
        })
        
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "test-item"}
        }
        
        response = lambda_handler(event, MagicMock())
        
        headers = response["headers"]
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "GET,POST,PUT,DELETE,OPTIONS" in headers["Access-Control-Allow-Methods"]
        assert headers["Content-Type"] == "application/json"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    @mock_dynamodb
    def test_delete_item_with_special_characters_in_data(self):
        """Test deleting item with special characters in data."""
        # Set up DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='crud-api-items',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Add item with special characters
        special_item = {
            "id": "special-item-123",
            "name": "Item with 'quotes' and \"double quotes\"",
            "description": "Description with\nnewlines and\ttabs",
            "price": 99.99,
            "quantity": 1,
            "is_active": True,
            "tags": ["tag with spaces", "tag-with-dashes", "tag_with_underscores"]
        }
        table.put_item(Item=special_item)
        
        event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "special-item-123"}
        }
        
        response = lambda_handler(event, MagicMock())
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["data"]["deleted_item"]["name"] == "Item with 'quotes' and \"double quotes\""
        assert "newlines" in body["data"]["deleted_item"]["description"]


if __name__ == "__main__":
    pytest.main([__file__])