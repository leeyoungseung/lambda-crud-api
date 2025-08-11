"""
Unit tests for validation module.
Tests all JSON data types and validation scenarios.
"""

import pytest
from datetime import datetime
import sys
import os

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from validation import (
    validate_item_data, 
    validate_required_fields, 
    validate_data_types,
    validate_item_id,
    ValidationResult,
    ITEM_SCHEMA
)


class TestValidateItemData:
    """Test validate_item_data function."""
    
    def test_valid_complete_item(self):
        """Test validation with all valid fields."""
        data = {
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
        
        result = validate_item_data(data)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_valid_minimal_item(self):
        """Test validation with only required fields."""
        data = {
            "id": "test-123",
            "name": "Test",
            "price": 1.00,
            "quantity": 1,
            "is_active": True
        }
        
        result = validate_item_data(data)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_data_type(self):
        """Test validation with non-dict data."""
        result = validate_item_data("not a dict")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0]["field"] == "root"
        assert "JSON object" in result.errors[0]["message"]
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {
            "name": "Test Item"
            # Missing id, price, quantity, is_active
        }
        
        result = validate_item_data(data)
        assert result.is_valid is False
        assert len(result.errors) == 4  # id, price, quantity, is_active
        
        error_fields = [error["field"] for error in result.errors]
        assert "id" in error_fields
        assert "price" in error_fields
        assert "quantity" in error_fields
        assert "is_active" in error_fields
    
    def test_null_required_fields(self):
        """Test validation with null required fields."""
        data = {
            "id": None,
            "name": None,
            "price": None,
            "quantity": None,
            "is_active": None
        }
        
        result = validate_item_data(data)
        assert result.is_valid is False
        assert len(result.errors) == 5
        
        for error in result.errors:
            assert "cannot be null" in error["message"]
    
    def test_update_mode_optional_required_fields(self):
        """Test validation in update mode where required fields are optional."""
        data = {
            "name": "Updated Name",
            "price": 150.00
        }
        
        result = validate_item_data(data, is_update=True)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_unknown_field(self):
        """Test validation with unknown field."""
        data = {
            "id": "test-123",
            "name": "Test",
            "price": 1.00,
            "quantity": 1,
            "is_active": True,
            "unknown_field": "value"
        }
        
        result = validate_item_data(data)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0]["field"] == "unknown_field"
        assert "Unknown field" in result.errors[0]["message"]


