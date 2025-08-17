"""
Lambda handler for updating items.
Handles PUT requests to update existing items in DynamoDB.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add shared modules to path

from shared.validation import validate_item_data, validate_item_id, ITEM_SCHEMA
from shared.dynamodb_client import update_item, get_item, DynamoDBError
from shared.response_handler import (
    success_response,
    validation_error_response,
    not_found_response,
    parse_json_body,
    extract_path_parameter,
    handle_cors_preflight,
    format_dynamodb_error,
    log_request,
    log_response,
    internal_server_error_response,
    bad_request_response
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for updating items.
    
    Handles PUT /items/{id} requests to update existing items.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Lambda response object
    """
    try:
        # Log incoming request
        log_request(event, context)
        
        # Handle CORS preflight
        cors_response = handle_cors_preflight(event)
        if cors_response:
            return cors_response
        
        # Extract item ID from path parameters
        item_id = extract_path_parameter(event, "id")
        if isinstance(item_id, dict) and "statusCode" in item_id:
            # extract_path_parameter returned an error response
            log_response(item_id, context)
            return item_id
        
        # Validate item ID format
        id_validation_result = validate_item_id(item_id)
        if not id_validation_result.is_valid:
            response = bad_request_response(
                "Invalid item ID format",
                details=id_validation_result.errors
            )
            log_response(response, context)
            return response
        
        # Parse JSON body
        update_data = parse_json_body(event)
        if isinstance(update_data, dict) and "statusCode" in update_data:
            # parse_json_body returned an error response
            log_response(update_data, context)
            return update_data
        
        # Prepare update data
        prepared_data = prepare_update_data(update_data, item_id)
        
        # Validate update data (in update mode, required fields are optional)
        validation_result = validate_item_data(prepared_data, ITEM_SCHEMA, is_update=True)
        if not validation_result.is_valid:
            response = validation_error_response(validation_result.errors)
            log_response(response, context)
            return response
        
        # Update item in DynamoDB
        try:
            updated_item = update_item(item_id, prepared_data)
            response = success_response(
                updated_item,
                f"Item '{item_id}' updated successfully"
            )
            log_response(response, context)
            return response
            
        except DynamoDBError as e:
            response = format_dynamodb_error(e)
            log_response(response, context)
            return response
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error during item update: {str(e)}"
        response = internal_server_error_response(error_message)
        log_response(response, context)
        return response


def prepare_update_data(update_data: Dict[str, Any], item_id: str) -> Dict[str, Any]:
    """
    Prepare update data by adding/updating timestamps and ensuring ID consistency.
    
    Args:
        update_data: Raw update data from request
        item_id: ID of item being updated
        
    Returns:
        Prepared update data
    """
    prepared_data = update_data.copy()
    
    # Ensure ID cannot be changed
    if "id" in prepared_data:
        del prepared_data["id"]
    
    # Don't allow changing created_at timestamp
    if "created_at" in prepared_data:
        del prepared_data["created_at"]
    
    # Update the updated_at timestamp
    prepared_data["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    return prepared_data


def validate_update_data(update_data: Dict[str, Any], item_id: str) -> Dict[str, Any]:
    """
    Validate data specifically for update operations.
    
    Args:
        update_data: Data to validate
        item_id: ID of item being updated
        
    Returns:
        Validation error response or None if valid
    """
    # Check if update data is empty
    if not update_data or len(update_data) == 0:
        return bad_request_response("Update data cannot be empty")
    
    # Remove system fields that shouldn't be updated directly
    filtered_data = {
        key: value for key, value in update_data.items()
        if key not in ["id", "created_at"]
    }
    
    if not filtered_data:
        return bad_request_response(
            "No valid fields to update. Cannot update 'id' or 'created_at' fields."
        )
    
    # Validate the filtered data
    validation_result = validate_item_data(filtered_data, ITEM_SCHEMA, is_update=True)
    
    if not validation_result.is_valid:
        return validation_error_response(validation_result.errors)
    
    return None


def check_item_exists(item_id: str) -> bool:
    """
    Check if an item exists before attempting to update it.
    
    Args:
        item_id: ID of item to check
        
    Returns:
        True if item exists, False otherwise
    """
    try:
        item = get_item(item_id)
        return item is not None
    except DynamoDBError:
        return False


def merge_update_data(existing_item: Dict[str, Any], update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge update data with existing item data.
    
    Args:
        existing_item: Current item data
        update_data: New data to merge
        
    Returns:
        Merged item data
    """
    merged_data = existing_item.copy()
    
    # Update with new data
    for key, value in update_data.items():
        if key not in ["id", "created_at"]:  # Protect system fields
            merged_data[key] = value
    
    # Always update the timestamp
    merged_data["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    return merged_data


def validate_partial_update(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate partial update data to ensure at least one valid field is being updated.
    
    Args:
        update_data: Update data to validate
        
    Returns:
        Error response if validation fails, None if valid
    """
    if not update_data:
        return bad_request_response("Update data is required")
    
    # Check if there are any updatable fields
    updatable_fields = {
        key: value for key, value in update_data.items()
        if key not in ["id", "created_at"]
    }
    
    if not updatable_fields:
        return bad_request_response(
            "No updatable fields provided. Cannot update 'id' or 'created_at'."
        )
    
    # Check for null values in required fields (if they're being updated)
    required_fields = [
        field for field, schema in ITEM_SCHEMA.items()
        if schema.get("required", False)
    ]
    
    null_required_fields = [
        field for field in required_fields
        if field in updatable_fields and updatable_fields[field] is None
    ]
    
    if null_required_fields:
        errors = [
            {"field": field, "message": f"Required field '{field}' cannot be set to null"}
            for field in null_required_fields
        ]
        return validation_error_response(errors)
    
    return None


# For testing purposes, expose internal functions
__all__ = [
    'lambda_handler',
    'prepare_update_data',
    'validate_update_data',
    'check_item_exists',
    'merge_update_data',
    'validate_partial_update'
]