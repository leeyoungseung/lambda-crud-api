# Lambda CRUD API Documentation

A comprehensive serverless CRUD API built with AWS Lambda, API Gateway, and DynamoDB.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Data Model](#data-model)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)
- [SDKs and Libraries](#sdks-and-libraries)

## Overview

The Lambda CRUD API provides a complete set of operations for managing items in a DynamoDB database. The API is built using AWS Lambda functions for compute, API Gateway for HTTP routing, and DynamoDB for data persistence.

### Key Features

- **Serverless Architecture**: Fully serverless using AWS Lambda
- **Independent Functions**: Separate Lambda functions for each CRUD operation
- **Comprehensive Validation**: Full validation for all JSON data types
- **Error Handling**: Standardized error responses with proper HTTP status codes
- **CORS Support**: Full cross-origin resource sharing support
- **High Performance**: Optimized for low latency and high throughput

### Base URL

```
https://your-api-id.execute-api.ap-northeast-1.amazonaws.com/v1
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│  Lambda Functions │────│    DynamoDB     │
│                 │    │                 │    │                 │
│ • Routing       │    │ • Create        │    │ • Items Table   │
│ • CORS          │    │ • Read          │    │ • Auto-scaling  │
│ • Validation    │    │ • Update        │    │ • Encryption    │
│ • Rate Limiting │    │ • Delete        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## API Endpoints

### Items Collection

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/items` | Get all items (with optional filtering) |
| POST   | `/items` | Create a new item |

### Individual Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/items/{id}` | Get a specific item by ID |
| PUT    | `/items/{id}` | Update an existing item |
| DELETE | `/items/{id}` | Delete an item |

### CORS Support

| Method | Endpoint | Description |
|--------|----------|-------------|
| OPTIONS | `/items` | CORS preflight for items collection |
| OPTIONS | `/items/{id}` | CORS preflight for individual items |

## Data Model

### Item Schema

```json
{
  "id": "string",                    // Unique identifier (auto-generated if not provided)
  "name": "string",                  // Item name (required, 1-100 characters)
  "description": "string|null",      // Item description (optional, max 500 characters)
  "price": 99.99,                    // Item price (required, positive number)
  "quantity": 100,                   // Item quantity (required, non-negative integer)
  "is_active": true,                 // Active status (required boolean)
  "tags": ["string"],                // Array of tags (optional, max 10 items)
  "metadata": {                      // Additional metadata (optional object)
    "category": "string",
    "weight": 1.5,
    "dimensions": {
      "length": 10,
      "width": 5,
      "height": 3
    }
  },
  "created_at": "2024-01-01T00:00:00Z",  // Creation timestamp (auto-generated)
  "updated_at": "2024-01-01T00:00:00Z"   // Last update timestamp (auto-updated)
}
```

### Field Constraints

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | string | No* | 1-50 characters, alphanumeric + hyphens/underscores |
| `name` | string | Yes | 1-100 characters |
| `description` | string | No | Max 500 characters |
| `price` | number | Yes | Positive number, max 999999.99 |
| `quantity` | integer | Yes | Non-negative, max 999999 |
| `is_active` | boolean | Yes | true or false |
| `tags` | array | No | Max 10 string items |
| `metadata` | object | No | Any valid JSON object |
| `created_at` | string | No** | ISO 8601 datetime |
| `updated_at` | string | No** | ISO 8601 datetime |

*Auto-generated if not provided  
**Auto-managed by the system

## Authentication

Currently, the API does not require authentication. In production environments, consider implementing:

- API Keys
- AWS IAM authentication
- JWT tokens
- OAuth 2.0

## Error Handling

### Standard Error Response Format

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

### HTTP Status Codes

| Status Code | Description | When Used |
|-------------|-------------|-----------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation errors, malformed JSON |
| 404 | Not Found | Item not found |
| 500 | Internal Server Error | Unexpected server errors |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request data validation failed |
| `NOT_FOUND` | Requested resource not found |
| `BAD_REQUEST` | Malformed request or invalid parameters |
| `INTERNAL_SERVER_ERROR` | Unexpected server error |

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Burst Limit**: 5,000 requests
- **Rate Limit**: 2,000 requests per second
- **Throttling**: Requests exceeding limits receive HTTP 429

## Examples

### Create Item

**Request:**
```bash
curl -X POST https://api.example.com/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 199.99,
    "quantity": 25,
    "is_active": true,
    "tags": ["electronics", "audio", "wireless"],
    "metadata": {
      "category": "electronics",
      "brand": "TechBrand",
      "weight": 0.3,
      "features": ["noise-cancellation", "wireless", "foldable"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "item-abc123",
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 199.99,
    "quantity": 25,
    "is_active": true,
    "tags": ["electronics", "audio", "wireless"],
    "metadata": {
      "category": "electronics",
      "brand": "TechBrand",
      "weight": 0.3,
      "features": ["noise-cancellation", "wireless", "foldable"]
    },
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  "message": "Item 'item-abc123' created successfully",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Get All Items

**Request:**
```bash
curl https://api.example.com/v1/items
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "item-abc123",
        "name": "Wireless Headphones",
        "price": 199.99,
        "quantity": 25,
        "is_active": true,
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      }
    ],
    "count": 1,
    "total": 1
  },
  "message": "Retrieved 1 items successfully",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Get Item by ID

