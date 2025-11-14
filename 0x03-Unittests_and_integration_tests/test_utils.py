#!/usr/bin/env python3
"""
Unit tests for the utility functions in utils.py,
demonstrating parameterized testing, mocking, and memoization tests.
"""
import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized
from typing import Union, Dict, Any, Tuple
from utils import access_nested_map, get_json, memoize


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
        mock_response = Mock()
        # Set the mock response's .json() method to return test_payload
        mock_response.json.return_value = test_payload
        mock_get.return_value = mock_response

        # 2. Call the function under test
        result = get_json(test_url)

        # 3. Assertions
        # Test 1: Check if the mocked get was called exactly once with the
        # correct URL (E501 fix)
        mock_get.assert_called_once_with(test_url)
        # Test 2: Check if the output of get_json matches the expected payload
        self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """
    Tests the functionality of the utils.memoize decorator, ensuring
    the decorated property calls its underlying method only once.
    """

    def test_memoize(self) -> None:
        """
        Tests that a_property calls a_method only once when accessed twice.
        """
        class TestClass:
            """Class for testing memoization."""
            def a_method(self) -> int:
                """Returns the value 42."""
                return 42

            @memoize
            def a_property(self) -> int:
                """Returns the result of a_method."""
                return self.a_method()

        # Patch a_method within the scope of TestClass
        with patch.object(
                TestClass, 'a_method', return_value=42
        ) as mock_a_method:
            # Instantiate the class
            test_instance = TestClass()

            # Call a_property twice
            result1 = test_instance.a_property
            result2 = test_instance.a_property

            # Assertions:
            # 1. Check if the result is correct
            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)

            # 2. Check if the underlying method was called only once
            mock_a_method.assert_called_once()