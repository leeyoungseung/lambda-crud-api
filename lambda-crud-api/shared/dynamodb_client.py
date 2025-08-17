"""
DynamoDB client module for Lambda CRUD API.
Handles all DynamoDB operations with comprehensive error handling.
"""

import boto3
import os
import json
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from decimal import Decimal


class DynamoDBError(Exception):
    """Custom exception for DynamoDB operations."""
    def __init__(self, message: str, error_code: str = "DYNAMODB_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class DynamoDBClient:
    """DynamoDB client for CRUD operations."""
    
    def __init__(self, table_name: str = None, region_name: str = None):
        """
        Initialize DynamoDB client.
        
        Args:
            table_name: DynamoDB table name (defaults to environment variable)
            region_name: AWS region (defaults to environment variable)
        """
        self.table_name = table_name or os.environ.get('DYNAMODB_TABLE_NAME', 'crud-api-items')
        self.region_name = region_name or os.environ.get('REGION', 'ap-northeast-1')
        
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
            self.table = self.dynamodb.Table(self.table_name)
        except Exception as e:
            raise DynamoDBError(f"Failed to initialize DynamoDB client: {str(e)}", "INIT_ERROR")
    
    def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item in DynamoDB.
        
        Args:
            item_data: Item data to create
            
        Returns:
            Created item data
            
        Raises:
            DynamoDBError: If creation fails
        """
        try:
            # Convert float values to Decimal for DynamoDB
            item_data = self._convert_floats_to_decimal(item_data)
            
            # Check if item already exists
            if self._item_exists(item_data['id']):
                raise DynamoDBError(f"Item with id '{item_data['id']}' already exists", "ITEM_EXISTS")
            
            # Put item in DynamoDB
            response = self.table.put_item(Item=item_data)
            
            # Convert back to regular Python types for response
            return self._convert_decimal_to_float(item_data)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise DynamoDBError(f"Failed to create item: {error_message}", error_code)
        except DynamoDBError:
            raise
        except Exception as e:
            raise DynamoDBError(f"Unexpected error creating item: {str(e)}", "CREATE_ERROR")
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single item by ID.
        
        Args:
            item_id: ID of item to retrieve
            
        Returns:
            Item data if found, None if not found
            
        Raises:
            DynamoDBError: If retrieval fails
        """
        try:
            response = self.table.get_item(Key={'id': item_id})
            
            if 'Item' not in response:
                return None
            
            # Convert Decimal values back to float
            return self._convert_decimal_to_float(response['Item'])
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise DynamoDBError(f"Failed to get item: {error_message}", error_code)
        except Exception as e:
            raise DynamoDBError(f"Unexpected error getting item: {str(e)}", "GET_ERROR")
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Get all items from the table.
        
        Returns:
            List of all items
            
        Raises:
            DynamoDBError: If retrieval fails
        """
        try:
            items = []
            
            # Use scan to get all items (paginated)
            response = self.table.scan()
            items.extend(response.get('Items', []))
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))
            
            # Convert Decimal values back to float
            return [self._convert_decimal_to_float(item) for item in items]
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise DynamoDBError(f"Failed to get all items: {error_message}", error_code)
        except Exception as e:
            raise DynamoDBError(f"Unexpected error getting all items: {str(e)}", "SCAN_ERROR")
    
    def _item_exists(self, item_id: str) -> bool:
        """
        Check if an item exists.
        
        Args:
            item_id: ID of item to check
            
        Returns:
            True if item exists, False otherwise
        """
        try:
            response = self.table.get_item(Key={'id': item_id})
            return 'Item' in response
        except Exception:
            return False
    
    def _convert_floats_to_decimal(self, data: Any) -> Any:
        """
        Convert float values to Decimal for DynamoDB storage.
        
        Args:
            data: Data to convert
            
        Returns:
            Data with floats converted to Decimal
        """
        if isinstance(data, dict):
            return {key: self._convert_floats_to_decimal(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_floats_to_decimal(item) for item in data]
        elif isinstance(data, float):
            return Decimal(str(data))
        else:
            return data
    
    def update_item(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing item in DynamoDB.
        
        Args:
            item_id: ID of item to update
            item_data: Updated item data
            
        Returns:
            Updated item data
            
        Raises:
            DynamoDBError: If update fails or item doesn't exist
        """
        try:
            # Check if item exists
            existing_item = self.get_item(item_id)
            if existing_item is None:
                raise DynamoDBError(f"Item with id '{item_id}' not found", "ITEM_NOT_FOUND")
            
            # Merge existing item with updates
            updated_item = existing_item.copy()
            updated_item.update(item_data)
            updated_item['id'] = item_id  # Ensure ID doesn't change
            
            # Convert float values to Decimal for DynamoDB
            updated_item = self._convert_floats_to_decimal(updated_item)
            
            # Build update expression dynamically
            update_expression = "SET "
            expression_attribute_names = {}
            expression_attribute_values = {}
            
            update_parts = []
            for key, value in updated_item.items():
                if key != 'id':  # Don't update the primary key
                    attr_name = f"#{key}"
                    attr_value = f":{key}"
                    update_parts.append(f"{attr_name} = {attr_value}")
                    expression_attribute_names[attr_name] = key
                    expression_attribute_values[attr_value] = value
            
            update_expression += ", ".join(update_parts)
            
            # Perform conditional update
            response = self.table.update_item(
                Key={'id': item_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression="attribute_exists(id)",
                ReturnValues="ALL_NEW"
            )
            
            # Convert back to regular Python types for response
            return self._convert_decimal_to_float(response['Attributes'])
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ConditionalCheckFailedException':
                raise DynamoDBError(f"Item with id '{item_id}' not found", "ITEM_NOT_FOUND")
            else:
                raise DynamoDBError(f"Failed to update item: {error_message}", error_code)
        except DynamoDBError:
            raise
        except Exception as e:
            raise DynamoDBError(f"Unexpected error updating item: {str(e)}", "UPDATE_ERROR")
    
    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item from DynamoDB.
        
        Args:
            item_id: ID of item to delete
            
        Returns:
            True if item was deleted, False if item didn't exist
            
        Raises:
            DynamoDBError: If deletion fails
        """
        try:
            # Check if item exists first
            if not self._item_exists(item_id):
                return False
            
            # Delete the item
            response = self.table.delete_item(
                Key={'id': item_id},
                ConditionExpression="attribute_exists(id)",
                ReturnValues="ALL_OLD"
            )
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ConditionalCheckFailedException':
                return False
            else:
                raise DynamoDBError(f"Failed to delete item: {error_message}", error_code)
        except Exception as e:
            raise DynamoDBError(f"Unexpected error deleting item: {str(e)}", "DELETE_ERROR")

    def _convert_decimal_to_float(self, data: Any) -> Any:
        """
        Convert Decimal values back to float for JSON serialization.
        
        Args:
            data: Data to convert
            
        Returns:
            Data with Decimals converted to float
        """
        if isinstance(data, dict):
            return {key: self._convert_decimal_to_float(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimal_to_float(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        else:
            return data


# Global client instance (initialized once per Lambda container)
_dynamodb_client = None


def get_dynamodb_client() -> DynamoDBClient:
    """
    Get singleton DynamoDB client instance.
    
    Returns:
        DynamoDB client instance
    """
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = DynamoDBClient()
    return _dynamodb_client


def create_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new item in DynamoDB.
    
    Args:
        item_data: Item data to create
        
    Returns:
        Created item data
    """
    client = get_dynamodb_client()
    return client.create_item(item_data)


def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single item by ID.
    
    Args:
        item_id: ID of item to retrieve
        
    Returns:
        Item data if found, None if not found
    """
    client = get_dynamodb_client()
    return client.get_item(item_id)


def get_all_items() -> List[Dict[str, Any]]:
    """
    Get all items from the table.
    
    Returns:
        List of all items
    """
    client = get_dynamodb_client()
    return client.get_all_items()


def update_item(item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing item in DynamoDB.
    
    Args:
        item_id: ID of item to update
        item_data: Updated item data
        
    Returns:
        Updated item data
    """
    client = get_dynamodb_client()
    return client.update_item(item_id, item_data)


def delete_item(item_id: str) -> bool:
    """
    Delete an item from DynamoDB.
    
    Args:
        item_id: ID of item to delete
        
    Returns:
        True if item was deleted, False if item didn't exist
    """
    client = get_dynamodb_client()
    return client.delete_item(item_id)