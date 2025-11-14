#!/usr/bin/env python3
"""
A module providing utility functions, including one for accessing
values in nested dictionaries.
"""
from typing import Mapping, Sequence, Any

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