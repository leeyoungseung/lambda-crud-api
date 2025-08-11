"""
Integration tests for Lambda CRUD API.
Tests complete CRUD workflows and data flow between all components.
"""

import pytest
import json
import sys
import os
from unittest.mock import MagicMock
from moto import mock_dynamodb
import boto3

# Add the lambdas and shared modules to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambdas'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from create_handler import lambda_handler as create_handler
from read_handler import lambda_handler as read_handler
from update_handler import lambda_handler as update_handler
from delete_handler import lambda_handler as delete_handler


@mock_dynamodb
class TestCRUDIntegration:
    """Test complete CRUD workflows."""
    
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
        
        # Mock context
        self.context = MagicMock()
        self.context.aws_request_id = "integration-test-request"
        
        # Set environment variables
        os.environ['DYNAMODB_TABLE_NAME'] = self.table_name
        os.environ['AWS_REGION'] = 'us-east-1'
        
        # Sample item data for testing
        self.sample_item = {
            "name": "Integration Test Item",
            "description": "An item for integration testing",
            "price": 199.99,
            "quantity": 15,
            "is_active": True,
            "tags": ["integration", "test", "electronics"],
            "metadata": {
                "category": "electronics",
                "weight": 2.5,
                "dimensions": {
                    "length": 20,
                    "width": 15,
                    "height": 10
                },
                "features": ["wireless", "bluetooth", "rechargeable"]
            }
        }
    
    def test_complete_crud_workflow(self):
        """Test complete Create -> Read -> Update -> Delete workflow."""
        # Step 1: Create an item
        create_event = {
            "httpMethod": "POST",
            "body": json.dumps(self.sample_item)
        }
        
        create_response = create_handler(create_event, self.context)
        assert create_response["statusCode"] == 201
        
        create_body = json.loads(create_response["body"])
        assert create_body["success"] is True
        created_item = create_body["data"]
        item_id = created_item["id"]
        
        # Verify all data was stored correctly
        assert created_item["name"] == self.sample_item["name"]
        assert created_item["price"] == self.sample_item["price"]
        assert created_item["metadata"]["category"] == self.sample_item["metadata"]["category"]
        assert "created_at" in created_item
        assert "updated_at" in created_item
        
        # Step 2: Read the created item
        read_single_event = {
            "httpMethod": "GET",
            "pathParameters": {"id": item_id}
        }
        
        read_response = read_handler(read_single_event, self.context)
        assert read_response["statusCode"] == 200
        
        read_body = json.loads(read_response["body"])
        assert read_body["success"] is True
        retrieved_item = read_body["data"]
        
        # Verify retrieved item matches created item
        assert retrieved_item["id"] == item_id
        assert retrieved_item["name"] == created_item["name"]
        assert retrieved_item["price"] == created_item["price"]
        assert retrieved_item["metadata"] == created_item["metadata"]
        
        # Step 3: Read all items (should include our created item)
        read_all_event = {
            "httpMethod": "GET"
        }
        
        read_all_response = read_handler(read_all_event, self.context)
        assert read_all_response["statusCode"] == 200
        
        read_all_body = json.loads(read_all_response["body"])
        assert read_all_body["data"]["count"] == 1
        assert read_all_body["data"]["total"] == 1
        assert len(read_all_body["data"]["items"]) == 1
        assert read_all_body["data"]["items"][0]["id"] == item_id
        
        # Step 4: Update the item
        update_data = {
            "name": "Updated Integration Test Item",
            "price": 249.99,
            "quantity": 25,
            "description": "Updated description for integration testing",
            "tags": ["updated", "integration", "test"]
        }
        
        update_event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": item_id},
            "body": json.dumps(update_data)
        }
        
        update_response = update_handler(update_event, self.context)
        assert update_response["statusCode"] == 200
        
        update_body = json.loads(update_response["body"])
        assert update_body["success"] is True
        updated_item = update_body["data"]
        
        # Verify updates were applied
        assert updated_item["name"] == update_data["name"]
        assert updated_item["price"] == update_data["price"]
        assert updated_item["quantity"] == update_data["quantity"]
        assert updated_item["description"] == update_data["description"]
        assert updated_item["tags"] == update_data["tags"]
        
        # Verify protected fields weren't changed
        assert updated_item["id"] == item_id
        assert updated_item["created_at"] == created_item["created_at"]
        assert updated_item["updated_at"] != created_item["updated_at"]
        
        # Verify unchanged fields were preserved
        assert updated_item["is_active"] == created_item["is_active"]
        assert updated_item["metadata"] == created_item["metadata"]
        
        # Step 5: Read the updated item to verify persistence
        read_updated_response = read_handler(read_single_event, self.context)
        assert read_updated_response["statusCode"] == 200
        
        read_updated_body = json.loads(read_updated_response["body"])
        persisted_item = read_updated_body["data"]
        
        # Verify updates persisted
        assert persisted_item["name"] == update_data["name"]
        assert persisted_item["price"] == update_data["price"]
        assert persisted_item["updated_at"] == updated_item["updated_at"]
        
        # Step 6: Delete the item
        delete_event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": item_id}
        }
        
        delete_response = delete_handler(delete_event, self.context)
        assert delete_response["statusCode"] == 200
        
        delete_body = json.loads(delete_response["body"])
        assert delete_body["success"] is True
        assert delete_body["data"]["id"] == item_id
        assert delete_body["data"]["deleted"] is True
        assert "deleted_item" in delete_body["data"]
        
        # Step 7: Verify item is deleted (read should return 404)
        read_deleted_response = read_handler(read_single_event, self.context)
        assert read_deleted_response["statusCode"] == 404
        
        read_deleted_body = json.loads(read_deleted_response["body"])
        assert read_deleted_body["success"] is False
        assert read_deleted_body["error"]["code"] == "NOT_FOUND"
        
        # Step 8: Verify item is not in list of all items
        final_read_all_response = read_handler(read_all_event, self.context)
        assert final_read_all_response["statusCode"] == 200
        
        final_read_all_body = json.loads(final_read_all_response["body"])
        assert final_read_all_body["data"]["count"] == 0
        assert final_read_all_body["data"]["total"] == 0
        assert len(final_read_all_body["data"]["items"]) == 0
    
    def test_multiple_items_crud_workflow(self):
        """Test CRUD operations with multiple items."""
        items_data = [
            {
                "name": "Item 1",
                "price": 100.00,
                "quantity": 10,
                "is_active": True,
                "tags": ["electronics"]
            },
            {
                "name": "Item 2",
                "price": 200.00,
                "quantity": 20,
                "is_active": False,
                "tags": ["books"]
            },
            {
                "name": "Item 3",
                "price": 150.00,
                "quantity": 15,
                "is_active": True,
                "tags": ["electronics", "gadget"]
            }
        ]
        
        created_items = []
        
        # Create multiple items
        for item_data in items_data:
            create_event = {
                "httpMethod": "POST",
                "body": json.dumps(item_data)
            }
            
            create_response = create_handler(create_event, self.context)
            assert create_response["statusCode"] == 201
            
            create_body = json.loads(create_response["body"])
            created_items.append(create_body["data"])
        
        # Read all items
        read_all_event = {
            "httpMethod": "GET"
        }
        
        read_all_response = read_handler(read_all_event, self.context)
        assert read_all_response["statusCode"] == 200
        
        read_all_body = json.loads(read_all_response["body"])
        assert read_all_body["data"]["count"] == 3
        assert read_all_body["data"]["total"] == 3
        
        # Test filtering by is_active
        filter_event = {
            "httpMethod": "GET",
            "queryStringParameters": {"is_active": "true"}
        }
        
        filter_response = read_handler(filter_event, self.context)
        assert filter_response["statusCode"] == 200
        
        filter_body = json.loads(filter_response["body"])
        assert filter_body["data"]["count"] == 2  # Only active items
        
        # Update one item
        update_event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": created_items[0]["id"]},
            "body": json.dumps({"name": "Updated Item 1", "price": 120.00})
        }
        
        update_response = update_handler(update_event, self.context)
        assert update_response["statusCode"] == 200
        
        # Delete one item
        delete_event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": created_items[1]["id"]}
        }
        
        delete_response = delete_handler(delete_event, self.context)
        assert delete_response["statusCode"] == 200
        
        # Verify final state
        final_read_response = read_handler(read_all_event, self.context)
        final_read_body = json.loads(final_read_response["body"])
        assert final_read_body["data"]["count"] == 2  # One deleted
        
        # Verify updated item
        remaining_items = final_read_body["data"]["items"]
        updated_item = next(item for item in remaining_items if item["id"] == created_items[0]["id"])
        assert updated_item["name"] == "Updated Item 1"
        assert updated_item["price"] == 120.00
    
    def test_error_propagation_workflow(self):
        """Test error handling and propagation through the workflow."""
        # Test creating item with validation errors
        invalid_item = {
            "name": "",  # Invalid: too short
            "price": -10.00,  # Invalid: negative
            "quantity": "not a number",  # Invalid: wrong type
            "is_active": "not a boolean"  # Invalid: wrong type
        }
        
        create_event = {
            "httpMethod": "POST",
            "body": json.dumps(invalid_item)
        }
        
        create_response = create_handler(create_event, self.context)
        assert create_response["statusCode"] == 400
        
        create_body = json.loads(create_response["body"])
        assert create_body["success"] is False
        assert create_body["error"]["code"] == "VALIDATION_ERROR"
        assert len(create_body["error"]["details"]) > 0
        
        # Test reading non-existent item
        read_event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "non-existent-item"}
        }
        
        read_response = read_handler(read_event, self.context)
        assert read_response["statusCode"] == 404
        
        read_body = json.loads(read_response["body"])
        assert read_body["success"] is False
        assert read_body["error"]["code"] == "NOT_FOUND"
        
        # Test updating non-existent item
        update_event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "non-existent-item"},
            "body": json.dumps({"name": "Updated Name"})
        }
        
        update_response = update_handler(update_event, self.context)
        assert update_response["statusCode"] == 404
        
        update_body = json.loads(update_response["body"])
        assert update_body["success"] is False
        assert update_body["error"]["code"] == "NOT_FOUND"
        
        # Test deleting non-existent item
        delete_event = {
            "httpMethod": "DELETE",
            "pathParameters": {"id": "non-existent-item"}
        }
        
        delete_response = delete_handler(delete_event, self.context)
        assert delete_response["statusCode"] == 404
        
        delete_body = json.loads(delete_response["body"])
        assert delete_body["success"] is False
        assert delete_body["error"]["code"] == "NOT_FOUND"
    
    def test_data_consistency_workflow(self):
        """Test data consistency across operations."""
        # Create item with comprehensive data
        comprehensive_item = {
            "name": "Consistency Test Item",
            "description": "Testing data consistency",
            "price": 299.99,
            "quantity": 50,
            "is_active": True,
            "tags": ["consistency", "test", "comprehensive"],
            "metadata": {
                "category": "test",
                "weight": 3.5,
                "dimensions": {"length": 25, "width": 20, "height": 15},
                "features": ["feature1", "feature2", "feature3"],
                "nested": {
                    "level1": {
                        "level2": {
                            "value": "deep nested value"
                        }
                    }
                }
            }
        }
        
        # Create the item
        create_event = {
            "httpMethod": "POST",
            "body": json.dumps(comprehensive_item)
        }
        
        create_response = create_handler(create_event, self.context)
        assert create_response["statusCode"] == 201
        
        create_body = json.loads(create_response["body"])
        created_item = create_body["data"]
        item_id = created_item["id"]
        
        # Verify all nested data structures are preserved
        assert created_item["metadata"]["nested"]["level1"]["level2"]["value"] == "deep nested value"
        assert created_item["metadata"]["dimensions"]["length"] == 25
        assert created_item["metadata"]["features"] == ["feature1", "feature2", "feature3"]
        
        # Read and verify consistency
        read_event = {
            "httpMethod": "GET",
            "pathParameters": {"id": item_id}
        }
        
        read_response = read_handler(read_event, self.context)
        read_body = json.loads(read_response["body"])
        retrieved_item = read_body["data"]
        
        # Verify deep equality of complex structures
        assert retrieved_item["metadata"]["nested"] == created_item["metadata"]["nested"]
        assert retrieved_item["metadata"]["dimensions"] == created_item["metadata"]["dimensions"]
        assert retrieved_item["tags"] == created_item["tags"]
        
        # Update with complex data changes
        update_data = {
            "metadata": {
                "category": "updated",
                "weight": 4.0,
                "dimensions": {"length": 30, "width": 25, "height": 20},
                "features": ["updated_feature1", "updated_feature2"],
                "nested": {
                    "level1": {
                        "level2": {
                            "value": "updated deep nested value"
                        },
                        "new_field": "new value"
                    }
                },
                "new_top_level": "new top level value"
            },
            "tags": ["updated", "consistency", "test"]
        }
        
        update_event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": item_id},
            "body": json.dumps(update_data)
        }
        
        update_response = update_handler(update_event, self.context)
        update_body = json.loads(update_response["body"])
        updated_item = update_body["data"]
        
        # Verify complex updates were applied correctly
        assert updated_item["metadata"]["nested"]["level1"]["level2"]["value"] == "updated deep nested value"
        assert updated_item["metadata"]["nested"]["level1"]["new_field"] == "new value"
        assert updated_item["metadata"]["new_top_level"] == "new top level value"
        assert updated_item["metadata"]["dimensions"]["length"] == 30
        assert updated_item["tags"] == ["updated", "consistency", "test"]
        
        # Verify unchanged fields are preserved
        assert updated_item["name"] == comprehensive_item["name"]
        assert updated_item["price"] == comprehensive_item["price"]
        assert updated_item["quantity"] == comprehensive_item["quantity"]
        
        # Final read to verify persistence
        final_read_response = read_handler(read_event, self.context)
        final_read_body = json.loads(final_read_response["body"])
        final_item = final_read_body["data"]
        
        # Verify all changes persisted correctly
        assert final_item["metadata"]["nested"]["level1"]["new_field"] == "new value"
        assert final_item["metadata"]["new_top_level"] == "new top level value"
        assert final_item["tags"] == ["updated", "consistency", "test"]