class TestStringValidation:
    """Test string field validation."""
    
    def test_valid_string(self):
        """Test valid string validation."""
        data = {"name": "Valid Name"}
        result = validate_data_types(data, {"name": {"type": "string"}}, ValidationResult(True, []))
        assert result.is_valid is True
    
    def test_invalid_string_type(self):
        """Test invalid string type."""
        data = {"name": 123}
        result = validate_data_types(data, {"name": {"type": "string"}}, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be a string" in result.errors[0]["message"]
    
    def test_string_length_constraints(self):
        """Test string length validation."""
        schema = {"name": {"type": "string", "min_length": 3, "max_length": 10}}
        
        # Too short
        data = {"name": "ab"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "at least 3 characters" in result.errors[0]["message"]
        
        # Too long
        data = {"name": "this is too long"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "at most 10 characters" in result.errors[0]["message"]
    
    def test_string_pattern_validation(self):
        """Test string pattern validation."""
        schema = {"id": {"type": "string", "pattern": r"^[a-zA-Z0-9\-_]+$"}}
        
        # Valid pattern
        data = {"id": "valid-id_123"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is True
        
        # Invalid pattern
        data = {"id": "invalid@id!"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "invalid format" in result.errors[0]["message"]
    
    def test_iso_datetime_validation(self):
        """Test ISO datetime format validation."""
        schema = {"created_at": {"type": "string", "format": "iso_datetime"}}
        
        # Valid ISO datetime
        data = {"created_at": "2024-01-01T00:00:00Z"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is True
        
        # Invalid datetime
        data = {"created_at": "not a datetime"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "valid ISO datetime" in result.errors[0]["message"]


class TestIntegerValidation:
    """Test integer field validation."""
    
    def test_valid_integer(self):
        """Test valid integer validation."""
        data = {"quantity": 10}
        result = validate_data_types(data, {"quantity": {"type": "integer"}}, ValidationResult(True, []))
        assert result.is_valid is True
    
    def test_invalid_integer_type(self):
        """Test invalid integer types."""
        schema = {"quantity": {"type": "integer"}}
        
        # String
        data = {"quantity": "10"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be an integer" in result.errors[0]["message"]
        
        # Float
        data = {"quantity": 10.5}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be an integer" in result.errors[0]["message"]
        
        # Boolean (should be rejected)
        data = {"quantity": True}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be an integer" in result.errors[0]["message"]
    
    def test_integer_value_constraints(self):
        """Test integer value constraints."""
        schema = {"quantity": {"type": "integer", "min_value": 0, "max_value": 100}}
        
        # Below minimum
        data = {"quantity": -1}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "at least 0" in result.errors[0]["message"]
        
        # Above maximum
        data = {"quantity": 101}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "at most 100" in result.errors[0]["message"]


class TestFloatValidation:
    """Test float field validation."""
    
    def test_valid_float(self):
        """Test valid float validation."""
        data = {"price": 99.99}
        result = validate_data_types(data, {"price": {"type": "float"}}, ValidationResult(True, []))
        assert result.is_valid is True
        
        # Integer should also be valid for float
        data = {"price": 100}
        result = validate_data_types(data, {"price": {"type": "float"}}, ValidationResult(True, []))
        assert result.is_valid is True
    
    def test_invalid_float_type(self):
        """Test invalid float types."""
        schema = {"price": {"type": "float"}}
        
        # String
        data = {"price": "99.99"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be a number" in result.errors[0]["message"]
        
        # Boolean (should be rejected)
        data = {"price": True}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be a number" in result.errors[0]["message"]
    
    def test_float_value_constraints(self):
        """Test float value constraints."""
        schema = {"price": {"type": "float", "min_value": 0.01, "max_value": 999.99}}
        
        # Below minimum
        data = {"price": 0.001}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "at least 0.01" in result.errors[0]["message"]
        
        # Above maximum
        data = {"price": 1000.00}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "at most 999.99" in result.errors[0]["message"]


class TestBooleanValidation:
    """Test boolean field validation."""
    
    def test_valid_boolean(self):
        """Test valid boolean validation."""
        data = {"is_active": True}
        result = validate_data_types(data, {"is_active": {"type": "boolean"}}, ValidationResult(True, []))
        assert result.is_valid is True
        
        data = {"is_active": False}
        result = validate_data_types(data, {"is_active": {"type": "boolean"}}, ValidationResult(True, []))
        assert result.is_valid is True
    
    def test_invalid_boolean_type(self):
        """Test invalid boolean types."""
        schema = {"is_active": {"type": "boolean"}}
        
        # String
        data = {"is_active": "true"}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be a boolean" in result.errors[0]["message"]
        
        # Integer
        data = {"is_active": 1}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be a boolean" in result.errors[0]["message"]


class TestArrayValidation:
    """Test array field validation."""
    
    def test_valid_array(self):
        """Test valid array validation."""
        data = {"tags": ["tag1", "tag2"]}
        result = validate_data_types(data, {"tags": {"type": "array", "item_type": "string"}}, ValidationResult(True, []))
        assert result.is_valid is True
    
    def test_invalid_array_type(self):
        """Test invalid array type."""
        data = {"tags": "not an array"}
        result = validate_data_types(data, {"tags": {"type": "array"}}, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be an array" in result.errors[0]["message"]
    
    def test_array_max_items(self):
        """Test array max items constraint."""
        schema = {"tags": {"type": "array", "max_items": 2}}
        
        data = {"tags": ["tag1", "tag2", "tag3"]}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "at most 2 items" in result.errors[0]["message"]
    
    def test_array_item_type_validation(self):
        """Test array item type validation."""
        schema = {"tags": {"type": "array", "item_type": "string"}}
        
        # Invalid item type
        data = {"tags": ["valid", 123, "also_valid"]}
        result = validate_data_types(data, schema, ValidationResult(True, []))
        assert result.is_valid is False
        assert "tags[1]" in result.errors[0]["field"]
        assert "must be a string" in result.errors[0]["message"]


class TestObjectValidation:
    """Test object field validation."""
    
    def test_valid_object(self):
        """Test valid object validation."""
        data = {"metadata": {"key": "value", "nested": {"inner": "value"}}}
        result = validate_data_types(data, {"metadata": {"type": "object"}}, ValidationResult(True, []))
        assert result.is_valid is True
    
    def test_invalid_object_type(self):
        """Test invalid object type."""
        data = {"metadata": "not an object"}
        result = validate_data_types(data, {"metadata": {"type": "object"}}, ValidationResult(True, []))
        assert result.is_valid is False
        assert "must be an object" in result.errors[0]["message"]


class TestValidateItemId:
    """Test validate_item_id function."""
    
    def test_valid_item_id(self):
        """Test valid item ID."""
        result = validate_item_id("valid-id_123")
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_item_id_type(self):
        """Test invalid item ID type."""
        result = validate_item_id(123)
        assert result.is_valid is False
        assert "must be a string" in result.errors[0]["message"]
    
    def test_empty_item_id(self):
        """Test empty item ID."""
        result = validate_item_id("")
        assert result.is_valid is False
        assert "cannot be empty" in result.errors[0]["message"]
        
        result = validate_item_id("   ")
        assert result.is_valid is False
        assert "cannot be empty" in result.errors[0]["message"]
    
    def test_item_id_too_long(self):
        """Test item ID too long."""
        long_id = "a" * 51
        result = validate_item_id(long_id)
        assert result.is_valid is False
        assert "at most 50 characters" in result.errors[0]["message"]
    
    def test_item_id_invalid_characters(self):
        """Test item ID with invalid characters."""
        result = validate_item_id("invalid@id!")
        assert result.is_valid is False
        assert "letters, numbers, hyphens, and underscores" in result.errors[0]["message"]


class TestNullValues:
    """Test null value handling."""
    
    def test_null_optional_fields(self):
        """Test null values in optional fields."""
        data = {
            "id": "test-123",
            "name": "Test",
            "price": 1.00,
            "quantity": 1,
            "is_active": True,
            "description": None,  # Optional field
            "tags": None,         # Optional field
            "metadata": None      # Optional field
        }
        
        result = validate_item_data(data)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_array(self):
        """Test empty array validation."""
        data = {
            "id": "test-123",
            "name": "Test",
            "price": 1.00,
            "quantity": 1,
            "is_active": True,
            "tags": []
        }
        
        result = validate_item_data(data)
        assert result.is_valid is True
    
    def test_empty_object(self):
        """Test empty object validation."""
        data = {
            "id": "test-123",
            "name": "Test",
            "price": 1.00,
            "quantity": 1,
            "is_active": True,
            "metadata": {}
        }
        
        result = validate_item_data(data)
        assert result.is_valid is True
    
    def test_boundary_values(self):
        """Test boundary values."""
        data = {
            "id": "a",  # Minimum length
            "name": "a",  # Minimum length
            "price": 0.01,  # Minimum value
            "quantity": 0,  # Minimum value
            "is_active": False
        }
        
        result = validate_item_data(data)
        assert result.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__])