from .sensor import Sensor
from common.voting import VotingSystem

class ReactorMonitor:
    """
    Monitors a critical reactor parameter using 4 redundant sensors.
    """
    def __init__(self, parameter_name: str, threshold: float):
        self.parameter_name = parameter_name
        self.threshold = threshold
        # Initialize 4 redundant sensors
        self.sensors = [Sensor(f"{parameter_name}_S{i+1}", parameter_name) for i in range(4)]
        self.voting_system = VotingSystem()

    def update_sensors(self, true_value: float):
        """Updates the true value for all sensors (simulating real-time data)."""
        for sensor in self.sensors:
            sensor.set_value(true_value)

    def check_safety_status(self) -> bool:
        """
        Reads all sensors, compares against threshold, and votes.
        Returns True if safety action (SCRAM) is required (2-out-of-4 logic).
        """
        readings = [sensor.read() for sensor in self.sensors]
        trip_signals = [value > self.threshold for value in readings]

        # In a real system, this would log to the recording system.

        return self.voting_system.two_out_of_four(trip_signals)
