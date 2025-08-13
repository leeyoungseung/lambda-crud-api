"""
Response handler module for Lambda CRUD API.
Provides standardized response formatting and error handling.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union


def success_response(data: Any, message: str = "Operation completed successfully", 
                    status_code: int = 200) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Formatted Lambda response
    """
    response_body = {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(response_body, default=str)
    }


def error_response(message: str, error_code: str = "INTERNAL_ERROR", 
                  status_code: int = 500, details: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_code: Error code identifier
        status_code: HTTP status code
        details: Optional error details
        
    Returns:
        Formatted Lambda error response
    """
    error_data = {
        "code": error_code,
        "message": message
    }
    
    if details:
        error_data["details"] = details
    
    response_body = {
        "success": False,
        "error": error_data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(response_body, default=str)
    }


def validation_error_response(errors: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Create a standardized validation error response.
    
    Args:
        errors: List of validation errors
        
    Returns:
        Formatted Lambda validation error response
    """
    return error_response(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        status_code=400,
        details=errors
    )


def not_found_response(resource: str = "Resource", resource_id: str = "") -> Dict[str, Any]:
    """
    Create a standardized not found error response.
    
    Args:
        resource: Name of the resource that wasn't found
        resource_id: ID of the resource that wasn't found
        
    Returns:
        Formatted Lambda not found response
    """
    if resource_id:
        message = f"{resource} with id '{resource_id}' not found"
    else:
        message = f"{resource} not found"
    
    return error_response(
        message=message,
        error_code="NOT_FOUND",
        status_code=404
    )


def bad_request_response(message: str, details: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Create a standardized bad request error response.
    
    Args:
        message: Error message
        details: Optional error details
        
    Returns:
        Formatted Lambda bad request response
    """
    return error_response(
        message=message,
        error_code="BAD_REQUEST",
        status_code=400,
        details=details
    )


def internal_server_error_response(message: str = "Internal server error occurred") -> Dict[str, Any]:
    """
    Create a standardized internal server error response.
    
    Args:
        message: Error message
        
    Returns:
        Formatted Lambda internal server error response
    """
    return error_response(
        message=message,
        error_code="INTERNAL_SERVER_ERROR",
        status_code=500
    )


def created_response(data: Any, message: str = "Resource created successfully") -> Dict[str, Any]:
    """
    Create a standardized created response.
    
    Args:
        data: Created resource data
        message: Success message
        
    Returns:
        Formatted Lambda created response
    """
    return success_response(data, message, 201)


def no_content_response(message: str = "Operation completed successfully") -> Dict[str, Any]:
    """
    Create a standardized no content response.
    
    Args:
        message: Success message
        
    Returns:
        Formatted Lambda no content response
    """
    return success_response(None, message, 204)


def parse_json_body(event: Dict[str, Any]) -> Union[Dict[str, Any], Dict[str, Any]]:
    """
    Parse JSON body from Lambda event.
    
    Args:
        event: Lambda event object
        
    Returns:
        Parsed JSON data or error response
    """
    try:
        if not event.get("body"):
            return bad_request_response("Request body is required")
        
        # Handle base64 encoded body (from API Gateway)
        body = event["body"]
        if event.get("isBase64Encoded", False):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        data = json.loads(body)
        
        if not isinstance(data, dict):
            return bad_request_response("Request body must be a JSON object")
        
        return data
        
    except json.JSONDecodeError as e:
        return bad_request_response(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        return bad_request_response(f"Failed to parse request body: {str(e)}")


def extract_path_parameter(event: Dict[str, Any], parameter_name: str) -> Union[str, Dict[str, Any]]:
    """
    Extract path parameter from Lambda event.
    
    Args:
        event: Lambda event object
        parameter_name: Name of the path parameter
        
    Returns:
        Parameter value or error response
    """
    try:
        path_parameters = event.get("pathParameters") or {}
        parameter_value = path_parameters.get(parameter_name)
        
        if not parameter_value:
            return bad_request_response(f"Path parameter '{parameter_name}' is required")
        
        return parameter_value.strip()
        
    except Exception as e:
        return bad_request_response(f"Failed to extract path parameter: {str(e)}")


def handle_cors_preflight(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle CORS preflight OPTIONS request.
    
    Args:
        event: Lambda event object
        
    Returns:
        CORS response if it's a preflight request, None otherwise
    """
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                "Access-Control-Max-Age": "86400"
            },
            "body": ""
        }
    return None


def format_dynamodb_error(error) -> Dict[str, Any]:
    """
    Format DynamoDB error into standardized response.
    
    Args:
        error: DynamoDB error object
        
    Returns:
        Formatted error response
    """
    from dynamodb_client import DynamoDBError
    
    if isinstance(error, DynamoDBError):
        if error.error_code == "ITEM_NOT_FOUND":
            return not_found_response("Item", "")
        elif error.error_code == "ITEM_EXISTS":
            return bad_request_response(error.message)
        else:
            return internal_server_error_response(error.message)
    else:
        return internal_server_error_response(f"Database operation failed: {str(error)}")


def log_request(event: Dict[str, Any], context: Any = None) -> None:
    """
    Log incoming request for debugging.
    
    Args:
        event: Lambda event object
        context: Lambda context object
    """
    import logging
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    log_data = {
        "httpMethod": event.get("httpMethod"),
        "path": event.get("path"),
        "pathParameters": event.get("pathParameters"),
        "queryStringParameters": event.get("queryStringParameters"),
        "requestId": str(context.aws_request_id) if context and hasattr(context, 'aws_request_id') else None
    }
    
    # Don't log the body content for security reasons
    if event.get("body"):
        log_data["hasBody"] = True
    
    logger.info(f"Request: {json.dumps(log_data)}")


def log_response(response: Dict[str, Any], context: Any = None) -> None:
    """
    Log outgoing response for debugging.
    
    Args:
        response: Lambda response object
        context: Lambda context object
    """
    import logging
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    log_data = {
        "statusCode": response.get("statusCode"),
        "requestId": str(context.aws_request_id) if context and hasattr(context, 'aws_request_id') else None
    }
    
    # Parse response body to check if it's an error
    try:
        body = json.loads(response.get("body", "{}"))
        log_data["success"] = body.get("success", True)
        if not body.get("success", True):
            log_data["errorCode"] = body.get("error", {}).get("code")
    except:
        pass
    
    logger.info(f"Response: {json.dumps(log_data)}")