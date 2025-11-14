#!/usr/bin/env python3
"""
Unit tests for the client.GithubOrgClient class, demonstrating
patching and parameterization of class methods.
"""
import unittest
from unittest.mock import patch, Mock, PropertyMock
from parameterized import parameterized
from client import GithubOrgClient
from typing import List, Dict


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
            # Initialize the client (org_name is irrelevant
            # since org() is mocked)
            client = GithubOrgClient("holbertonschool")

            # Call the method under test
            result_url = client.repos_url

            # Test 1: Check that the result is the expected URL
            self.assertEqual(result_url, expected_repos_url)

            # Test 2: Check that client.org was called once
            mock_org.assert_called_once()

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json: Mock) -> None:
        """
        Tests that public_repos returns the expected list of repository names,
        mocking both the network call (get_json) and the internal dependency
        (repos_url).
        """
        # 1. Define the payloads and expected result
        test_repos_payload: List[Dict] = [
            {"name": "repo-1", "license": {"key": "mit"}},
            {"name": "repo-2", "license": {"key": "apache-2.0"}},
            {"name": "repo-3", "license": None},
        ]
        expected_repos: List[str] = ["repo-1", "repo-2", "repo-3"]
        mock_repos_url: str = (
            "https://api.github.com/orgs/holbertonschool/repos"
        )

        # 2. Configure the mocked network call
        mock_get_json.return_value = test_repos_payload

        # 3. Configure the mocked internal dependency (repos_url)
        with patch.object(
            GithubOrgClient,
            'repos_url',
            new_callable=PropertyMock,
            return_value=mock_repos_url
        ) as mock_repos_url_property:
            # Initialize the client
            client = GithubOrgClient("holbertonschool")

            # Call the method under test
            result_repos = client.public_repos()

            # 4. Assertions
            # Test 1: Check that the result matches the expected list of names
            self.assertEqual(result_repos, expected_repos)

            # Test 2: Check that the internal dependency was called once
            mock_repos_url_property.assert_called_once()

            # Test 3: Check that the network call was made once with the
            # correct URL.
            mock_get_json.assert_called_once_with(mock_repos_url)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
        ({"license": {"key": "my_license"}}, "other_license", False),
        ({}, "my_license", False),
        ({"license": None}, "my_license", False),
    ])
    def test_has_license(
            self,
            repo: Dict,
            license_key: str,
            expected_result: bool
    ) -> None:
        """
        Tests that GithubOrgClient.has_license returns the expected boolean
        based on the repository dictionary and license key.
        """
        client = GithubOrgClient("irrelevant")
        result = client.has_license(repo, license_key)
        self.assertEqual(result, expected_result)