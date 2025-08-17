"""
Data validation module for Lambda CRUD API.
Provides comprehensive validation for all JSON data types.
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Union, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    errors: List[Dict[str, str]]
    
    def add_error(self, field: str, message: str):
        """Add validation error."""
        self.errors.append({"field": field, "message": message})
        self.is_valid = False


# Item schema definition with all JSON data types
ITEM_SCHEMA = {
    "id": {
        "type": "string", 
        "required": True, 
        "max_length": 50,
        "pattern": r"^[a-zA-Z0-9\-_]+$"
    },
    "name": {
        "type": "string", 
        "required": True, 
        "max_length": 100,
        "min_length": 1
    },
    "description": {
        "type": "string", 
        "required": False, 
        "max_length": 500
    },
    "price": {
        "type": "float", 
        "required": True, 
        "min_value": 0.01,
        "max_value": 999999.99
    },
    "quantity": {
        "type": "integer", 
        "required": True, 
        "min_value": 0,
        "max_value": 999999
    },
    "is_active": {
        "type": "boolean", 
        "required": True
    },
    "tags": {
        "type": "array", 
        "required": False, 
        "item_type": "string",
        "max_items": 10
    },
    "metadata": {
        "type": "object", 
        "required": False
    },
    "created_at": {
        "type": "string", 
        "required": False, 
        "format": "iso_datetime"
    },
    "updated_at": {
        "type": "string", 
        "required": False, 
        "format": "iso_datetime"
    }
}


def validate_item_data(data: Dict[str, Any], schema: Dict[str, Any] = ITEM_SCHEMA, 
                      is_update: bool = False, is_create: bool = False) -> ValidationResult:
    """
    Validate item data against schema.
    
    Args:
        data: Data to validate
        schema: Validation schema
        is_update: If True, required fields are optional (for updates)
        is_create: If True, id field is not required (for creates)
    
    Returns:
        ValidationResult with validation status and errors
    """
    result = ValidationResult(is_valid=True, errors=[])
    
    if not isinstance(data, dict):
        result.add_error("root", "Data must be a JSON object")
        return result
    
    # For create operations, modify schema to make id optional
    if is_create:
        schema = schema.copy()
        if 'id' in schema:
            schema['id'] = schema['id'].copy()
            schema['id']['required'] = False
    
    # Validate required fields
    if not is_update:
        result = validate_required_fields(data, schema, result)
    
    # Validate data types and constraints
    result = validate_data_types(data, schema, result)
    
    return result


def validate_required_fields(data: Dict[str, Any], schema: Dict[str, Any], 
                           result: ValidationResult) -> ValidationResult:
    """
    Validate that all required fields are present and not null.
    
    Args:
        data: Data to validate
        schema: Validation schema
        result: ValidationResult to update
    
    Returns:
        Updated ValidationResult
    """
    for field_name, field_schema in schema.items():
        if field_schema.get("required", False):
            if field_name not in data:
                result.add_error(field_name, f"Field '{field_name}' is required")
            elif data[field_name] is None:
                result.add_error(field_name, f"Field '{field_name}' cannot be null")
    
    return result


def validate_data_types(data: Dict[str, Any], schema: Dict[str, Any], 
                       result: ValidationResult) -> ValidationResult:
    """
    Validate data types and constraints for each field.
    
    Args:
        data: Data to validate
        schema: Validation schema
        result: ValidationResult to update
    
    Returns:
        Updated ValidationResult
    """
    for field_name, value in data.items():
        if field_name not in schema:
            result.add_error(field_name, f"Unknown field '{field_name}'")
            continue
        
        field_schema = schema[field_name]
        
        # Skip validation for null fields (required field null check is done separately)
        if value is None:
            continue
        
        # Validate based on field type
        field_type = field_schema["type"]
        
        if field_type == "string":
            result = _validate_string(field_name, value, field_schema, result)
        elif field_type == "integer":
            result = _validate_integer(field_name, value, field_schema, result)
        elif field_type == "float":
            result = _validate_float(field_name, value, field_schema, result)
        elif field_type == "boolean":
            result = _validate_boolean(field_name, value, field_schema, result)
        elif field_type == "array":
            result = _validate_array(field_name, value, field_schema, result)
        elif field_type == "object":
            result = _validate_object(field_name, value, field_schema, result)
    
    return result


def _validate_string(field_name: str, value: Any, schema: Dict[str, Any], 
                    result: ValidationResult) -> ValidationResult:
    """Validate string field."""
    if not isinstance(value, str):
        result.add_error(field_name, f"Field '{field_name}' must be a string")
        return result
    
    # Check length constraints
    if "min_length" in schema and len(value) < schema["min_length"]:
        result.add_error(field_name, 
                        f"Field '{field_name}' must be at least {schema['min_length']} characters")
    
    if "max_length" in schema and len(value) > schema["max_length"]:
        result.add_error(field_name, 
                        f"Field '{field_name}' must be at most {schema['max_length']} characters")
    
    # Check pattern
    if "pattern" in schema and not re.match(schema["pattern"], value):
        result.add_error(field_name, f"Field '{field_name}' has invalid format")
    
    # Check datetime format
    if schema.get("format") == "iso_datetime":
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            result.add_error(field_name, f"Field '{field_name}' must be a valid ISO datetime")
    
    return result


def _validate_integer(field_name: str, value: Any, schema: Dict[str, Any], 
                     result: ValidationResult) -> ValidationResult:
    """Validate integer field."""
    if not isinstance(value, int) or isinstance(value, bool):
        result.add_error(field_name, f"Field '{field_name}' must be an integer")
        return result
    
    # Check value constraints
    if "min_value" in schema and value < schema["min_value"]:
        result.add_error(field_name, 
                        f"Field '{field_name}' must be at least {schema['min_value']}")
    
    if "max_value" in schema and value > schema["max_value"]:
        result.add_error(field_name, 
                        f"Field '{field_name}' must be at most {schema['max_value']}")
    
    return result


def _validate_float(field_name: str, value: Any, schema: Dict[str, Any], 
                   result: ValidationResult) -> ValidationResult:
    """Validate float field."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        result.add_error(field_name, f"Field '{field_name}' must be a number")
        return result
    
    # Convert to float for validation
    float_value = float(value)
    
    # Check value constraints
    if "min_value" in schema and float_value < schema["min_value"]:
        result.add_error(field_name, 
                        f"Field '{field_name}' must be at least {schema['min_value']}")
    
    if "max_value" in schema and float_value > schema["max_value"]:
        result.add_error(field_name, 
                        f"Field '{field_name}' must be at most {schema['max_value']}")
    
    return result


