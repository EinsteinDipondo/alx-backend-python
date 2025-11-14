#!/usr/bin/env python3
"""
Unit tests for the client.GithubOrgClient class, demonstrating
patching and parameterization of class methods.
"""
import unittest
from unittest.mock import patch, Mock, PropertyMock
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

    def test_public_repos_url(self) -> None:
        """
        Tests that the repos_url method returns the expected URL,
        mocking the underlying org property/method.
        """
        # Known payload mimicking the GitHub API response
        test_payload = {
            "repos_url": "https://api.github.com/orgs/holbertonschool/repos",
        }
        expected_repos_url = test_payload["repos_url"]

        # Use patch as a context manager to mock the 'org' method
        with patch.object(
            GithubOrgClient,
            'org',
            new_callable=PropertyMock,
            return_value=test_payload
        ) as mock_org:
            # Initialize the client (org_name is irrelevant since org() is mocked)
            client = GithubOrgClient("holbertonschool")

            # Call the method under test
            result_url = client.repos_url()

            # Test 1: Check that the result is the expected URL
            self.assertEqual(result_url, expected_repos_url)

            # Test 2: Check that client.org was called once
            mock_org.assert_called_once()