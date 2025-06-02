"""
Utility functions for CSV data processing.
"""

from typing import Dict, List, Any, Union, Set


class DataFlattener:
    """Utility class for flattening nested dictionary structures."""

    def __init__(
        self,
        separator: str = "__",
        flatten_enabled: bool = True,
        preserve_lists: bool = True,
    ):
        self.separator = separator
        self.flatten_enabled = flatten_enabled
        self.preserve_lists = preserve_lists

    def flatten_data(
        self, data: Union[Dict, Any], parent_key: str = ""
    ) -> Dict[str, Any]:
        """
        Flatten a nested dictionary structure.

        Args:
            data: Data to flatten (dict, object, or primitive)
            parent_key: Parent key for nested items

        Returns:
            Flattened dictionary
        """
        if not self.flatten_enabled:
            return self._handle_non_flattened(data, parent_key)

        # Convert objects to dictionaries
        if hasattr(data, "__dict__"):
            data = data.__dict__
        elif not isinstance(data, dict):
            return {parent_key or "value": data}

        items = []
        for key, value in data.items():
            new_key = self._build_key(parent_key, key)
            items.extend(self._process_value(new_key, value))

        return dict(items)

    def _handle_non_flattened(self, data: Any, parent_key: str) -> Dict[str, Any]:
        """Handle data when flattening is disabled."""
        if isinstance(data, dict):
            return {parent_key or "data": str(data)}
        return {parent_key or "value": data}

    def _build_key(self, parent_key: str, key: str) -> str:
        """Build nested key with separator."""
        return f"{parent_key}{self.separator}{key}" if parent_key else key

    def _process_value(self, key: str, value: Any) -> List[tuple]:
        """Process individual values based on their type."""
        if isinstance(value, dict):
            return list(self.flatten_data(value, key).items())
        elif isinstance(value, list):
            return self._process_list(key, value)
        else:
            return [(key, value)]

    def _process_list(self, key: str, value: List[Any]) -> List[tuple]:
        """Process list values."""
        if not value:
            return [(key, "")]

        if self.preserve_lists:
            return [(key, value)]

        if isinstance(value[0], dict) and self.flatten_enabled:
            items = []
            for i, item in enumerate(value):
                indexed_key = f"{key}{self.separator}{i}"
                items.extend(self.flatten_data(item, indexed_key).items())
            return items
        else:
            # Convert to comma-separated string
            return [(key, ", ".join(str(v) for v in value))]


class FieldnameManager:
    """Manages CSV fieldnames collection and sorting."""

    @staticmethod
    def collect_fieldnames(data_list: List[Dict[str, Any]]) -> List[str]:
        """Collect all unique fieldnames from a list of dictionaries."""
        fieldnames: Set[str] = set()
        for item in data_list:
            fieldnames.update(item.keys())
        return sorted(list(fieldnames))

    @staticmethod
    def ensure_consistent_data(
        data_list: List[Dict[str, Any]], fieldnames: List[str]
    ) -> List[Dict[str, Any]]:
        """Ensure all data items have all fieldnames with default values."""
        return [
            {field: item.get(field, "") for field in fieldnames} for item in data_list
        ]
