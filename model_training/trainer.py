from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseTrainer(ABC):
    """
    Abstract base class for model training.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the trainer with configuration.

        Args:
            config: Configuration dictionary (hyperparameters, paths, etc.).
        """
        self.config = config
        self.model = None
        self.optimizer = None
        self.loss_fn = None

    @abstractmethod
    def build_model(self):
        """Builds the model architecture."""
        pass

    @abstractmethod
    def train(self, train_loader: Any, val_loader: Optional[Any] = None) -> Dict[str, float]:
        """
        Trains the model.

        Args:
            train_loader: DataLoader for training data.
            val_loader: DataLoader for validation data (optional).

        Returns:
            Dictionary containing training metrics (e.g., loss, accuracy).
        """
        pass

    @abstractmethod
    def evaluate(self, test_loader: Any) -> Dict[str, float]:
        """
        Evaluates the model.

        Args:
            test_loader: DataLoader for test data.

        Returns:
            Dictionary containing evaluation metrics.
        """
        pass

    @abstractmethod
    def save_checkpoint(self, path: str):
        """Saves the model checkpoint."""
        pass

    @abstractmethod
    def load_checkpoint(self, path: str):
        """Loads the model checkpoint."""
        pass
