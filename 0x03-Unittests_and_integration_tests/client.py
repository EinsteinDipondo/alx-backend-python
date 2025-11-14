#!/usr/bin/env python3
"""
Client for interacting with the GitHub API to retrieve organization data.
"""
from typing import Dict
from utils import get_json


class GithubOrgClient:
    """
    A client for fetching GitHub organization data.
    """
    def __init__(self, org_name: str) -> None:
        """
        Initializes the client with the organization name.
        """
        self._org_url = f"https://api.github.com/orgs/{org_name}"

    def org(self) -> Dict:
        """
        Returns the organization payload from the GitHub API.
        """
        return get_json(self._org_url)

    def repos_url(self) -> str:
        """
        Returns the repository URL string from the organization payload.
        """
        return self.org()["repos_url"]