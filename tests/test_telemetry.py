import unittest
import sys
import os

# Add src to path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from telemetry.monitor import TelemetryMonitor

class TestTelemetryMonitor(unittest.TestCase):

    def test_threshold_check(self):
        monitor = TelemetryMonitor()
        monitor.set_threshold('voltage', min_val=3.0, max_val=4.2)

        # Test normal
        anomalies = monitor.check({'voltage': 3.7})
        self.assertEqual(len(anomalies), 0)

        # Test low
        anomalies = monitor.check({'voltage': 2.8})
        self.assertEqual(len(anomalies), 1)
        self.assertIn('below minimum', anomalies[0])

        # Test high
        anomalies = monitor.check({'voltage': 4.5})
        self.assertEqual(len(anomalies), 1)
        self.assertIn('above maximum', anomalies[0])

    def test_multiple_keys(self):
        monitor = TelemetryMonitor()
        monitor.set_threshold('temp', min_val=-20, max_val=50)
        monitor.set_threshold('current', max_val=10)

        data = {'temp': 60, 'current': 12, 'voltage': 3.7}
        anomalies = monitor.check(data)

        self.assertEqual(len(anomalies), 2)
        self.assertTrue(any('temp' in a for a in anomalies))
        self.assertTrue(any('current' in a for a in anomalies))

if __name__ == '__main__':
    unittest.main()
