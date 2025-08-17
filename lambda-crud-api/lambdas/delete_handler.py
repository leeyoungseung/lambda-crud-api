"""
Lambda handler for deleting items.
Handles DELETE requests to remove items from DynamoDB.
"""

import json
import sys
import os
from typing import Dict, Any

# Add shared modules to path

from shared.validation import validate_item_id
from shared.dynamodb_client import delete_item, get_item, DynamoDBError
from shared.response_handler import (
    success_response,
    not_found_response,
    extract_path_parameter,
    handle_cors_preflight,
    format_dynamodb_error,
    log_request,
    log_response,
    internal_server_error_response,
    bad_request_response,
    no_content_response
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for deleting items.
    
    Handles DELETE /items/{id} requests to remove items from DynamoDB.
    
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
        
        # Check if item exists before attempting deletion
        try:
            existing_item = get_item(item_id)
            if existing_item is None:
                response = not_found_response("Item", item_id)
                log_response(response, context)
                return response
        except DynamoDBError as e:
            response = format_dynamodb_error(e)
            log_response(response, context)
            return response
        
        # Delete item from DynamoDB
        try:
            deletion_successful = delete_item(item_id)
            
            if deletion_successful:
                response = success_response(
                    {
                        "id": item_id,
                        "deleted": True,
                        "deleted_item": existing_item
                    },
                    f"Item '{item_id}' deleted successfully"
                )
            else:
                # This shouldn't happen since we checked existence above,
                # but handle it gracefully
                response = not_found_response("Item", item_id)
            
            log_response(response, context)
            return response
            
        except DynamoDBError as e:
            response = format_dynamodb_error(e)
            log_response(response, context)
            return response
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error during item deletion: {str(e)}"
        response = internal_server_error_response(error_message)
        log_response(response, context)
        return response


def validate_delete_request(item_id: str) -> Dict[str, Any]:
    """
    Validate delete request parameters.
    
    Args:
        item_id: ID of item to delete
        
    Returns:
        Error response if validation fails, None if valid
    """
    # Validate item ID format
    id_validation_result = validate_item_id(item_id)
    if not id_validation_result.is_valid:
        return bad_request_response(
            "Invalid item ID format",
            details=id_validation_result.errors
        )
    
    return None


def check_item_exists_for_deletion(item_id: str) -> tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Check if an item exists before deletion and return the item data.
    
    Args:
        item_id: ID of item to check
        
    Returns:
        Tuple of (exists, item_data, error_response)
        - exists: True if item exists, False otherwise
        - item_data: Item data if exists, None otherwise
        - error_response: Error response if check failed, None otherwise
    """
    try:
        item = get_item(item_id)
        if item is None:
            return False, None, not_found_response("Item", item_id)
        return True, item, None
        
    except DynamoDBError as e:
        return False, None, format_dynamodb_error(e)
    except Exception as e:
        return False, None, internal_server_error_response(
            f"Error checking item existence: {str(e)}"
        )


def perform_item_deletion(item_id: str) -> tuple[bool, Dict[str, Any]]:
    """
    Perform the actual item deletion.
    
    Args:
        item_id: ID of item to delete
        
    Returns:
        Tuple of (success, error_response)
        - success: True if deletion successful, False otherwise
        - error_response: Error response if deletion failed, None if successful
    """
    try:
        deletion_successful = delete_item(item_id)
        return deletion_successful, None
        
    except DynamoDBError as e:
        return False, format_dynamodb_error(e)
    except Exception as e:
        return False, internal_server_error_response(
            f"Error deleting item: {str(e)}"
        )


def create_deletion_response(item_id: str, deleted_item: Dict[str, Any], 
                           include_deleted_item: bool = True) -> Dict[str, Any]:
    """
    Create a standardized deletion success response.
    
    Args:
        item_id: ID of deleted item
        deleted_item: Data of the deleted item
        include_deleted_item: Whether to include deleted item data in response
        
    Returns:
        Formatted success response
    """
    response_data = {
        "id": item_id,
        "deleted": True
    }
    
    if include_deleted_item and deleted_item:
        response_data["deleted_item"] = deleted_item
    
    return success_response(
        response_data,
        f"Item '{item_id}' deleted successfully"
    )


def handle_soft_delete(item_id: str, soft_delete: bool = False) -> Dict[str, Any]:
    """
    Handle soft delete functionality (future enhancement).
    
    This is a placeholder for soft delete functionality where items
    are marked as deleted rather than physically removed.
    
    Args:
        item_id: ID of item to soft delete
        soft_delete: Whether to perform soft delete
        
    Returns:
        Response indicating soft delete status
    """
    if not soft_delete:
        return None
    
    # Future implementation could:
    # 1. Update item with is_deleted=True flag
    # 2. Add deleted_at timestamp
    # 3. Keep item in database for audit purposes
    
    # For now, return not implemented
    return bad_request_response(
        "Soft delete functionality not yet implemented"
    )


def validate_deletion_permissions(item_id: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Validate user permissions for deletion (future enhancement).
    
    This is a placeholder for permission validation where certain users
    might not have permission to delete certain items.
    
    Args:
        item_id: ID of item to delete
        user_context: User context for permission checking
        
    Returns:
        Error response if permission denied, None if allowed
    """
    # Future implementation could:
    # 1. Check user roles and permissions
    # 2. Validate item ownership
    # 3. Check business rules for deletion
    
    # For now, allow all deletions
    return None


def log_deletion_audit(item_id: str, deleted_item: Dict[str, Any], 
                      user_context: Dict[str, Any] = None) -> None:
    """
    Log deletion for audit purposes (future enhancement).
    
    Args:
        item_id: ID of deleted item
        deleted_item: Data of deleted item
        user_context: User context for audit logging
    """
    import logging
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    audit_data = {
        "action": "DELETE",
        "item_id": item_id,
        "item_name": deleted_item.get("name", "Unknown") if deleted_item else "Unknown",
        "user_id": user_context.get("user_id", "Unknown") if user_context else "System",
        "timestamp": deleted_item.get("updated_at") if deleted_item else None
    }
    
    logger.info(f"AUDIT: Item deletion - {json.dumps(audit_data)}")


# For testing purposes, expose internal functions
__all__ = [
    'lambda_handler',
    'validate_delete_request',
    'check_item_exists_for_deletion',
    'perform_item_deletion',
    'create_deletion_response',
    'handle_soft_delete',
    'validate_deletion_permissions',
    'log_deletion_audit'
]