from sklearn.ensemble import IsolationForest
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.mission_models import AnomalyLog
import datetime
from typing import Dict, Any, List

class AnomalyDetector:
    def __init__(self, contamination=0.01):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_fitted = False

    def initialize_model(self):
        """
        Initialize the model with some dummy 'normal' data so it is ready to use.
        In a real system, this would load a saved model or train on historical DB data.
        """
        # Generate some synthetic normal telemetry data
        # Assume features: [voltage, temperature, signal_strength]
        # voltage ~ 5.0 +/- 0.5
        # temperature ~ 25.0 +/- 5.0
        # signal ~ -50 +/- 10

        n_samples = 100
        rng = np.random.RandomState(42)
        X_voltage = rng.normal(5.0, 0.5, (n_samples, 1))
        X_temp = rng.normal(25.0, 5.0, (n_samples, 1))
        X_signal = rng.normal(-50.0, 10.0, (n_samples, 1))

        X_train = np.hstack([X_voltage, X_temp, X_signal])

        self.train(X_train)

    def train(self, data: np.ndarray):
        """
        Train the IsolationForest model.
        data: Numpy array of feature vectors.
        """
        if data.size == 0:
            return
        self.model.fit(data)
        self.is_fitted = True

    def detect_telemetry_anomaly(self, telemetry_data: Dict[str, float]) -> bool:
        """
        Detect if a single telemetry data point is anomalous.
        """
        # Extract features in specific order: voltage, temperature, signal_strength
        # Use defaults if missing to maintain feature vector consistency
        voltage = telemetry_data.get("voltage", 5.0)
        temp = telemetry_data.get("temperature", 25.0)
        signal = telemetry_data.get("signal_strength", -50.0)

        features = np.array([[voltage, temp, signal]])

        if not self.is_fitted:
            # Fallback if not initialized
            return False

        prediction = self.model.predict(features)
        # -1 for anomaly, 1 for normal
        return prediction[0] == -1

    def classify_fault(self, telemetry_data: Dict[str, float]) -> str:
        """
        Simple rule-based classification based on telemetry values.
        """
        if telemetry_data.get("voltage", 5.0) < 3.0:
            return "Low Voltage"
        if telemetry_data.get("temperature", 25.0) > 80.0:
            return "Overheating"
        if telemetry_data.get("signal_strength", -50) < -100:
            return "Signal Loss"

        return "Unknown Anomaly"

    def recommend_recovery_action(self, fault_type: str) -> str:
        if fault_type == "Low Voltage":
            return "Switch to Safe Mode"
        if fault_type == "Overheating":
            return "Shutdown non-essential systems"
        if fault_type == "Signal Loss":
            return "Reorient Antenna"
        return "Monitor closely"

    async def log_anomaly(self, db: AsyncSession, satellite_id: int, severity: str, description: str, recommended_action: str) -> AnomalyLog:
        anomaly = AnomalyLog(
            satellite_id=satellite_id,
            severity=severity,
            description=description,
            timestamp=datetime.datetime.utcnow(),
            recommended_action=recommended_action
        )
        db.add(anomaly)
        await db.commit()
        await db.refresh(anomaly)
        return anomaly
