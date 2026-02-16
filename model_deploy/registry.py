from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ModelVersion:
    name: str
    version: str
    path: str
    metadata: Dict
    created_at: datetime

class ModelRegistry:
    """
    A simple in-memory model registry.
    In a real-world scenario, this would be backed by a database (e.g., PostgreSQL, MLflow).
    """

    def __init__(self):
        # Structure: {model_name: {version: ModelVersion}}
        self._registry: Dict[str, Dict[str, ModelVersion]] = {}

    def register_model(self, name: str, version: str, path: str, metadata: Optional[Dict] = None) -> ModelVersion:
        """
        Registers a new model version.

        Args:
            name: Name of the model (e.g., "resnet50_classifier").
            version: Version string (e.g., "v1.0.0").
            path: Path to the model artifacts (e.g., S3 bucket path).
            metadata: Additional metadata (metrics, hyperparameters).

        Returns:
            The created ModelVersion object.
        """
        if metadata is None:
            metadata = {}

        if name not in self._registry:
            self._registry[name] = {}

        if version in self._registry[name]:
            raise ValueError(f"Model {name} version {version} already exists.")

        model_version = ModelVersion(
            name=name,
            version=version,
            path=path,
            metadata=metadata,
            created_at=datetime.now()
        )

        self._registry[name][version] = model_version
        return model_version

    def get_model(self, name: str, version: str) -> Optional[ModelVersion]:
        """
        Retrieves a specific model version.
        """
        if name not in self._registry:
            return None
        return self._registry[name].get(version)

    def list_versions(self, name: str) -> List[ModelVersion]:
        """
        Lists all versions of a specific model.
        """
        if name not in self._registry:
            return []
        return list(self._registry[name].values())

    def list_models(self) -> List[str]:
        """
        Lists all registered model names.
        """
        return list(self._registry.keys())
