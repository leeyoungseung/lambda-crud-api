"""
Comprehensive test data sets for Lambda CRUD API testing.
Provides various data scenarios including edge cases and invalid data.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any


class TestDataGenerator:
    """Generator for comprehensive test data sets."""
    
    @staticmethod
    def get_valid_items() -> List[Dict[str, Any]]:
        """
        Get a collection of valid items covering all JSON data types.
        
        Returns:
            List of valid item dictionaries
        """
        return [
            # Basic electronics item
            {
                "id": "electronics-001",
                "name": "Wireless Bluetooth Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "price": 199.99,
                "quantity": 25,
                "is_active": True,
                "tags": ["electronics", "audio", "wireless", "bluetooth"],
                "metadata": {
                    "category": "electronics",
                    "brand": "TechBrand",
                    "weight": 0.3,
                    "dimensions": {
                        "length": 18.5,
                        "width": 16.2,
                        "height": 8.1
                    },
                    "features": ["noise-cancellation", "wireless", "foldable"],
                    "warranty_months": 24,
                    "color_options": ["black", "white", "blue"]
                },
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            },
            
            # Book item with null optional fields
            {
                "id": "book-001",
                "name": "Python Programming Guide",
                "description": None,  # Null optional field
                "price": 49.99,
                "quantity": 100,
                "is_active": True,
                "tags": ["books", "programming", "python", "education"],
                "metadata": {
                    "category": "books",
                    "author": "Jane Developer",
                    "isbn": "978-0123456789",
                    "pages": 450,
                    "publisher": "Tech Publications",
                    "publication_year": 2024,
                    "language": "English",
                    "format": "paperback"
                },
                "created_at": "2024-01-02T14:30:00Z",
                "updated_at": "2024-01-02T14:30:00Z"
            },
            
            # Clothing item with complex nested metadata
            {
                "id": "clothing-001",
                "name": "Premium Cotton T-Shirt",
                "description": "Comfortable 100% organic cotton t-shirt",
                "price": 29.99,
                "quantity": 50,
                "is_active": False,  # Inactive item
                "tags": ["clothing", "cotton", "organic", "casual"],
                "metadata": {
                    "category": "clothing",
                    "material": "100% organic cotton",
                    "care_instructions": ["machine wash cold", "tumble dry low", "do not bleach"],
                    "sizes": {
                        "available": ["XS", "S", "M", "L", "XL", "XXL"],
                        "size_chart": {
                            "S": {"chest": 36, "length": 28},
                            "M": {"chest": 40, "length": 29},
                            "L": {"chest": 44, "length": 30}
                        }
                    },
                    "colors": ["white", "black", "navy", "gray"],
                    "sustainability": {
                        "organic": True,
                        "fair_trade": True,
                        "carbon_neutral": False
                    }
                },
                "created_at": "2024-01-03T09:15:00Z",
                "updated_at": "2024-01-05T16:45:00Z"
            },
            
            # Home & Garden item with minimal data
            {
                "id": "home-001",
                "name": "Ceramic Plant Pot",
                "description": "Small decorative ceramic pot for indoor plants",
                "price": 15.50,
                "quantity": 200,
                "is_active": True,
                "tags": ["home", "garden", "ceramic", "decor"],
                "metadata": {
                    "category": "home_garden",
                    "material": "ceramic",
                    "color": "terracotta",
                    "diameter_cm": 12.5,
                    "height_cm": 10.0,
                    "drainage_holes": True
                },
                "created_at": "2024-01-04T11:20:00Z",
                "updated_at": "2024-01-04T11:20:00Z"
            },
            
            # Sports equipment with arrays and numbers
            {
                "id": "sports-001",
                "name": "Professional Tennis Racket",
                "description": "High-performance tennis racket for competitive play",
                "price": 299.00,
                "quantity": 15,
                "is_active": True,
                "tags": ["sports", "tennis", "professional", "equipment"],
                "metadata": {
                    "category": "sports",
                    "sport": "tennis",
                    "weight_grams": 310,
                    "head_size_sq_inches": 100,
                    "string_pattern": "16x19",
                    "grip_sizes": [1, 2, 3, 4, 5],
                    "recommended_for": ["intermediate", "advanced"],
                    "specifications": {
                        "length_inches": 27.0,
                        "balance_mm": 320,
                        "stiffness_rating": 65,
                        "swing_weight": 325
                    }
                },
                "created_at": "2024-01-05T13:45:00Z",
                "updated_at": "2024-01-05T13:45:00Z"
            }
        ]
    
    @staticmethod
    def get_edge_case_items() -> List[Dict[str, Any]]:
        """
        Get items that test edge cases and boundary conditions.
        
        Returns:
            List of edge case item dictionaries
        """
        return [
            # Minimum values
            {
                "id": "a",  # Minimum length ID
                "name": "A",  # Minimum length name
                "price": 0.01,  # Minimum price
                "quantity": 0,  # Minimum quantity
                "is_active": False,
                "tags": [],  # Empty array
                "metadata": {}  # Empty object
            },
            
            # Maximum values
            {
                "id": "a" * 50,  # Maximum length ID
                "name": "A" * 100,  # Maximum length name
                "description": "D" * 500,  # Maximum length description
                "price": 999999.99,  # Maximum price
                "quantity": 999999,  # Maximum quantity
                "is_active": True,
                "tags": [f"tag{i}" for i in range(10)],  # Maximum tags
                "metadata": {
                    "large_nested_object": {
                        f"key{i}": f"value{i}" for i in range(20)
                    }
                }
            },
            
            # Special characters and unicode
            {
                "id": "special-chars-123",
                "name": "Item with 'quotes' and \"double quotes\"",
                "description": "Description with\nnewlines and\ttabs and émojis 🚀",
                "price": 123.45,
                "quantity": 10,
                "is_active": True,
                "tags": ["special-chars", "unicode", "émojis"],
                "metadata": {
                    "unicode_text": "Héllo Wörld! 你好世界 🌍",
                    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                    "json_like_string": '{"key": "value"}',
                    "escaped_quotes": "He said \"Hello\" to me"
                }
            },
            
            # Floating point precision
            {
                "id": "precision-test",
                "name": "Precision Test Item",
                "price": 99.999999,  # High precision float
                "quantity": 1,
                "is_active": True,
                "metadata": {
                    "pi": 3.141592653589793,
                    "very_small": 0.000000001,
                    "very_large": 999999999.999999,
                    "scientific_notation": 1.23e-10
                }
            },
            
            # Deep nesting
            {
                "id": "deep-nested",
                "name": "Deep Nested Item",
                "price": 50.00,
                "quantity": 5,
                "is_active": True,
                "metadata": {
                    "level1": {
                        "level2": {
                            "level3": {
                                "level4": {
                                    "level5": {
                                        "deep_value": "Found me!",
                                        "deep_array": [1, 2, 3, {"nested_in_array": True}],
                                        "deep_number": 42.42
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
    
    @staticmethod
    def get_invalid_items() -> List[Dict[str, Any]]:
        """
        Get items with various validation errors for testing error handling.
        
        Returns:
            List of invalid item dictionaries with expected errors
        """
        return [
            # Missing required fields
            {
                "data": {
                    "description": "Missing required fields"
                },
                "expected_errors": ["name", "price", "quantity", "is_active"]
            },
            
            # Invalid data types
            {
                "data": {
                    "name": 123,  # Should be string
                    "price": "not_a_number",  # Should be number
                    "quantity": 10.5,  # Should be integer
                    "is_active": "true",  # Should be boolean
                    "tags": "not_an_array",  # Should be array
                    "metadata": "not_an_object"  # Should be object
                },
                "expected_errors": ["name", "price", "quantity", "is_active", "tags", "metadata"]
            },
            
            # Out of range values
            {
                "data": {
                    "id": "a" * 51,  # Too long
                    "name": "",  # Too short
                    "description": "D" * 501,  # Too long
                    "price": -10.00,  # Negative
                    "quantity": -5,  # Negative
                    "is_active": True,
                    "tags": [f"tag{i}" for i in range(11)]  # Too many tags
                },
                "expected_errors": ["id", "name", "description", "price", "quantity", "tags"]
            },
            
            # Invalid formats
            {
                "data": {
                    "id": "invalid@id!",  # Invalid characters
                    "name": "Valid Name",
                    "price": 99.99,
                    "quantity": 10,
                    "is_active": True,
                    "created_at": "not_a_datetime",  # Invalid datetime format
                    "updated_at": "2024-13-45T25:70:70Z"  # Invalid datetime
                },
                "expected_errors": ["id", "created_at", "updated_at"]
            },
            
            # Null required fields
            {
                "data": {
                    "id": None,
                    "name": None,
                    "price": None,
                    "quantity": None,
                    "is_active": None
                },
                "expected_errors": ["id", "name", "price", "quantity", "is_active"]
            },
            
            # Array with invalid item types
            {
                "data": {
                    "name": "Array Test",
                    "price": 99.99,
                    "quantity": 10,
                    "is_active": True,
                    "tags": ["valid_tag", 123, True, {"invalid": "object"}]  # Mixed types
                },
                "expected_errors": ["tags"]
            }
        ]
    
    @staticmethod
    def get_update_test_data() -> List[Dict[str, Any]]:
        """
        Get test data specifically for update operations.
        
        Returns:
            List of update test scenarios
        """
        return [
            # Partial update - single field
            {
                "description": "Update single field",
                "update_data": {"name": "Updated Name"},
                "should_succeed": True
            },
            
            # Partial update - multiple fields
            {
                "description": "Update multiple fields",
                "update_data": {
                    "name": "Updated Name",
                    "price": 199.99,
                    "description": "Updated description"
                },
                "should_succeed": True
            },
            
            # Update with null optional field
            {
                "description": "Set optional field to null",
                "update_data": {"description": None},
                "should_succeed": True
            },
            
            # Try to update protected fields (should be ignored)
            {
                "description": "Try to update protected fields",
                "update_data": {
                    "id": "different-id",
                    "created_at": "2024-12-31T23:59:59Z",
                    "name": "Updated Name"
                },
                "should_succeed": True,
                "protected_fields": ["id", "created_at"]
            },
            
            # Update with validation errors
            {
                "description": "Update with validation errors",
                "update_data": {
                    "name": "",  # Too short
                    "price": -10.00  # Negative
                },
                "should_succeed": False,
                "expected_errors": ["name", "price"]
            },
            
            # Empty update data
            {
                "description": "Empty update data",
                "update_data": {},
                "should_succeed": False,
                "expected_error": "empty"
            },
            
            # Update only system fields (should fail)
            {
                "description": "Update only system fields",
                "update_data": {
                    "id": "different-id",
                    "created_at": "2024-12-31T23:59:59Z"
                },
                "should_succeed": False,
                "expected_error": "no valid fields"
            }
        ]
    
    @staticmethod
    def get_query_filter_test_data() -> List[Dict[str, Any]]:
        """
        Get test data for query filtering scenarios.
        
        Returns:
            List of query filter test scenarios
        """
        return [
            # Filter by is_active
            {
                "description": "Filter by active items",
                "query_params": {"is_active": "true"},
                "should_succeed": True
            },
            
            # Filter by price range
            {
                "description": "Filter by price range",
                "query_params": {"min_price": "50.00", "max_price": "200.00"},
                "should_succeed": True
            },
            
            # Filter by tag
            {
                "description": "Filter by tag",
                "query_params": {"tag": "electronics"},
                "should_succeed": True
            },
            
            # Combined filters
            {
                "description": "Combined filters",
                "query_params": {
                    "is_active": "true",
                    "min_price": "100.00",
                    "tag": "electronics"
                },
                "should_succeed": True
            },
            
            # Invalid filter values
            {
                "description": "Invalid is_active value",
                "query_params": {"is_active": "maybe"},
                "should_succeed": False,
                "expected_error": "is_active parameter must be"
            },
            
            # Invalid price values
            {
                "description": "Invalid price values",
                "query_params": {
                    "min_price": "not_a_number",
                    "max_price": "-10.00"
                },
                "should_succeed": False,
                "expected_errors": ["min_price", "max_price"]
            },
            
            # Invalid price range
            {
                "description": "Invalid price range (min > max)",
                "query_params": {
                    "min_price": "200.00",
                    "max_price": "100.00"
                },
                "should_succeed": False,
                "expected_error": "min_price cannot be greater than max_price"
            }
        ]
    
    @staticmethod
    def get_performance_test_data() -> List[Dict[str, Any]]:
        """
        Get test data for performance testing scenarios.
        
        Returns:
            List of items for performance testing
        """
        items = []
        
        # Generate 100 items for performance testing
        for i in range(100):
            item = {
                "id": f"perf-test-{i:03d}",
                "name": f"Performance Test Item {i}",
                "description": f"This is performance test item number {i} with some description text",
                "price": round(10.00 + (i * 1.5), 2),
                "quantity": (i % 50) + 1,
                "is_active": i % 2 == 0,  # Alternate active/inactive
                "tags": [
                    "performance",
                    "test",
                    f"category{i % 5}",  # 5 different categories
                    f"batch{i // 10}"    # 10 different batches
                ],
                "metadata": {
                    "category": f"category{i % 5}",
                    "batch": i // 10,
                    "index": i,
                    "generated": True,
                    "test_data": {
                        "value1": i * 2,
                        "value2": i * 3.14,
                        "value3": f"string_value_{i}"
                    }
                },
                "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat() + "Z",
                "updated_at": (datetime.utcnow() - timedelta(days=i)).isoformat() + "Z"
            }
            items.append(item)
        
        return items
    
    @staticmethod
    def get_large_payload_test_data() -> Dict[str, Any]:
        """
        Get test data with large payload for testing size limits.
        
        Returns:
            Large item dictionary
        """
        # Create large arrays and objects
        large_array = [f"item_{i}" for i in range(1000)]
        large_object = {f"key_{i}": f"value_{i}" for i in range(500)}
        
        return {
            "id": "large-payload-test",
            "name": "Large Payload Test Item",
            "description": "A" * 500,  # Maximum description length
            "price": 999.99,
            "quantity": 100,
            "is_active": True,
            "tags": [f"tag_{i}" for i in range(10)],  # Maximum tags
            "metadata": {
                "large_array": large_array,
                "large_object": large_object,
                "nested_large": {
                    "level1": {
                        "level2": {
                            "large_nested_array": [f"nested_item_{i}" for i in range(100)],
                            "large_nested_object": {f"nested_key_{i}": f"nested_value_{i}" for i in range(100)}
                        }
                    }
                },
                "repeated_data": ["repeated_string"] * 100
            }
        }
    
    @staticmethod
    def save_test_data_to_files(output_dir: str = "test_data_output") -> None:
        """
        Save all test data to JSON files for external use.
        
        Args:
            output_dir: Directory to save test data files
        """
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save different data sets
        datasets = {
            "valid_items.json": TestDataGenerator.get_valid_items(),
            "edge_case_items.json": TestDataGenerator.get_edge_case_items(),
            "invalid_items.json": TestDataGenerator.get_invalid_items(),
            "update_test_data.json": TestDataGenerator.get_update_test_data(),
            "query_filter_test_data.json": TestDataGenerator.get_query_filter_test_data(),
            "performance_test_data.json": TestDataGenerator.get_performance_test_data(),
            "large_payload_test_data.json": TestDataGenerator.get_large_payload_test_data()
        }
        
        for filename, data in datasets.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Test data saved to {output_dir}/")


# Convenience functions for easy access
def get_valid_test_items() -> List[Dict[str, Any]]:
    """Get valid test items."""
    return TestDataGenerator.get_valid_items()


def get_invalid_test_items() -> List[Dict[str, Any]]:
    """Get invalid test items."""
    return TestDataGenerator.get_invalid_items()


def get_edge_case_test_items() -> List[Dict[str, Any]]:
    """Get edge case test items."""
    return TestDataGenerator.get_edge_case_items()


def get_performance_test_items() -> List[Dict[str, Any]]:
    """Get performance test items."""
    return TestDataGenerator.get_performance_test_data()


# Export all test data generators
__all__ = [
    'TestDataGenerator',
    'get_valid_test_items',
    'get_invalid_test_items',
    'get_edge_case_test_items',
    'get_performance_test_items'
]


if __name__ == "__main__":
    # Generate and save test data when run directly
    TestDataGenerator.save_test_data_to_files()
    print("Test data generation complete!")