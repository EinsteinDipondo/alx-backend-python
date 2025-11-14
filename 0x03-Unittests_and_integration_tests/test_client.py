#!/usr/bin/env python3
"""
Unit tests for the client.GithubOrgClient class, demonstrating
patching and parameterization of class methods.
"""
import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """
    Tests the GithubOrgClient.org method using parameterized inputs
    and patching the external utility call.
    """

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name: str, mock_get_json: Mock) -> None:
        """
        Tests that GithubOrgClient.org returns the correct value and
        that get_json is called exactly once with the expected URL.
        """
        # The expected URL format
        test_url = f"https://api.github.com/orgs/{org_name}"

        # Initialize the client with the organization name
        client = GithubOrgClient(org_name)

        # Call the method under test
        client.org()

        # Assertion 1: Check if get_json was called once with the expected URL
        # We patch 'client.get_json' because that is where it is imported.
        mock_get_json.assert_called_once_with(test_url)