import pytest
import os
import joblib
import tempfile
from sklearn.linear_model import LinearRegression
import numpy as np

@pytest.fixture
def sample_linear_regression_model():
    """
    Creates a simple LinearRegression model, trains it on dummy data,
    saves it to a temporary file, and returns the file path.
    """
    # Create dummy data
    X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
    y = np.dot(X, np.array([1, 2])) + 3

    # Train model
    model = LinearRegression()
    model.fit(X, y)

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        joblib.dump(model, tmp.name)
        tmp_path = tmp.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