class TestCORSIntegration:
    """Test CORS handling across all endpoints."""
    
    def setup_method(self):
        """Set up test environment."""
        self.context = MagicMock()
        self.context.aws_request_id = "cors-test-request"
    
    def test_cors_preflight_all_handlers(self):
        """Test CORS preflight requests for all handlers."""
        preflight_event = {
            "httpMethod": "OPTIONS"
        }
        
        # Test Create handler
        create_response = create_handler(preflight_event, self.context)
        assert create_response["statusCode"] == 200
        assert create_response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "POST" in create_response["headers"]["Access-Control-Allow-Methods"]
        
        # Test Read handler
        read_response = read_handler(preflight_event, self.context)
        assert read_response["statusCode"] == 200
        assert read_response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET" in read_response["headers"]["Access-Control-Allow-Methods"]
        
        # Test Update handler
        update_response = update_handler(preflight_event, self.context)
        assert update_response["statusCode"] == 200
        assert update_response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "PUT" in update_response["headers"]["Access-Control-Allow-Methods"]
        
        # Test Delete handler
        delete_response = delete_handler(preflight_event, self.context)
        assert delete_response["statusCode"] == 200
        assert delete_response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "DELETE" in delete_response["headers"]["Access-Control-Allow-Methods"]


class TestValidationIntegration:
    """Test validation integration across all operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.context = MagicMock()
        self.context.aws_request_id = "validation-test-request"
    
    def test_validation_consistency_across_operations(self):
        """Test that validation rules are consistent across create and update."""
        # Test data that should fail validation
        invalid_data = {
            "name": "",  # Too short
            "price": -10.00,  # Negative
            "quantity": -5,  # Negative
            "is_active": "not_boolean",  # Wrong type
            "tags": "not_array",  # Wrong type
            "metadata": "not_object"  # Wrong type
        }
        
        # Test create validation
        create_event = {
            "httpMethod": "POST",
            "body": json.dumps(invalid_data)
        }
        
        create_response = create_handler(create_event, self.context)
        assert create_response["statusCode"] == 400
        
        create_body = json.loads(create_response["body"])
        create_errors = create_body["error"]["details"]
        
        # Test update validation (should have similar errors)
        update_event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-item"},
            "body": json.dumps(invalid_data)
        }
        
        update_response = update_handler(update_event, self.context)
        assert update_response["statusCode"] == 400
        
        update_body = json.loads(update_response["body"])
        update_errors = update_body["error"]["details"]
        
        # Verify similar validation errors (excluding required field errors for update)
        create_error_fields = {error["field"] for error in create_errors}
        update_error_fields = {error["field"] for error in update_errors}
        
        # Common validation errors should be present in both
        common_fields = {"name", "price", "quantity", "is_active", "tags", "metadata"}
        assert common_fields.issubset(create_error_fields)
        assert common_fields.issubset(update_error_fields)


if __name__ == "__main__":
    pytest.main([__file__])