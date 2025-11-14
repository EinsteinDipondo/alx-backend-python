#!/usr/bin/env python3
"""
A module providing utility functions, including one for accessing
values in nested dictionaries and fetching JSON from URLs.
"""
from typing import Mapping, Sequence, Any, Dict
import requests

def access_nested_map(nested_map: Mapping, path: Sequence[Any]) -> Any:
    """
    Accesses a value in a nested dictionary using a sequence of keys.

    Args:
        nested_map: The nested dictionary.
        path: A sequence of keys defining the path to the desired value.

    Returns:
        The value at the specified path.

    Raises:
        KeyError: If any key in the path is not found in the map.
    """
    current_map = nested_map
    for key in path:
        if not isinstance(current_map, Mapping) or key not in current_map:
            raise KeyError(key)
        current_map = current_map[key]
    return current_map

def get_json(url: str) -> Dict:
    """
    Fetches JSON data from a given URL.

    Args:
        url: The URL to fetch data from.

    Returns:
        The JSON payload (as a dictionary).
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.json()