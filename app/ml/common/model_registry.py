"""
app/ml/common/model_registry.py
--------------------------------
Central model registry for tracking model metadata, versions, and active model paths.
"""

from typing import Dict, Any


class ModelRegistry:
    """
    Registry for managing model definitions, versions, and paths across domain modules.
    """

    def __init__(self):
        self._registry: Dict[str, Dict[str, Any]] = {}

    def register(self, model_name: str, metadata: Dict[str, Any]) -> None:
        """Register model metadata."""
        self._registry[model_name] = metadata

    def get_metadata(self, model_name: str) -> Dict[str, Any]:
        """Retrieve model metadata."""
        return self._registry.get(model_name, {})


model_registry = ModelRegistry()
