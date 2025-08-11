"""
Unit tests for response handler module.
Tests response formatting and error handling.
"""

import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the shared module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from response_handler import (
    success_response,
    error_response,
    validation_error_response,
    not_found_response,
    bad_request_response,
    internal_server_error_response,
    created_response,
    no_content_response,
    parse_json_body,
    extract_path_parameter,
    handle_cors_preflight,
    format_dynamodb_error,
    log_request,
    log_response
)


class TestSuccessResponse:
    """Test success response functions."""
    
    def test_success_response_basic(self):
        """Test basic success response."""
        data = {"id": "123", "name": "Test Item"}
        response = success_response(data)
        
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in response["headers"]
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"] == data
        assert body["message"] == "Operation completed successfully"
        assert "timestamp" in body
    
    def test_success_response_custom_message(self):
        """Test success response with custom message."""
        data = {"result": "ok"}
        message = "Custom success message"
        response = success_response(data, message)
        
        body = json.loads(response["body"])
        assert body["message"] == message
    
    def test_success_response_custom_status_code(self):
        """Test success response with custom status code."""
        data = {"result": "ok"}
        response = success_response(data, status_code=202)
        
        assert response["statusCode"] == 202
    
    def test_created_response(self):
        """Test created response."""
        data = {"id": "new-item", "name": "New Item"}
        response = created_response(data)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["message"] == "Resource created successfully"
        assert body["data"] == data
    
    def test_no_content_response(self):
        """Test no content response."""
        response = no_content_response()
        
        assert response["statusCode"] == 204
        body = json.loads(response["body"])
        assert body["data"] is None
        assert body["message"] == "Operation completed successfully"


class TestErrorResponse:
    """Test error response functions."""
    
    def test_error_response_basic(self):
        """Test basic error response."""
        message = "Something went wrong"
        response = error_response(message)
        
        assert response["statusCode"] == 500
        assert response["headers"]["Content-Type"] == "application/json"
        
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["message"] == message
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert "timestamp" in body
    
    def test_error_response_custom_code_and_status(self):
        """Test error response with custom code and status."""
        message = "Custom error"
        error_code = "CUSTOM_ERROR"
        status_code = 422
        
        response = error_response(message, error_code, status_code)
        
        assert response["statusCode"] == status_code
        body = json.loads(response["body"])
        assert body["error"]["code"] == error_code
    
    def test_error_response_with_details(self):
        """Test error response with details."""
        message = "Validation failed"
        details = [
            {"field": "name", "message": "Name is required"},
            {"field": "price", "message": "Price must be positive"}
        ]
        
        response = error_response(message, details=details)
        
        body = json.loads(response["body"])
        assert body["error"]["details"] == details
    
    def test_validation_error_response(self):
        """Test validation error response."""
        errors = [
            {"field": "email", "message": "Invalid email format"},
            {"field": "age", "message": "Age must be a number"}
        ]
        
        response = validation_error_response(errors)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "Validation failed"
        assert body["error"]["details"] == errors
    
    def test_not_found_response_basic(self):
        """Test basic not found response."""
        response = not_found_response()
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["error"]["message"] == "Resource not found"
    
    def test_not_found_response_with_resource_and_id(self):
        """Test not found response with resource and ID."""
        response = not_found_response("Item", "123")
        
        body = json.loads(response["body"])
        assert body["error"]["message"] == "Item with id '123' not found"
    
    def test_bad_request_response(self):
        """Test bad request response."""
        message = "Invalid request format"
        response = bad_request_response(message)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "BAD_REQUEST"
        assert body["error"]["message"] == message
    
    def test_internal_server_error_response(self):
        """Test internal server error response."""
        response = internal_server_error_response()
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert body["error"]["message"] == "Internal server error occurred"


class TestRequestParsing:
    """Test request parsing functions."""
    
    def test_parse_json_body_success(self):
        """Test successful JSON body parsing."""
        event = {
            "body": '{"name": "Test Item", "price": 99.99}'
        }
        
        result = parse_json_body(event)
        
        assert isinstance(result, dict)
        assert result["name"] == "Test Item"
        assert result["price"] == 99.99
    
    def test_parse_json_body_empty(self):
        """Test parsing empty body."""
        event = {"body": None}
        
        result = parse_json_body(event)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "required" in body["error"]["message"]
    
    def test_parse_json_body_invalid_json(self):
        """Test parsing invalid JSON."""
        event = {
            "body": '{"name": "Test Item", "price": 99.99'  # Missing closing brace
        }
        
        result = parse_json_body(event)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid JSON format" in body["error"]["message"]
    
    def test_parse_json_body_not_object(self):
        """Test parsing JSON that's not an object."""
        event = {
            "body": '"just a string"'
        }
        
        result = parse_json_body(event)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "JSON object" in body["error"]["message"]
    
    def test_parse_json_body_base64_encoded(self):
        """Test parsing base64 encoded body."""
        import base64
        
        original_data = {"name": "Test Item", "price": 99.99}
        json_string = json.dumps(original_data)
        encoded_body = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
        
        event = {
            "body": encoded_body,
            "isBase64Encoded": True
        }
        
        result = parse_json_body(event)
        
        assert isinstance(result, dict)
        assert result["name"] == "Test Item"
        assert result["price"] == 99.99
    
    def test_extract_path_parameter_success(self):
        """Test successful path parameter extraction."""
        event = {
            "pathParameters": {
                "id": "test-item-123",
                "category": "electronics"
            }
        }
        
        result = extract_path_parameter(event, "id")
        assert result == "test-item-123"
    
    def test_extract_path_parameter_missing(self):
        """Test extracting missing path parameter."""
        event = {
            "pathParameters": {
                "category": "electronics"
            }
        }
        
        result = extract_path_parameter(event, "id")
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "required" in body["error"]["message"]
    
    def test_extract_path_parameter_no_parameters(self):
        """Test extracting parameter when no path parameters exist."""
        event = {}
        
        result = extract_path_parameter(event, "id")
        
        assert result["statusCode"] == 400
    
    def test_extract_path_parameter_whitespace(self):
        """Test extracting parameter with whitespace."""
        event = {
            "pathParameters": {
                "id": "  test-item-123  "
            }
        }
        
        result = extract_path_parameter(event, "id")
        assert result == "test-item-123"  # Should be trimmed


