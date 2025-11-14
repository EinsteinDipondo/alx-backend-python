#!/usr/bin/env python3
"""
Unit tests for the access_nested_map function in utils.py,
demonstrating the use of parameterized testing.
"""
import unittest
from parameterized import parameterized
from typing import Union, Dict, Any, Tuple
from utils import access_nested_map # Import the function to be tested

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
