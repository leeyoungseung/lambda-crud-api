"""
Unit tests for Read Lambda handler.
Tests item retrieval functionality and error handling.
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

from read_handler import (
    lambda_handler, 
    handle_get_single_item, 
    handle_get_all_items,
    apply_query_filters,
    validate_query_parameters
)
from dynamodb_client import DynamoDBError


@mock_dynamodb
class TestReadHandler:
    """Test Read Lambda handler."""
    
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
        
        # Sample test items
        self.test_items = [
            {
                "id": "item-1",
                "name": "Test Item 1",
                "description": "First test item",
                "price": 99.99,
                "quantity": 10,
                "is_active": True,
                "tags": ["electronics", "gadget"],
                "metadata": {"category": "electronics"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "item-2",
                "name": "Test Item 2",
                "description": "Second test item",
                "price": 149.99,
                "quantity": 5,
                "is_active": False,
                "tags": ["books", "education"],
                "metadata": {"category": "books"},
                "created_at": "2024-01-02T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z"
            },
            {
                "id": "item-3",
                "name": "Test Item 3",
                "description": "Third test item",
                "price": 49.99,
                "quantity": 20,
                "is_active": True,
                "tags": ["electronics", "accessories"],
                "metadata": {"category": "electronics"},
                "created_at": "2024-01-03T00:00:00Z",
                "updated_at": "2024-01-03T00:00:00Z"
            }
        ]
        
        # Mock context
        self.context = MagicMock()
        self.context.aws_request_id = "test-request-id"
        
        # Populate table with test data
        for item in self.test_items:
            self.table.put_item(Item=item)
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_get_single_item_success(self):
        """Test successful single item retrieval."""
        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "item-1"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["id"] == "item-1"
        assert body["data"]["name"] == "Test Item 1"
        assert body["data"]["price"] == 99.99
        assert "retrieved successfully" in body["message"]
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_get_single_item_not_found(self):
        """Test single item retrieval when item doesn't exist."""
        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "non-existent-item"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 404
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"
        assert "non-existent-item" in body["error"]["message"]
    
    def test_get_single_item_missing_id(self):
        """Test single item retrieval with missing ID parameter."""
        event = {
            "httpMethod": "GET",
            "pathParameters": {}
        }
        
        response = lambda_handler(event, self.context)
        
        # Should fall back to get all items since no ID provided
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert "items" in body["data"]
    
    def test_get_single_item_invalid_id_format(self):
        """Test single item retrieval with invalid ID format."""
        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "invalid@id!"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "Invalid item ID format" in body["error"]["message"]
    
    def test_get_single_item_empty_id(self):
        """Test single item retrieval with empty ID."""
        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": ""}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 400
        
        body = json.loads(response["body"])
        assert "cannot be empty" in body["error"]["details"][0]["message"]
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_get_all_items_success(self):
        """Test successful retrieval of all items."""
        event = {
            "httpMethod": "GET"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert "items" in body["data"]
        assert "count" in body["data"]
        assert "total" in body["data"]
        assert body["data"]["count"] == 3
        assert body["data"]["total"] == 3
        assert len(body["data"]["items"]) == 3
        
        # Check that all test items are present
        item_ids = [item["id"] for item in body["data"]["items"]]
        assert "item-1" in item_ids
        assert "item-2" in item_ids
        assert "item-3" in item_ids
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_get_all_items_empty_table(self):
        """Test retrieval from empty table."""
        # Clear the table
        for item in self.test_items:
            self.table.delete_item(Key={'id': item['id']})
        
        event = {
            "httpMethod": "GET"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["data"]["count"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_get_all_items_with_filters(self):
        """Test retrieval with query parameter filters."""
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "is_active": "true"
            }
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["data"]["count"] == 2  # Only active items
        assert body["data"]["total"] == 3  # Total items in table
        
        # Check that only active items are returned
        for item in body["data"]["items"]:
            assert item["is_active"] is True
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_get_all_items_price_filter(self):
        """Test retrieval with price range filters."""
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "min_price": "50.00",
                "max_price": "100.00"
            }
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["data"]["count"] == 1  # Only item-1 (99.99) fits the range
        
        # Check price range
        for item in body["data"]["items"]:
            assert 50.00 <= item["price"] <= 100.00
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_get_all_items_tag_filter(self):
        """Test retrieval with tag filter."""
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "tag": "electronics"
            }
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        
        body = json.loads(response["body"])
        assert body["data"]["count"] == 2  # item-1 and item-3 have electronics tag
        
        # Check that all returned items have the electronics tag
        for item in body["data"]["items"]:
            assert "electronics" in item["tags"]
    
    def test_cors_preflight(self):
        """Test CORS preflight OPTIONS request."""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["body"] == ""
    
    @patch('read_handler.get_item')
    def test_get_single_item_dynamodb_error(self, mock_get_item):
        """Test handling of DynamoDB errors in single item retrieval."""
        mock_get_item.side_effect = DynamoDBError("Database connection failed", "CONNECTION_ERROR")
        
        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "test-item"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "Database connection failed" in body["error"]["message"]
    
    @patch('read_handler.get_all_items')
    def test_get_all_items_dynamodb_error(self, mock_get_all_items):
        """Test handling of DynamoDB errors in get all items."""
        mock_get_all_items.side_effect = DynamoDBError("Database connection failed", "CONNECTION_ERROR")
        
        event = {
            "httpMethod": "GET"
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert "Database connection failed" in body["error"]["message"]
    
    @patch('read_handler.validate_item_id')
    def test_get_single_item_unexpected_error(self, mock_validate):
        """Test handling of unexpected errors."""
        mock_validate.side_effect = Exception("Unexpected error")
        
        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "test-item"}
        }
        
        response = lambda_handler(event, self.context)
        
        assert response["statusCode"] == 500
        
        body = json.loads(response["body"])
        assert "Unexpected error" in body["error"]["message"]


