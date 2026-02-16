import pytest
from model_deploy.registry import ModelRegistry

class TestModelRegistry:
    def setup_method(self):
        self.registry = ModelRegistry()

    def test_register_model(self):
        """Test registering a new model version."""
        metadata = {"accuracy": 0.95, "framework": "pytorch"}
        model_version = self.registry.register_model(
            name="resnet50",
            version="v1",
            path="s3://models/resnet50/v1",
            metadata=metadata
        )

        assert model_version.name == "resnet50"
        assert model_version.version == "v1"
        assert model_version.path == "s3://models/resnet50/v1"
        assert model_version.metadata == metadata

    def test_get_model(self):
        """Test retrieving a registered model."""
        self.registry.register_model(
            name="bert-base",
            version="v1",
            path="models/bert/v1"
        )

        model = self.registry.get_model("bert-base", "v1")
        assert model is not None
        assert model.name == "bert-base"

        # Test non-existent model
        assert self.registry.get_model("bert-base", "v2") is None
        assert self.registry.get_model("gpt-3", "v1") is None

    def test_list_versions(self):
        """Test listing versions of a model."""
        self.registry.register_model("model_a", "v1", "path/v1")
        self.registry.register_model("model_a", "v2", "path/v2")

        versions = self.registry.list_versions("model_a")
        assert len(versions) == 2
        assert {v.version for v in versions} == {"v1", "v2"}

        # Test listing for non-existent model
        assert self.registry.list_versions("unknown_model") == []

    def test_duplicate_version_error(self):
        """Test that registering a duplicate version raises an error."""
        self.registry.register_model("model_x", "v1", "path/v1")

        with pytest.raises(ValueError, match="already exists"):
            self.registry.register_model("model_x", "v1", "path/new_v1")