def _validate_boolean(field_name: str, value: Any, schema: Dict[str, Any], 
                     result: ValidationResult) -> ValidationResult:
    """Validate boolean field."""
    if not isinstance(value, bool):
        result.add_error(field_name, f"Field '{field_name}' must be a boolean")
    
    return result


def _validate_array(field_name: str, value: Any, schema: Dict[str, Any], 
                   result: ValidationResult) -> ValidationResult:
    """Validate array field."""
    if not isinstance(value, list):
        result.add_error(field_name, f"Field '{field_name}' must be an array")
        return result
    
    # Check array length
    if "max_items" in schema and len(value) > schema["max_items"]:
        result.add_error(field_name, 
                        f"Field '{field_name}' must have at most {schema['max_items']} items")
    
    # Validate array items
    if "item_type" in schema:
        item_type = schema["item_type"]
        for i, item in enumerate(value):
            if item_type == "string" and not isinstance(item, str):
                result.add_error(f"{field_name}[{i}]", 
                               f"Field '{field_name}[{i}]' must be a string")
            elif item_type == "integer" and (not isinstance(item, int) or isinstance(item, bool)):
                result.add_error(f"{field_name}[{i}]", 
                               f"Field '{field_name}[{i}]' must be an integer")
            elif item_type == "float" and not isinstance(item, (int, float)) or isinstance(item, bool):
                result.add_error(f"{field_name}[{i}]", 
                               f"Field '{field_name}[{i}]' must be a number")
            elif item_type == "boolean" and not isinstance(item, bool):
                result.add_error(f"{field_name}[{i}]", 
                               f"Field '{field_name}[{i}]' must be a boolean")
    
    return result


def _validate_object(field_name: str, value: Any, schema: Dict[str, Any], 
                    result: ValidationResult) -> ValidationResult:
    """Validate object field."""
    if not isinstance(value, dict):
        result.add_error(field_name, f"Field '{field_name}' must be an object")
    
    return result


def validate_item_id(item_id: str) -> ValidationResult:
    """
    Validate item ID format.
    
    Args:
        item_id: Item ID to validate
    
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, errors=[])
    
    if not isinstance(item_id, str):
        result.add_error("id", "Item ID must be a string")
        return result
    
    if not item_id.strip():
        result.add_error("id", "Item ID cannot be empty")
        return result
    
    if len(item_id) > 50:
        result.add_error("id", "Item ID must be at most 50 characters")
        return result
    
    if not re.match(r"^[a-zA-Z0-9\-_]+$", item_id):
        result.add_error("id", "Item ID can only contain letters, numbers, hyphens, and underscores")
    
    return result