class TestApplyQueryFilters:
    """Test apply_query_filters function."""
    
    def setup_method(self):
        """Set up test data."""
        self.test_items = [
            {
                "id": "item-1",
                "name": "Item 1",
                "price": 99.99,
                "is_active": True,
                "tags": ["electronics", "gadget"]
            },
            {
                "id": "item-2",
                "name": "Item 2",
                "price": 149.99,
                "is_active": False,
                "tags": ["books", "education"]
            },
            {
                "id": "item-3",
                "name": "Item 3",
                "price": 49.99,
                "is_active": True,
                "tags": ["electronics", "accessories"]
            }
        ]
    
    def test_no_filters(self):
        """Test with no query parameters."""
        result = apply_query_filters(self.test_items, {})
        assert len(result) == 3
        assert result == self.test_items
    
    def test_is_active_filter_true(self):
        """Test filtering by is_active=true."""
        result = apply_query_filters(self.test_items, {"is_active": "true"})
        assert len(result) == 2
        for item in result:
            assert item["is_active"] is True
    
    def test_is_active_filter_false(self):
        """Test filtering by is_active=false."""
        result = apply_query_filters(self.test_items, {"is_active": "false"})
        assert len(result) == 1
        assert result[0]["id"] == "item-2"
    
    def test_min_price_filter(self):
        """Test filtering by minimum price."""
        result = apply_query_filters(self.test_items, {"min_price": "75.00"})
        assert len(result) == 2
        for item in result:
            assert item["price"] >= 75.00
    
    def test_max_price_filter(self):
        """Test filtering by maximum price."""
        result = apply_query_filters(self.test_items, {"max_price": "100.00"})
        assert len(result) == 2
        for item in result:
            assert item["price"] <= 100.00
    
    def test_price_range_filter(self):
        """Test filtering by price range."""
        result = apply_query_filters(self.test_items, {
            "min_price": "50.00",
            "max_price": "100.00"
        })
        assert len(result) == 1
        assert result[0]["id"] == "item-1"
    
    def test_tag_filter(self):
        """Test filtering by tag."""
        result = apply_query_filters(self.test_items, {"tag": "electronics"})
        assert len(result) == 2
        for item in result:
            assert "electronics" in item["tags"]
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        result = apply_query_filters(self.test_items, {
            "is_active": "true",
            "tag": "electronics"
        })
        assert len(result) == 2
        for item in result:
            assert item["is_active"] is True
            assert "electronics" in item["tags"]
    
    def test_invalid_price_filter(self):
        """Test with invalid price filter values."""
        # Should ignore invalid filters
        result = apply_query_filters(self.test_items, {"min_price": "invalid"})
        assert len(result) == 3  # No filtering applied
    
    def test_nonexistent_tag_filter(self):
        """Test filtering by non-existent tag."""
        result = apply_query_filters(self.test_items, {"tag": "nonexistent"})
        assert len(result) == 0


class TestValidateQueryParameters:
    """Test validate_query_parameters function."""
    
    def test_valid_parameters(self):
        """Test with valid query parameters."""
        params = {
            "is_active": "true",
            "min_price": "10.00",
            "max_price": "100.00",
            "tag": "electronics"
        }
        
        result = validate_query_parameters(params)
        assert result is None
    
    def test_invalid_is_active(self):
        """Test with invalid is_active parameter."""
        params = {"is_active": "maybe"}
        
        result = validate_query_parameters(params)
        
        assert result is not None
        assert result["statusCode"] == 400
        
        body = json.loads(result["body"])
        assert "is_active parameter must be" in body["error"]["details"][0]["message"]
    
    def test_invalid_min_price(self):
        """Test with invalid min_price parameter."""
        params = {"min_price": "not_a_number"}
        
        result = validate_query_parameters(params)
        
        assert result is not None
        body = json.loads(result["body"])
        assert "valid number" in body["error"]["details"][0]["message"]
    
    def test_negative_price(self):
        """Test with negative price parameters."""
        params = {
            "min_price": "-10.00",
            "max_price": "-5.00"
        }
        
        result = validate_query_parameters(params)
        
        assert result is not None
        body = json.loads(result["body"])
        assert len(body["error"]["details"]) == 2
    
    def test_invalid_price_range(self):
        """Test with invalid price range (min > max)."""
        params = {
            "min_price": "100.00",
            "max_price": "50.00"
        }
        
        result = validate_query_parameters(params)
        
        assert result is not None
        body = json.loads(result["body"])
        assert "min_price cannot be greater than max_price" in body["error"]["details"][0]["message"]


class TestHandleFunctions:
    """Test individual handle functions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.context = MagicMock()
        self.context.aws_request_id = "test-request-id"
    
    @patch('read_handler.get_item')
    def test_handle_get_single_item_success(self, mock_get_item):
        """Test handle_get_single_item with successful retrieval."""
        mock_get_item.return_value = {"id": "test-item", "name": "Test Item"}
        
        event = {
            "pathParameters": {"id": "test-item"}
        }
        
        response = handle_get_single_item(event, self.context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["id"] == "test-item"
    
    @patch('read_handler.get_all_items')
    def test_handle_get_all_items_success(self, mock_get_all_items):
        """Test handle_get_all_items with successful retrieval."""
        mock_get_all_items.return_value = [
            {"id": "item-1", "name": "Item 1"},
            {"id": "item-2", "name": "Item 2"}
        ]
        
        event = {}
        
        response = handle_get_all_items(event, self.context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["count"] == 2
        assert len(body["data"]["items"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])