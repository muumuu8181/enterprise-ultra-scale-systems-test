class TelemetryMonitor:
    def __init__(self):
        self.thresholds = {}

    def set_threshold(self, key, min_val=None, max_val=None):
        """
        Set monitoring thresholds for a telemetry key.
        :param key: Telemetry key (e.g., "battery_voltage")
        :param min_val: Minimum allowed value (optional)
        :param max_val: Maximum allowed value (optional)
        """
        self.thresholds[key] = {'min': min_val, 'max': max_val}

    def check(self, telemetry_data):
        """
        Check telemetry data for anomalies.
        :param telemetry_data: Dictionary of telemetry values
        :return: List of anomaly descriptions
        """
        anomalies = []
        for key, value in telemetry_data.items():
            if key in self.thresholds:
                limits = self.thresholds[key]
                if limits['min'] is not None and value < limits['min']:
                    anomalies.append(f"Anomaly: {key} value {value} is below minimum {limits['min']}")
                if limits['max'] is not None and value > limits['max']:
                    anomalies.append(f"Anomaly: {key} value {value} is above maximum {limits['max']}")
        return anomalies
