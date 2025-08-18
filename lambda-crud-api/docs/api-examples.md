# API Usage Examples

This document provides comprehensive examples of how to use the Lambda CRUD API.

## Base URL

Replace `{api-gateway-url}` with your actual API Gateway URL from the Terraform outputs:

```
https://{api-id}.execute-api.{region}.amazonaws.com/{environment}
```

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Content Type

All requests that send data must include the `Content-Type: application/json` header.

## Response Format

All responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": [
      {
        "field": "field_name",
        "message": "Specific field error"
      }
    ]
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## API Endpoints

### 1. Create Item

**Endpoint:** `POST /items`

**Description:** Creates a new item with auto-generated ID and timestamps.

**Request Body:**
```json
{
  "name": "Wireless Headphones",
  "description": "High-quality wireless headphones with noise cancellation",
  "price": 199.99,
  "quantity": 50,
  "is_active": true,
  "tags": ["electronics", "audio", "wireless"],
  "metadata": {
    "category": "electronics",
    "brand": "TechCorp",
    "weight": 0.3,
    "dimensions": {
      "length": 20,
      "width": 18,
      "height": 8
    },
    "features": ["noise-cancellation", "bluetooth-5.0", "30h-battery"]
  }
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 199.99,
    "quantity": 50,
    "is_active": true,
    "tags": ["electronics", "audio", "wireless"],
    "metadata": {
      "category": "electronics",
      "brand": "TechCorp",
      "weight": 0.3,
      "dimensions": {
        "length": 20,
        "width": 18,
        "height": 8
      },
      "features": ["noise-cancellation", "bluetooth-5.0", "30h-battery"]
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "Item created successfully"
}
```

**cURL Example:**
```bash
curl -X POST "https://your-api-gateway-url/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 199.99,
    "quantity": 50,
    "is_active": true,
    "tags": ["electronics", "audio", "wireless"],
    "metadata": {
      "category": "electronics",
      "brand": "TechCorp",
      "weight": 0.3,
      "dimensions": {
        "length": 20,
        "width": 18,
        "height": 8
      }
    }
  }'
```

### 2. Get All Items

**Endpoint:** `GET /items`

**Description:** Retrieves all items with optional filtering via query parameters.

**Query Parameters:**
- `is_active` (boolean): Filter by active status (`true` or `false`)
- `min_price` (number): Minimum price filter
- `max_price` (number): Maximum price filter
- `tag` (string): Filter items containing the specified tag

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Wireless Headphones",
        "description": "High-quality wireless headphones",
        "price": 199.99,
        "quantity": 50,
        "is_active": true,
        "tags": ["electronics", "audio"],
        "metadata": {
          "category": "electronics",
          "weight": 0.3
        },
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "count": 1,
    "total": 1
  },
  "message": "Retrieved 1 items successfully"
}
```

**cURL Examples:**
```bash
# Get all items
curl -X GET "https://your-api-gateway-url/items"

# Get only active items
curl -X GET "https://your-api-gateway-url/items?is_active=true"

# Get items in price range $50-$200
curl -X GET "https://your-api-gateway-url/items?min_price=50&max_price=200"

# Get items with specific tag
curl -X GET "https://your-api-gateway-url/items?tag=electronics"

# Combine multiple filters
curl -X GET "https://your-api-gateway-url/items?is_active=true&min_price=100&tag=electronics"
```

### 3. Get Single Item

**Endpoint:** `GET /items/{id}`

**Description:** Retrieves a specific item by its ID.

**Path Parameters:**
- `id` (string): The unique identifier of the item

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones",
    "price": 199.99,
    "quantity": 50,
    "is_active": true,
    "tags": ["electronics", "audio"],
    "metadata": {
      "category": "electronics",
      "weight": 0.3
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "Item '550e8400-e29b-41d4-a716-446655440000' retrieved successfully"
}
```

**Not Found Response (404):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Item with ID 'non-existent-id' not found"
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**cURL Example:**
```bash
curl -X GET "https://your-api-gateway-url/items/550e8400-e29b-41d4-a716-446655440000"
```

### 4. Update Item

**Endpoint:** `PUT /items/{id}`

**Description:** Updates an existing item. All fields are optional; only provided fields will be updated.

**Path Parameters:**
- `id` (string): The unique identifier of the item to update

