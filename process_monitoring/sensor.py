import random

class Sensor:
    """
    Simulates a sensor reading process values.
    """
    def __init__(self, sensor_id: str, measurement_type: str):
        self.sensor_id = sensor_id
        self.measurement_type = measurement_type
        self.value = 0.0
        self.fault_active = False
        self.fault_value = 0.0

    def set_value(self, value: float):
        """Sets the true physical value being measured."""
        self.value = value

    def inject_fault(self, value: float):
        """Forces the sensor to output a specific value (simulating a fault)."""
        self.fault_active = True
        self.fault_value = value

    def clear_fault(self):
        """Clears any injected faults, returning to normal operation."""
        self.fault_active = False

    def read(self) -> float:
        """
        Reads the current value.
        Includes simulated noise if operating normally.
        Returns the fault value if a fault is active.
        """
        if self.fault_active:
            return self.fault_value

        # Add a tiny bit of noise for realism (e.g., +/- 0.5%)
        noise = self.value * random.uniform(-0.005, 0.005)
        return self.value + noise
