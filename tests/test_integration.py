import unittest
from process_monitoring.reactor_monitor import ReactorMonitor
from safety_protection.scram_system import ScramSystem

class TestIntegration(unittest.TestCase):
    def test_scram_activates_on_high_temp(self):
        monitor = ReactorMonitor("TestTemp", threshold=100.0)
        scram = ScramSystem()

        # Normal Op (Below threshold)
        monitor.update_sensors(90.0)
        is_tripped = monitor.check_safety_status()
        self.assertFalse(is_tripped, "Should not trip under normal conditions")

        # Fault: High Temp (Above threshold)
        # Note: update_sensors sets the 'physical' value.
        # The sensors read this value (with noise), but 110.0 vs 100.0 is enough gap to overcome small noise.
        monitor.update_sensors(110.0)
        is_tripped = monitor.check_safety_status()
        self.assertTrue(is_tripped, "Should trip when temp exceeds threshold")

        scram.evaluate_monitors({"TestTemp": is_tripped})
        self.assertTrue(scram.scram_active, "SCRAM system should be active after trip")

    def test_single_sensor_fault_does_not_trip(self):
        # Test the redundancy: 1 sensor fails high, but true value is low.
        monitor = ReactorMonitor("TestPressure", threshold=100.0)

        monitor.update_sensors(50.0) # Normal pressure

        # Inject fault into ONE sensor
        monitor.sensors[0].inject_fault(150.0) # High value

        is_tripped = monitor.check_safety_status()
        self.assertFalse(is_tripped, "Single sensor fault should not trigger trip (2-out-of-4 logic)")

    def test_two_sensor_fault_trips(self):
        # Test the redundancy: 2 sensors fail high
        monitor = ReactorMonitor("TestFlux", threshold=100.0)
        monitor.update_sensors(50.0)

        monitor.sensors[0].inject_fault(150.0)
        monitor.sensors[1].inject_fault(150.0)

        is_tripped = monitor.check_safety_status()
        self.assertTrue(is_tripped, "Two sensor faults should trigger trip")
