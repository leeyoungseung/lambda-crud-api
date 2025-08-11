"""
Lambda handler for reading items.
Handles GET requests to retrieve single items or all items from DynamoDB.
"""

import json
import sys
import os
from typing import Dict, Any, Optional

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from validation import validate_item_id
from dynamodb_client import get_item, get_all_items, DynamoDBError
from response_handler import (
    success_response,
    not_found_response,
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
    Lambda handler for reading items.
    
    Supports two operations:
    - GET /items/{id} - Get single item by ID
    - GET /items - Get all items
    
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
        
        # Determine if this is a single item request or get all items request
        path_parameters = event.get("pathParameters")
        
        if path_parameters and path_parameters.get("id"):
            # Single item request
            response = handle_get_single_item(event, context)
        else:
            # Get all items request
            response = handle_get_all_items(event, context)
        
        log_response(response, context)
        return response
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error during item retrieval: {str(e)}"
        response = internal_server_error_response(error_message)
        log_response(response, context)
        return response


def handle_get_single_item(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET request for a single item by ID.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Lambda response object
    """
    try:
        # Extract item ID from path parameters
        item_id = extract_path_parameter(event, "id")
        if isinstance(item_id, dict) and "statusCode" in item_id:
            # extract_path_parameter returned an error response
            return item_id
        
        # Validate item ID format
        validation_result = validate_item_id(item_id)
        if not validation_result.is_valid:
            return bad_request_response(
                "Invalid item ID format",
                details=validation_result.errors
            )
        
        # Get item from DynamoDB
        try:
            item = get_item(item_id)
            
            if item is None:
                return not_found_response("Item", item_id)
            
            return success_response(
                item,
                f"Item '{item_id}' retrieved successfully"
            )
            
        except DynamoDBError as e:
            return format_dynamodb_error(e)
        
    except Exception as e:
        return internal_server_error_response(
            f"Error retrieving item: {str(e)}"
        )


def handle_get_all_items(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET request for all items.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Lambda response object
    """
    try:
        # Parse query parameters for filtering/pagination (future enhancement)
        query_params = event.get("queryStringParameters") or {}
        
        # Get all items from DynamoDB
        try:
            items = get_all_items()
            
            # Apply any query parameter filters here (future enhancement)
            filtered_items = apply_query_filters(items, query_params)
            
            return success_response(
                {
                    "items": filtered_items,
                    "count": len(filtered_items),
                    "total": len(items)
                },
                f"Retrieved {len(filtered_items)} items successfully"
            )
            
        except DynamoDBError as e:
            return format_dynamodb_error(e)
        
    except Exception as e:
        return internal_server_error_response(
            f"Error retrieving items: {str(e)}"
        )


def apply_query_filters(items: list, query_params: Dict[str, str]) -> list:
    """
    Apply query parameter filters to items list.
    
    This is a placeholder for future filtering functionality.
    Currently returns all items unchanged.
    
    Args:
        items: List of items to filter
        query_params: Query parameters from request
        
    Returns:
        Filtered list of items
    """
    # Future enhancements could include:
    # - Filtering by is_active status
    # - Filtering by price range
    # - Filtering by tags
    # - Pagination with limit/offset
    # - Sorting by different fields
    
    filtered_items = items.copy()
    
    # Example filter by is_active (if provided)
    if "is_active" in query_params:
        is_active_filter = query_params["is_active"].lower() == "true"
        filtered_items = [
            item for item in filtered_items 
            if item.get("is_active") == is_active_filter
        ]
    
    # Example filter by minimum price (if provided)
    if "min_price" in query_params:
        try:
            min_price = float(query_params["min_price"])
            filtered_items = [
                item for item in filtered_items 
                if item.get("price", 0) >= min_price
            ]
        except ValueError:
            # Invalid min_price parameter, ignore filter
            pass
    
    # Example filter by maximum price (if provided)
    if "max_price" in query_params:
        try:
            max_price = float(query_params["max_price"])
            filtered_items = [
                item for item in filtered_items 
                if item.get("price", float('inf')) <= max_price
            ]
        except ValueError:
            # Invalid max_price parameter, ignore filter
            pass
    
    # Example filter by tag (if provided)
    if "tag" in query_params:
        tag_filter = query_params["tag"]
        filtered_items = [
            item for item in filtered_items 
            if tag_filter in item.get("tags", [])
        ]
    
    return filtered_items


def validate_query_parameters(query_params: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Validate query parameters.
    
    Args:
        query_params: Query parameters to validate
        
    Returns:
        Error response if validation fails, None if valid
    """
    errors = []
    
    # Validate is_active parameter
    if "is_active" in query_params:
        is_active_value = query_params["is_active"].lower()
        if is_active_value not in ["true", "false"]:
            errors.append({
                "field": "is_active",
                "message": "is_active parameter must be 'true' or 'false'"
            })
    
    # Validate price range parameters
    if "min_price" in query_params:
        try:
            min_price = float(query_params["min_price"])
            if min_price < 0:
                errors.append({
                    "field": "min_price",
                    "message": "min_price must be non-negative"
                })
        except ValueError:
            errors.append({
                "field": "min_price",
                "message": "min_price must be a valid number"
            })
    
    if "max_price" in query_params:
        try:
            max_price = float(query_params["max_price"])
            if max_price < 0:
                errors.append({
                    "field": "max_price",
                    "message": "max_price must be non-negative"
                })
        except ValueError:
            errors.append({
                "field": "max_price",
                "message": "max_price must be a valid number"
            })
    
    # Validate price range consistency
    if "min_price" in query_params and "max_price" in query_params:
        try:
            min_price = float(query_params["min_price"])
            max_price = float(query_params["max_price"])
            if min_price > max_price:
                errors.append({
                    "field": "price_range",
                    "message": "min_price cannot be greater than max_price"
                })
        except ValueError:
            # Already handled above
            pass
    
    if errors:
        return bad_request_response(
            "Invalid query parameters",
            details=errors
        )
    
    return None


# For testing purposes, expose internal functions
__all__ = [
    'lambda_handler',
    'handle_get_single_item',
    'handle_get_all_items',
    'apply_query_filters',
    'validate_query_parameters'
]