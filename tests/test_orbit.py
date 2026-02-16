import unittest
import math
import sys
import os

# Add src to path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from orbit.propagator import KeplerianElements, KeplerianPropagator

class TestKeplerianPropagator(unittest.TestCase):

    def test_circular_orbit_period(self):
        # Geostationary-like orbit parameters
        a = 42164.0  # km
        e = 0.0
        i = 0.0
        omega = 0.0
        w = 0.0
        M0 = 0.0

        elements = KeplerianElements(a, e, i, omega, w, M0)
        propagator = KeplerianPropagator(elements)

        # Calculate expected period: T = 2*pi * sqrt(a^3/mu)
        mu = KeplerianPropagator.MU_EARTH
        period = 2 * math.pi * math.sqrt(a**3 / mu)

        # Propagate for one full period
        pos = propagator.propagate(period)

        # Expected position at t=T is same as t=0 (a, 0, 0)
        # Allow small tolerance due to floating point arithmetic
        self.assertAlmostEqual(pos[0], a, delta=1.0)  # Check X
        self.assertAlmostEqual(pos[1], 0.0, delta=1.0) # Check Y
        self.assertAlmostEqual(pos[2], 0.0, delta=1.0) # Check Z

    def test_half_period_position(self):
        # Circular orbit
        a = 10000.0
        e = 0.0
        i = 0.0
        omega = 0.0
        w = 0.0
        M0 = 0.0

        elements = KeplerianElements(a, e, i, omega, w, M0)
        propagator = KeplerianPropagator(elements)

        mu = KeplerianPropagator.MU_EARTH
        period = 2 * math.pi * math.sqrt(a**3 / mu)

        # Propagate for half period
        pos = propagator.propagate(period / 2.0)

        # Expected position at t=T/2 is (-a, 0, 0)
        self.assertAlmostEqual(pos[0], -a, delta=1.0)
        self.assertAlmostEqual(pos[1], 0.0, delta=1.0)
        self.assertAlmostEqual(pos[2], 0.0, delta=1.0)

    def test_inclined_orbit(self):
        # 90 degree inclination (Polar Orbit)
        a = 10000.0
        e = 0.0
        i = math.pi / 2.0  # 90 degrees
        omega = 0.0
        w = 0.0
        M0 = 0.0

        elements = KeplerianElements(a, e, i, omega, w, M0)
        propagator = KeplerianPropagator(elements)

        mu = KeplerianPropagator.MU_EARTH
        period = 2 * math.pi * math.sqrt(a**3 / mu)

        # Propagate for 1/4 period (should be at North Pole roughly?)
        # At M = pi/2 (90 deg), true anomaly nu = 90 deg.
        # Position in orbital plane: (0, a, 0).
        # Rotate by i=90 around X:
        # y' = y*cos(90) - z*sin(90) = 0
        # z' = y*sin(90) + z*cos(90) = a
        # So expected ECI is (0, 0, a)

        pos = propagator.propagate(period / 4.0)

        self.assertAlmostEqual(pos[0], 0.0, delta=1.0)
        self.assertAlmostEqual(pos[1], 0.0, delta=1.0)
        self.assertAlmostEqual(pos[2], a, delta=1.0)

if __name__ == '__main__':
    unittest.main()
