from datetime import datetime, timezone

class MisbehaviorDetector:
    """
    Service for detecting V2X misbehaviors and calculating trust scores.
    """
    def __init__(self):
        # Configuration thresholds
        self.max_speed_diff = 10.0 # m/s
        self.max_timestamp_diff = 5.0 # seconds
        self.trust_score_initial = 100.0

    def detect_position_spoofing(self, vehicle_data: dict) -> bool:
        """
        Detects position spoofing based on physical constraints.

        Args:
            vehicle_data (dict): Dictionary containing vehicle data like speed, location.

        Returns:
            bool: True if spoofing detected, False otherwise.
        """
        # Simplified logic: Check if speed is physically possible (e.g., > 300 m/s)
        current_speed = vehicle_data.get("speed", 0.0)
        if current_speed > 300.0: # Impossible speed > 300 m/s (approx 1080 km/h)
             return True
        return False

    def detect_replay_attack(self, message_timestamp: datetime) -> bool:
        """
        Detects replay attacks by checking timestamp validity.

        Args:
            message_timestamp (datetime): Timestamp from the received message.

        Returns:
            bool: True if replay attack detected (timestamp too old), False otherwise.
        """
        current_time = datetime.now(timezone.utc)

        # Ensure message_timestamp is timezone aware
        if message_timestamp.tzinfo is None:
            message_timestamp = message_timestamp.replace(tzinfo=timezone.utc)

        diff = abs((current_time - message_timestamp).total_seconds())
        return diff > self.max_timestamp_diff

    def detect_sybil_attack(self, reports: list) -> bool:
        """
        Detects Sybil attacks (multiple identities from same source).

        Args:
            reports (list): List of recent reports/messages from various vehicles.

        Returns:
            bool: True if Sybil attack detected, False otherwise.
        """
        # Simplified logic: Check if multiple IDs report from exact same location/time
        locations = set()
        for r in reports:
            # Assuming r is a dict or object with latitude, longitude, timestamp
            if isinstance(r, dict):
                lat = r.get("latitude")
                lon = r.get("longitude")
                ts = r.get("timestamp")
            else:
                lat = getattr(r, "latitude", None)
                lon = getattr(r, "longitude", None)
                ts = getattr(r, "timestamp", None)

            if lat is None or lon is None:
                continue

            loc_key = (lat, lon, ts)
            if loc_key in locations:
                return True
            locations.add(loc_key)
        return False

    def calculate_trust_score(self, vehicle_id: str, reports: list) -> float:
        """
        Calculates the trust score for a vehicle based on its misbehavior history.

        Args:
            vehicle_id (str): ID of the vehicle.
            reports (list): List of MisbehaviorReport objects associated with the vehicle.

        Returns:
            float: Trust score between 0.0 and 100.0.
        """
        score = self.trust_score_initial

        for report in reports:
            # Determine impact based on attack_type
            # Handle both dict and object access
            if isinstance(report, dict):
                attack_type = report.get("attack_type")
            else:
                attack_type = getattr(report, "attack_type", "unknown")

            if attack_type == "spoofing":
                score -= 20.0
            elif attack_type == "replay":
                score -= 10.0
            elif attack_type == "sybil":
                score -= 30.0
            else:
                score -= 5.0

        return max(0.0, min(100.0, score))
