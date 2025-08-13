"""
Unit tests for DynamoDB client module.
Uses moto library to mock DynamoDB operations.
"""

import pytest
import boto3
import os
import sys
from decimal import Decimal
from moto import mock_dynamodb
from unittest.mock import patch

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_client import (
    DynamoDBClient,
    DynamoDBError,
    create_item,
    get_item,
    get_all_items,
    update_item,
    delete_item
)


@mock_dynamodb
class TestDynamoDBClient:
    """Test DynamoDBClient class."""
    
    def setup_method(self, method):
        """Set up test environment before each test."""
        # Create mock DynamoDB table
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'test-crud-api-items'
        
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
        
        # Initialize client
        self.client = DynamoDBClient(table_name=self.table_name, region_name='us-east-1')
        
        # Sample test data
        self.sample_item = {
            "id": "test-item-123",
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
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    
    def test_create_item_success(self):
        """Test successful item creation."""
        result = self.client.create_item(self.sample_item)
        
        assert result == self.sample_item
        
        # Verify item was actually created
        stored_item = self.client.get_item("test-item-123")
        assert stored_item is not None
        assert stored_item["name"] == "Test Item"
        assert stored_item["price"] == 99.99
    
    def test_create_item_duplicate_id(self):
        """Test creating item with duplicate ID."""
        # Create first item
        self.client.create_item(self.sample_item)
        
        # Try to create duplicate
        with pytest.raises(DynamoDBError) as exc_info:
            self.client.create_item(self.sample_item)
        
        assert exc_info.value.error_code == "ITEM_EXISTS"
        assert "already exists" in str(exc_info.value)
    
    def test_create_item_with_floats(self):
        """Test creating item with float values (Decimal conversion)."""
        item_with_floats = {
            "id": "float-test",
            "name": "Float Test",
            "price": 123.45,
            "quantity": 1,
            "is_active": True,
            "metadata": {
                "weight": 2.5,
                "nested": {
                    "value": 3.14
                }
            }
        }
        
        result = self.client.create_item(item_with_floats)
        
        # Result should have floats converted back
        assert isinstance(result["price"], float)
        assert result["price"] == 123.45
        assert isinstance(result["metadata"]["weight"], float)
        assert result["metadata"]["weight"] == 2.5
    
    def test_get_item_success(self):
        """Test successful item retrieval."""
        # Create item first
        self.client.create_item(self.sample_item)
        
        # Retrieve item
        result = self.client.get_item("test-item-123")
        
        assert result is not None
        assert result["id"] == "test-item-123"
        assert result["name"] == "Test Item"
        assert result["price"] == 99.99
        assert isinstance(result["price"], float)  # Should be converted from Decimal
    
    def test_get_item_not_found(self):
        """Test retrieving non-existent item."""
        result = self.client.get_item("non-existent-id")
        assert result is None
    
    def test_get_all_items_empty(self):
        """Test getting all items from empty table."""
        result = self.client.get_all_items()
        assert result == []
    
    def test_get_all_items_with_data(self):
        """Test getting all items with data."""
        # Create multiple items
        item1 = self.sample_item.copy()
        item2 = self.sample_item.copy()
        item2["id"] = "test-item-456"
        item2["name"] = "Second Item"
        
        self.client.create_item(item1)
        self.client.create_item(item2)
        
        # Get all items
        result = self.client.get_all_items()
        
        assert len(result) == 2
        ids = [item["id"] for item in result]
        assert "test-item-123" in ids
        assert "test-item-456" in ids
    
    def test_update_item_success(self):
        """Test successful item update."""
        # Create item first
        self.client.create_item(self.sample_item)
        
        # Update item
        update_data = {
            "name": "Updated Item",
            "price": 149.99,
            "quantity": 20,
            "updated_at": "2024-01-02T00:00:00Z"
        }
        
        result = self.client.update_item("test-item-123", update_data)
        
        assert result["name"] == "Updated Item"
        assert result["price"] == 149.99
        assert result["quantity"] == 20
        assert result["updated_at"] == "2024-01-02T00:00:00Z"
        # Original fields should be preserved
        assert result["description"] == "A test item description"
        assert result["is_active"] is True
    
    def test_update_item_not_found(self):
        """Test updating non-existent item."""
        update_data = {"name": "Updated Item"}
        
        with pytest.raises(DynamoDBError) as exc_info:
            self.client.update_item("non-existent-id", update_data)
        
        assert exc_info.value.error_code == "ITEM_NOT_FOUND"
        assert "not found" in str(exc_info.value)
    
    def test_update_item_partial(self):
        """Test partial item update."""
        # Create item first
        self.client.create_item(self.sample_item)
        
        # Update only one field
        update_data = {"name": "Partially Updated"}
        
        result = self.client.update_item("test-item-123", update_data)
        
        assert result["name"] == "Partially Updated"
        # Other fields should remain unchanged
        assert result["price"] == 99.99
        assert result["quantity"] == 10
        assert result["description"] == "A test item description"
    
    def test_update_item_id_preservation(self):
        """Test that item ID cannot be changed during update."""
        # Create item first
        self.client.create_item(self.sample_item)
        
        # Try to update ID (should be ignored)
        update_data = {
            "id": "different-id",
            "name": "Updated Item"
        }
        
        result = self.client.update_item("test-item-123", update_data)
        
        # ID should remain the same
        assert result["id"] == "test-item-123"
        assert result["name"] == "Updated Item"
    
    def test_delete_item_success(self):
        """Test successful item deletion."""
        # Create item first
        self.client.create_item(self.sample_item)
        
        # Verify item exists
        assert self.client.get_item("test-item-123") is not None
        
        # Delete item
        result = self.client.delete_item("test-item-123")
        
        assert result is True
        
        # Verify item is gone
        assert self.client.get_item("test-item-123") is None
    
    def test_delete_item_not_found(self):
        """Test deleting non-existent item."""
        result = self.client.delete_item("non-existent-id")
        assert result is False
    
    def test_item_exists_true(self):
        """Test _item_exists method when item exists."""
        self.client.create_item(self.sample_item)
        assert self.client._item_exists("test-item-123") is True
    
    def test_item_exists_false(self):
        """Test _item_exists method when item doesn't exist."""
        assert self.client._item_exists("non-existent-id") is False
    
    def test_convert_floats_to_decimal(self):
        """Test float to Decimal conversion."""
        data = {
            "price": 99.99,
            "nested": {
                "weight": 1.5,
                "dimensions": [10.0, 5.0, 3.0]
            },
            "string_field": "test",
            "int_field": 42
        }
        
        result = self.client._convert_floats_to_decimal(data)
        
        assert isinstance(result["price"], Decimal)
        assert isinstance(result["nested"]["weight"], Decimal)
        assert isinstance(result["nested"]["dimensions"][0], Decimal)
        assert isinstance(result["string_field"], str)
        assert isinstance(result["int_field"], int)
    
    def test_convert_decimal_to_float(self):
        """Test Decimal to float conversion."""
        data = {
            "price": Decimal("99.99"),
            "nested": {
                "weight": Decimal("1.5"),
                "dimensions": [Decimal("10.0"), Decimal("5.0"), Decimal("3.0")]
            },
            "string_field": "test",
            "int_field": 42
        }
        
        result = self.client._convert_decimal_to_float(data)
        
        assert isinstance(result["price"], float)
        assert isinstance(result["nested"]["weight"], float)
        assert isinstance(result["nested"]["dimensions"][0], float)
        assert isinstance(result["string_field"], str)
        assert isinstance(result["int_field"], int)


@mock_dynamodb
class TestModuleFunctions:
    """Test module-level convenience functions."""
    
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
        
        self.sample_item = {
            "id": "module-test-123",
            "name": "Module Test Item",
            "price": 50.00,
            "quantity": 5,
            "is_active": True
        }
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_module_create_item(self):
        """Test module-level create_item function."""
        result = create_item(self.sample_item)
        assert result["id"] == "module-test-123"
        assert result["name"] == "Module Test Item"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_module_get_item(self):
        """Test module-level get_item function."""
        # Create item first
        create_item(self.sample_item)
        
        # Get item
        result = get_item("module-test-123")
        assert result is not None
        assert result["name"] == "Module Test Item"
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_module_get_all_items(self):
        """Test module-level get_all_items function."""
        # Create items
        create_item(self.sample_item)
        
        item2 = self.sample_item.copy()
        item2["id"] = "module-test-456"
        create_item(item2)
        
        # Get all items
        result = get_all_items()
        assert len(result) == 2
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_module_update_item(self):
        """Test module-level update_item function."""
        # Create item first
        create_item(self.sample_item)
        
        # Update item
        update_data = {"name": "Updated Module Test"}
        result = update_item("module-test-123", update_data)
        
        assert result["name"] == "Updated Module Test"
        assert result["price"] == 50.00  # Unchanged
    
    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'crud-api-items', 'AWS_REGION': 'us-east-1'})
    def test_module_delete_item(self):
        """Test module-level delete_item function."""
        # Create item first
        create_item(self.sample_item)
        
        # Delete item
        result = delete_item("module-test-123")
        assert result is True
        
        # Verify deletion
        assert get_item("module-test-123") is None


