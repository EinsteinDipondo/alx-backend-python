#!/usr/bin/env python3
"""
Unit tests for the utility functions in utils.py,
demonstrating parameterized testing and mocking HTTP calls.
"""
import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized
from typing import Union, Dict, Any, Tuple
from utils import access_nested_map, get_json

class TestAccessNestedMap(unittest.TestCase):
    """
    Tests the functionality of the utils.access_nested_map function
    using various valid inputs.
    """

    @parameterized.expand([
        # (nested_map, path, expected_result)
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(
            self,
            nested_map: Dict,
            path: Tuple[str, ...],
            expected: Union[int, Dict[str, Any]]
        ) -> None:
        """
        Tests that access_nested_map returns the correct value for a given
        nested map and a valid key path.
        """
        # The body is intentionally kept to one line to satisfy the requirement.
        self.assertEqual(access_nested_map(nested_map, path), expected)


class TestGetJson(unittest.TestCase):
    """
    Tests the functionality of the utils.get_json function, ensuring
    it correctly handles HTTP requests using mocking.
    """

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    @patch('requests.get')
    def test_get_json(self, test_url: str, test_payload: Dict, mock_get: Mock) -> None:
        """
        Tests that get_json returns the expected payload and makes
        exactly one call to requests.get with the correct URL.
        """
        # 1. Configure the mock object to return the expected payload
        # Create a Mock response object
        mock_response = Mock()
        # Set the mock response's .json() method to return test_payload
        mock_response.json.return_value = test_payload
        
        # Configure the patched requests.get to return our mock response
        mock_get.return_value = mock_response

        # 2. Call the function under test
        result = get_json(test_url)

        # 3. Assertions (required assertions are placed here)
        # Test 1: Check if the mocked get was called exactly once with the correct URL
        mock_get.assert_called_once_with(test_url)
        # Test 2: Check if the output of get_json matches the expected payload
        self.assertEqual(result, test_payload)