**Request Body (partial update example):**
```json
{
  "name": "Premium Wireless Headphones",
  "price": 249.99,
  "quantity": 25,
  "tags": ["electronics", "audio", "premium"],
  "metadata": {
    "category": "electronics",
    "brand": "TechCorp",
    "weight": 0.35,
    "features": ["noise-cancellation", "bluetooth-5.2", "40h-battery"]
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Premium Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 249.99,
    "quantity": 25,
    "is_active": true,
    "tags": ["electronics", "audio", "premium"],
    "metadata": {
      "category": "electronics",
      "brand": "TechCorp",
      "weight": 0.35,
      "dimensions": {
        "length": 20,
        "width": 18,
        "height": 8
      },
      "features": ["noise-cancellation", "bluetooth-5.2", "40h-battery"]
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:45:00Z"
  },
  "message": "Item '550e8400-e29b-41d4-a716-446655440000' updated successfully"
}
```

**cURL Example:**
```bash
curl -X PUT "https://your-api-gateway-url/items/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Wireless Headphones",
    "price": 249.99,
    "quantity": 25,
    "tags": ["electronics", "audio", "premium"]
  }'
```

### 5. Delete Item

**Endpoint:** `DELETE /items/{id}`

**Description:** Deletes an item by its ID.

**Path Parameters:**
- `id` (string): The unique identifier of the item to delete

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted": true
  },
  "message": "Item '550e8400-e29b-41d4-a716-446655440000' deleted successfully"
}
```

**Not Found Response (404):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Item with ID 'non-existent-id' not found"
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**cURL Example:**
```bash
curl -X DELETE "https://your-api-gateway-url/items/550e8400-e29b-41d4-a716-446655440000"
```

## Error Responses

### Validation Errors (400)

**Invalid JSON:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_JSON",
    "message": "Invalid JSON format in request body"
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Missing Required Fields:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "name",
        "message": "name is required"
      },
      {
        "field": "price",
        "message": "price is required"
      }
    ]
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Invalid Data Types:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "price",
        "message": "price must be a number"
      },
      {
        "field": "is_active",
        "message": "is_active must be a boolean"
      }
    ]
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### Server Errors (500)

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred"
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

## Complete Workflow Example

Here's a complete example showing a typical workflow:

```bash
# Set your API Gateway URL
API_URL="https://your-api-gateway-url"

# 1. Create a new item
ITEM_ID=$(curl -s -X POST "$API_URL/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smart Watch",
    "description": "Fitness tracking smart watch",
    "price": 299.99,
    "quantity": 30,
    "is_active": true,
    "tags": ["electronics", "wearable", "fitness"],
    "metadata": {
      "category": "wearables",
      "battery_life": "7 days",
      "water_resistant": true
    }
  }' | jq -r '.data.id')

echo "Created item with ID: $ITEM_ID"

# 2. Get the created item
curl -s -X GET "$API_URL/items/$ITEM_ID" | jq '.'

# 3. Update the item
curl -s -X PUT "$API_URL/items/$ITEM_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 279.99,
    "quantity": 25,
    "metadata": {
      "category": "wearables",
      "battery_life": "10 days",
      "water_resistant": true,
      "gps": true
    }
  }' | jq '.'

# 4. Get all items
curl -s -X GET "$API_URL/items" | jq '.'

# 5. Get items with filters
curl -s -X GET "$API_URL/items?tag=electronics&min_price=200" | jq '.'

# 6. Delete the item
curl -s -X DELETE "$API_URL/items/$ITEM_ID" | jq '.'

# 7. Verify deletion (should return 404)
curl -s -X GET "$API_URL/items/$ITEM_ID" | jq '.'
```

## Testing with Different Data Types

The API supports all JSON data types. Here are examples:

```json
{
  "name": "Complex Item",
  "description": "Demonstrates all data types",
  "price": 99.99,
  "quantity": 10,
  "is_active": true,
  "tags": ["test", "demo"],
  "metadata": {
    "string_field": "text value",
    "number_field": 42,
    "float_field": 3.14159,
    "boolean_field": false,
    "null_field": null,
    "array_field": [1, 2, 3, "mixed", true],
    "nested_object": {
      "level2": {
        "level3": "deep nesting works"
      }
    },
    "empty_array": [],
    "empty_object": {}
  }
}
```

This comprehensive example shows that the API can handle complex nested structures and all JSON data types as specified in the requirements.