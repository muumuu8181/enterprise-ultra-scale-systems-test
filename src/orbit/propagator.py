import math

class KeplerianElements:
    """
    Keplerian orbital elements.
    """
    def __init__(self, a, e, i, omega, w, M0, epoch=0.0):
        """
        :param a: Semi-major axis (km)
        :param e: Eccentricity
        :param i: Inclination (rad)
        :param omega: Longitude of ascending node (rad)
        :param w: Argument of periapsis (rad)
        :param M0: Mean anomaly at epoch (rad)
        :param epoch: Reference time (seconds)
        """
        self.a = a
        self.e = e
        self.i = i
        self.omega = omega
        self.w = w
        self.M0 = M0
        self.epoch = epoch

class KeplerianPropagator:
    """
    Propagator for Keplerian orbits (Two-Body Problem).
    """
    MU_EARTH = 398600.4418  # km^3/s^2

    def __init__(self, elements):
        self.elements = elements
        self.n = math.sqrt(self.MU_EARTH / (self.elements.a ** 3))

    def propagate(self, time_delta):
        """
        Propagate the orbit by a time delta.
        :param time_delta: Time since epoch (seconds)
        :return: Position (x, y, z) in ECI frame (km)
        """
        # Calculate new Mean Anomaly
        M_t = self.elements.M0 + self.n * time_delta

        # Solve Kepler's Equation for Eccentric Anomaly (E) using Newton-Raphson
        E = self._solve_kepler(M_t, self.elements.e)

        # Calculate True Anomaly (nu)
        sqrt_1_e2 = math.sqrt(1 - self.elements.e**2)
        sin_E = math.sin(E)
        cos_E = math.cos(E)

        # Calculate radius distance (r) and position in orbital plane
        # r = a * (1 - e * cos(E))
        # x_orb = r * cos(nu)
        # y_orb = r * sin(nu)

        # Alternatively, using E directly:
        x_orb = self.elements.a * (cos_E - self.elements.e)
        y_orb = self.elements.a * sqrt_1_e2 * sin_E

        # Rotate to ECI frame
        # Apply rotations for argument of periapsis (w), inclination (i), and RAAN (omega)
        cos_w = math.cos(self.elements.w)
        sin_w = math.sin(self.elements.w)
        cos_i = math.cos(self.elements.i)
        sin_i = math.sin(self.elements.i)
        cos_omega = math.cos(self.elements.omega)
        sin_omega = math.sin(self.elements.omega)

        # Position in PQW frame (Perifocal)
        # P = [cos_w, sin_w, 0]
        # Q = [-sin_w * cos_i, cos_w * cos_i, sin_i]
        # This is simpler to just apply the rotation matrices sequentially

        # 1. Rotate by argument of periapsis (w) about Z axis
        x1 = x_orb * cos_w - y_orb * sin_w
        y1 = x_orb * sin_w + y_orb * cos_w
        z1 = 0.0

        # 2. Rotate by inclination (i) about X axis
        x2 = x1
        y2 = y1 * cos_i
        z2 = y1 * sin_i

        # 3. Rotate by RAAN (omega) about Z axis
        x_eci = x2 * cos_omega - y2 * sin_omega
        y_eci = x2 * sin_omega + y2 * cos_omega
        z_eci = z2

        return (x_eci, y_eci, z_eci)

    def _solve_kepler(self, M, e, tolerance=1e-6):
        """
        Solves Kepler's Equation M = E - e*sin(E) for E.
        """
        E = M  # Initial guess
        while True:
            delta_E = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
            E -= delta_E
            if abs(delta_E) < tolerance:
                break
        return E
