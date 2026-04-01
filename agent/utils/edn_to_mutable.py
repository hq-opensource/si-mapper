"""
Local copy of the edn_to_mutable utility.

This is a standalone copy that does NOT import from the server package.
It recursively converts ImmutableDict/Mapping to standard Python dicts
and tuples/lists to standard Python lists.
"""

from collections.abc import Mapping
from typing import Any
import logging

logger = logging.getLogger(__name__)


def edn_to_mutable(data: Any) -> Any:
    """
    Recursively converts ImmutableDict/Mapping to standard Python dicts,
    and tuples/lists to standard Python lists.
    """
    # 1. Check for Mapping (covers dict AND ImmutableDict)
    if isinstance(data, Mapping):
        return {k: edn_to_mutable(v) for k, v in data.items()}

    # 2. Check for list or tuple (but not strings)
    elif isinstance(data, (list, tuple)) and not isinstance(data, str):
        return [edn_to_mutable(i) for i in data]

    # 3. Return primitives as is
    else:
        return data