**Request:**
```bash
curl https://api.example.com/v1/items/item-abc123
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "item-abc123",
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 199.99,
    "quantity": 25,
    "is_active": true,
    "tags": ["electronics", "audio", "wireless"],
    "metadata": {
      "category": "electronics",
      "brand": "TechBrand"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  "message": "Item 'item-abc123' retrieved successfully",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Update Item

**Request:**
```bash
curl -X PUT https://api.example.com/v1/items/item-abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Wireless Headphones",
    "price": 249.99,
    "description": "Updated premium wireless headphones with enhanced features"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "item-abc123",
    "name": "Premium Wireless Headphones",
    "description": "Updated premium wireless headphones with enhanced features",
    "price": 249.99,
    "quantity": 25,
    "is_active": true,
    "tags": ["electronics", "audio", "wireless"],
    "metadata": {
      "category": "electronics",
      "brand": "TechBrand"
    },
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "message": "Item 'item-abc123' updated successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Delete Item

**Request:**
```bash
curl -X DELETE https://api.example.com/v1/items/item-abc123
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "item-abc123",
    "deleted": true,
    "deleted_item": {
      "id": "item-abc123",
      "name": "Premium Wireless Headphones",
      "price": 249.99,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  },
  "message": "Item 'item-abc123' deleted successfully",
  "timestamp": "2024-01-01T13:00:00Z"
}
```

### Query Parameters (Get All Items)

**Filter by Active Status:**
```bash
curl "https://api.example.com/v1/items?is_active=true"
```

**Filter by Price Range:**
```bash
curl "https://api.example.com/v1/items?min_price=50.00&max_price=200.00"
```

**Filter by Tag:**
```bash
curl "https://api.example.com/v1/items?tag=electronics"
```

**Combined Filters:**
```bash
curl "https://api.example.com/v1/items?is_active=true&min_price=100.00&tag=electronics"
```

### Error Examples

**Validation Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "name",
        "message": "Field 'name' is required"
      },
      {
        "field": "price",
        "message": "Field 'price' must be a positive number"
      }
    ]
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

**Not Found Error:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Item with id 'non-existent-id' not found"
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## SDKs and Libraries

### JavaScript/Node.js

```javascript
// Using fetch API
const createItem = async (itemData) => {
  const response = await fetch('https://api.example.com/v1/items', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(itemData),
  });
  
  return await response.json();
};

// Using axios
const axios = require('axios');

const api = axios.create({
  baseURL: 'https://api.example.com/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

const getAllItems = async () => {
  const response = await api.get('/items');
  return response.data;
};
```

### Python

```python
import requests
import json

class CrudApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def create_item(self, item_data):
        response = self.session.post(f'{self.base_url}/items', json=item_data)
        return response.json()
    
    def get_item(self, item_id):
        response = self.session.get(f'{self.base_url}/items/{item_id}')
        return response.json()
    
    def update_item(self, item_id, update_data):
        response = self.session.put(f'{self.base_url}/items/{item_id}', json=update_data)
        return response.json()
    
    def delete_item(self, item_id):
        response = self.session.delete(f'{self.base_url}/items/{item_id}')
        return response.json()

# Usage
client = CrudApiClient('https://api.example.com/v1')
result = client.create_item({
    'name': 'Test Item',
    'price': 99.99,
    'quantity': 10,
    'is_active': True
})
```

### Java

```java
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import com.fasterxml.jackson.databind.ObjectMapper;

public class CrudApiClient {
    private final HttpClient client;
    private final String baseUrl;
    private final ObjectMapper mapper;
    
    public CrudApiClient(String baseUrl) {
        this.client = HttpClient.newHttpClient();
        this.baseUrl = baseUrl;
        this.mapper = new ObjectMapper();
    }
    
    public ApiResponse createItem(Item item) throws Exception {
        String json = mapper.writeValueAsString(item);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/items"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build();
        
        HttpResponse<String> response = client.send(request, 
            HttpResponse.BodyHandlers.ofString());
        
        return mapper.readValue(response.body(), ApiResponse.class);
    }
}
```

## Best Practices

### Request Guidelines

1. **Always include Content-Type header** for POST/PUT requests
2. **Use proper HTTP methods** for each operation
3. **Handle errors gracefully** by checking the `success` field
4. **Implement retry logic** for 5xx errors
5. **Validate data client-side** before sending requests

### Performance Optimization

1. **Use query parameters** to filter results instead of fetching all items
2. **Implement client-side caching** for frequently accessed data
3. **Batch operations** when possible (future enhancement)
4. **Use compression** (gzip) for large payloads

### Security Considerations

1. **Validate all input data** before sending to the API
2. **Use HTTPS** for all API communications
3. **Implement proper authentication** in production
4. **Sanitize data** before displaying to users
5. **Follow OWASP guidelines** for API security

## Troubleshooting

### Common Issues

**Issue: 400 Bad Request with validation errors**
- Check that all required fields are present
- Verify data types match the schema
- Ensure field values are within allowed ranges

**Issue: 404 Not Found**
- Verify the item ID exists
- Check the URL path is correct
- Ensure the item hasn't been deleted

**Issue: 500 Internal Server Error**
- Check AWS service status
- Verify DynamoDB table exists and is accessible
- Review CloudWatch logs for detailed error information

### Support

For additional support:
- Check CloudWatch logs for detailed error information
- Review the OpenAPI specification for complete API details
- Contact the development team for assistance

## Changelog

### Version 1.0.0
- Initial release
- Complete CRUD operations
- Comprehensive validation
- Error handling
- CORS support
- Query filtering