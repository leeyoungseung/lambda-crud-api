"""
Lambda handler for creating items.
Handles POST requests to create new items in DynamoDB.
"""

import json
import uuid
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from validation import validate_item_data, ITEM_SCHEMA
from dynamodb_client import create_item, DynamoDBError
from response_handler import (
    created_response,
    validation_error_response,
    parse_json_body,
    handle_cors_preflight,
    format_dynamodb_error,
    log_request,
    log_response,
    internal_server_error_response
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for creating items.
    
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
        
        # Parse JSON body
        data = parse_json_body(event)
        if isinstance(data, dict) and "statusCode" in data:
            # parse_json_body returned an error response
            log_response(data, context)
            return data
        
        # Generate ID and timestamps if not provided
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())
        
        current_time = datetime.utcnow().isoformat() + "Z"
        data["created_at"] = current_time
        data["updated_at"] = current_time
        
        # Validate item data
        validation_result = validate_item_data(data, ITEM_SCHEMA, is_update=False)
        if not validation_result.is_valid:
            response = validation_error_response(validation_result.errors)
            log_response(response, context)
            return response
        
        # Create item in DynamoDB
        try:
            created_item = create_item(data)
            response = created_response(
                created_item, 
                f"Item '{created_item['id']}' created successfully"
            )
            log_response(response, context)
            return response
            
        except DynamoDBError as e:
            response = format_dynamodb_error(e)
            log_response(response, context)
            return response
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error during item creation: {str(e)}"
        response = internal_server_error_response(error_message)
        log_response(response, context)
        return response


def validate_create_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate data specifically for create operations.
    
    Args:
        data: Data to validate
        
    Returns:
        Validation result or None if valid
    """
    # Additional create-specific validations can be added here
    # For now, we use the standard validation
    validation_result = validate_item_data(data, ITEM_SCHEMA, is_update=False)
    
    if not validation_result.is_valid:
        return validation_error_response(validation_result.errors)
    
    return None


def prepare_item_for_creation(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare item data for creation by adding required fields.
    
    Args:
        data: Raw item data
        
    Returns:
        Prepared item data
    """
    prepared_data = data.copy()
    
    # Generate ID if not provided
    if "id" not in prepared_data or not prepared_data["id"]:
        prepared_data["id"] = str(uuid.uuid4())
    
    # Add timestamps
    current_time = datetime.utcnow().isoformat() + "Z"
    prepared_data["created_at"] = current_time
    prepared_data["updated_at"] = current_time
    
    return prepared_data


# For testing purposes, expose internal functions
__all__ = [
    'lambda_handler',
    'validate_create_data',
    'prepare_item_for_creation'
]