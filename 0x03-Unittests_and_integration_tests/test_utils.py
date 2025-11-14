#!/usr/bin/env python3
"""
Unit tests for utils module demonstrating unit testing concepts.
"""

import unittest
from utils import access_nested_map


class TestAccessNestedMap(unittest.TestCase):
    """
    Test class for access_nested_map function with parameterized tests.
    """

    def test_access_nested_map(self):
        """
        Test access_nested_map returns correct value for valid paths.
        Uses multiple test cases within one test method.
        """
        # Test case 1: nested_map={"a": 1}, path=("a",)
        result1 = access_nested_map({"a": 1}, ("a",))
        self.assertEqual(result1, 1)

        # Test case 2: nested_map={"a": {"b": 2}}, path=("a",)
        result2 = access_nested_map({"a": {"b": 2}}, ("a",))
        self.assertEqual(result2, {"b": 2})

        # Test case 3: nested_map={"a": {"b": 2}}, path=("a", "b")
        result3 = access_nested_map({"a": {"b": 2}}, ("a", "b"))
        self.assertEqual(result3, 2)


if __name__ == '__main__':
    unittest.main()