class TestCORSHandling:
    """Test CORS handling functions."""
    
    def test_handle_cors_preflight_options(self):
        """Test CORS preflight OPTIONS request."""
        event = {
            "httpMethod": "OPTIONS"
        }
        
        result = handle_cors_preflight(event)
        
        assert result is not None
        assert result["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in result["headers"]
        assert "Access-Control-Allow-Methods" in result["headers"]
        assert "Access-Control-Allow-Headers" in result["headers"]
        assert result["body"] == ""
    
    def test_handle_cors_preflight_not_options(self):
        """Test non-OPTIONS request."""
        event = {
            "httpMethod": "GET"
        }
        
        result = handle_cors_preflight(event)
        assert result is None


class TestDynamoDBErrorFormatting:
    """Test DynamoDB error formatting."""
    
    def test_format_dynamodb_error_not_found(self):
        """Test formatting DynamoDB not found error."""
        from dynamodb_client import DynamoDBError
        
        error = DynamoDBError("Item not found", "ITEM_NOT_FOUND")
        result = format_dynamodb_error(error)
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["error"]["code"] == "NOT_FOUND"
    
    def test_format_dynamodb_error_item_exists(self):
        """Test formatting DynamoDB item exists error."""
        from dynamodb_client import DynamoDBError
        
        error = DynamoDBError("Item already exists", "ITEM_EXISTS")
        result = format_dynamodb_error(error)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"]["code"] == "BAD_REQUEST"
    
    def test_format_dynamodb_error_generic(self):
        """Test formatting generic DynamoDB error."""
        from dynamodb_client import DynamoDBError
        
        error = DynamoDBError("Database connection failed", "CONNECTION_ERROR")
        result = format_dynamodb_error(error)
        
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    
    def test_format_non_dynamodb_error(self):
        """Test formatting non-DynamoDB error."""
        error = Exception("Generic error")
        result = format_dynamodb_error(error)
        
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Database operation failed" in body["error"]["message"]


class TestLogging:
    """Test logging functions."""
    
    @patch('response_handler.logging.getLogger')
    def test_log_request(self, mock_get_logger):
        """Test request logging."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        event = {
            "httpMethod": "POST",
            "path": "/api/v1/items",
            "pathParameters": {"id": "123"},
            "body": '{"name": "test"}'
        }
        
        context = MagicMock()
        context.aws_request_id = "test-request-id"
        
        log_request(event, context)
        
        mock_logger.setLevel.assert_called_with(20)  # logging.INFO
        mock_logger.info.assert_called_once()
        
        # Check that the log message contains expected data
        log_call_args = mock_logger.info.call_args[0][0]
        assert "POST" in log_call_args
        assert "/api/v1/items" in log_call_args
        assert "test-request-id" in log_call_args
    
    @patch('response_handler.logging.getLogger')
    def test_log_response_success(self, mock_get_logger):
        """Test response logging for success."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        response = {
            "statusCode": 200,
            "body": json.dumps({"success": True, "data": {"id": "123"}})
        }
        
        context = MagicMock()
        context.aws_request_id = "test-request-id"
        
        log_response(response, context)
        
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "200" in log_call_args
        assert "test-request-id" in log_call_args
    
    @patch('response_handler.logging.getLogger')
    def test_log_response_error(self, mock_get_logger):
        """Test response logging for error."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        response = {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": {"code": "VALIDATION_ERROR", "message": "Invalid data"}
            })
        }
        
        log_response(response)
        
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "400" in log_call_args
        assert "VALIDATION_ERROR" in log_call_args


class TestResponseHeaders:
    """Test response headers."""
    
    def test_cors_headers_in_success_response(self):
        """Test CORS headers are included in success responses."""
        response = success_response({"test": "data"})
        
        headers = response["headers"]
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "GET,POST,PUT,DELETE,OPTIONS" in headers["Access-Control-Allow-Methods"]
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
    
    def test_cors_headers_in_error_response(self):
        """Test CORS headers are included in error responses."""
        response = error_response("Test error")
        
        headers = response["headers"]
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "GET,POST,PUT,DELETE,OPTIONS" in headers["Access-Control-Allow-Methods"]
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]


class TestJSONSerialization:
    """Test JSON serialization edge cases."""
    
    def test_datetime_serialization(self):
        """Test datetime serialization in responses."""
        from datetime import datetime
        
        data = {
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "name": "Test Item"
        }
        
        response = success_response(data)
        
        # Should not raise an exception
        body = json.loads(response["body"])
        assert "created_at" in body["data"]
        assert body["data"]["name"] == "Test Item"
    
    def test_none_values_serialization(self):
        """Test None values serialization."""
        data = {
            "name": "Test Item",
            "description": None,
            "tags": None
        }
        
        response = success_response(data)
        
        body = json.loads(response["body"])
        assert body["data"]["description"] is None
        assert body["data"]["tags"] is None


if __name__ == "__main__":
    pytest.main([__file__])