class TestDynamoDBError:
    """Test DynamoDBError exception."""
    
    def test_dynamodb_error_creation(self):
        """Test DynamoDBError creation."""
        error = DynamoDBError("Test error message", "TEST_ERROR")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"
    
    def test_dynamodb_error_default_code(self):
        """Test DynamoDBError with default error code."""
        error = DynamoDBError("Test error message")
        
        assert error.error_code == "DYNAMODB_ERROR"


@mock_dynamodb
class TestErrorHandling:
    """Test error handling scenarios."""
    
    def setup_method(self, method):
        """Set up test environment before each test."""
        # Create mock DynamoDB table
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'test-crud-api-items'
        
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
        
        self.client = DynamoDBClient(table_name=self.table_name, region_name='us-east-1')
    
    def test_initialization_error(self):
        """Test DynamoDB client initialization error."""
        with pytest.raises(DynamoDBError) as exc_info:
            DynamoDBClient(table_name="non-existent-table", region_name="invalid-region")
        
        assert exc_info.value.error_code == "INIT_ERROR"
    
    def test_scan_pagination(self):
        """Test scan operation with pagination (simulated)."""
        # Create multiple items to test pagination
        for i in range(5):
            item = {
                "id": f"pagination-test-{i}",
                "name": f"Item {i}",
                "price": 10.0 + i,
                "quantity": i,
                "is_active": True
            }
            self.client.create_item(item)
        
        # Get all items (should handle pagination internally)
        result = self.client.get_all_items()
        
        assert len(result) == 5
        ids = [item["id"] for item in result]
        for i in range(5):
            assert f"pagination-test-{i}" in ids


if __name__ == "__main__":
    pytest.main([__file__])