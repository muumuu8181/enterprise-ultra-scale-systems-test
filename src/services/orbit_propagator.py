from sgp4.api import Satrec, jday
import datetime
import numpy as np
from typing import List, Dict, Any, Tuple

class OrbitPropagator:
    def __init__(self):
        # Earth constants (WGS84)
        self.a = 6378.137  # Semi-major axis (km)
        self.f = 1/298.257223563  # Flattening
        self.e2 = self.f * (2 - self.f)  # Eccentricity squared

    def calculate_position(self, tle_line1: str, tle_line2: str, timestamp: datetime.datetime) -> Dict[str, Any]:
        """
        Calculate position and velocity using SGP4 algorithm (TEME frame).
        """
        satellite = Satrec.twoline2rv(tle_line1, tle_line2)
        jd, fr = jday(timestamp.year, timestamp.month, timestamp.day,
                      timestamp.hour, timestamp.minute, timestamp.second)
        e, r, v = satellite.sgp4(jd, fr)

        if e != 0:
            raise ValueError(f"SGP4 propagation error code: {e}")

        return {
            "position": r,
            "velocity": v,
            "timestamp": timestamp
        }

    def _calculate_gmst(self, jd: float, fr: float) -> float:
        """
        Calculate Greenwich Mean Sidereal Time (GMST) in radians.
        Using the algorithm from 'Revisiting Spacetrack Report #3'.
        """
        t = (jd + fr - 2451545.0) / 36525.0
        gmst = 67310.54841 + (876600 * 3600 + 8640184.812866) * t + 0.093104 * t**2 - 6.2e-6 * t**3
        # Convert seconds to radians (modulo 86400 seconds in a day)
        gmst = (gmst % 86400.0) / 240.0 * np.pi / 180.0 # 240 seconds per degree
        return gmst

    def _teme_to_ecef(self, r_teme: Tuple[float, float, float], gmst: float) -> np.ndarray:
        """
        Convert TEME coordinates to ECEF (approximate).
        """
        x, y, z = r_teme
        theta = gmst

        # Simple Z-rotation
        x_ecef = x * np.cos(theta) + y * np.sin(theta)
        y_ecef = -x * np.sin(theta) + y * np.cos(theta)
        z_ecef = z

        return np.array([x_ecef, y_ecef, z_ecef])

    def _lla_to_ecef(self, lat: float, lon: float, alt: float) -> np.ndarray:
        """
        Convert Latitude, Longitude, Altitude to ECEF coordinates.
        lat, lon in degrees, alt in meters.
        """
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)
        alt_km = alt / 1000.0

        N = self.a / np.sqrt(1 - self.e2 * np.sin(lat_rad)**2)

        x = (N + alt_km) * np.cos(lat_rad) * np.cos(lon_rad)
        y = (N + alt_km) * np.cos(lat_rad) * np.sin(lon_rad)
        z = (N * (1 - self.e2) + alt_km) * np.sin(lat_rad)

        return np.array([x, y, z])

    def _calculate_elevation(self, sat_ecef: np.ndarray, station_ecef: np.ndarray, lat: float, lon: float) -> float:
        """
        Calculate elevation angle of satellite from ground station.
        """
        # Vector from station to satellite
        rho_ecef = sat_ecef - station_ecef

        # Convert to ENU (East-North-Up)
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)

        slat = np.sin(lat_rad)
        clat = np.cos(lat_rad)
        slon = np.sin(lon_rad)
        clon = np.cos(lon_rad)

        dx, dy, dz = rho_ecef

        # Up component
        z = clat * clon * dx + clat * slon * dy + slat * dz

        range_rho = np.linalg.norm(rho_ecef)
        elevation = np.arcsin(z / range_rho)

        return np.degrees(elevation)

    def predict_access_windows(self, tle_line1: str, tle_line2: str,
                               station_lat: float, station_lon: float, station_alt: float, min_elevation: float,
                               start_time: datetime.datetime, end_time: datetime.datetime) -> List[Dict[str, Any]]:
        """
        Predict visibility windows for a ground station using geometric calculations.
        Sampling interval: 1 minute.
        """
        try:
            satellite = Satrec.twoline2rv(tle_line1, tle_line2)
        except Exception:
            return []

        station_ecef = self._lla_to_ecef(station_lat, station_lon, station_alt)

        windows = []
        in_window = False
        window_start = None
        max_el = -90.0

        current_time = start_time
        while current_time <= end_time:
            jd, fr = jday(current_time.year, current_time.month, current_time.day,
                          current_time.hour, current_time.minute, current_time.second)
            e, r, v = satellite.sgp4(jd, fr)

            if e == 0:
                gmst = self._calculate_gmst(jd, fr)
                sat_ecef = self._teme_to_ecef(r, gmst)
                elevation = self._calculate_elevation(sat_ecef, station_ecef, station_lat, station_lon)

                if elevation >= min_elevation:
                    if not in_window:
                        in_window = True
                        window_start = current_time
                        max_el = elevation
                    else:
                        max_el = max(max_el, elevation)
                else:
                    if in_window:
                        in_window = False
                        windows.append({
                            "start_time": window_start,
                            "end_time": current_time,
                            "max_elevation": max_el
                        })
                        max_el = -90.0

            current_time += datetime.timedelta(minutes=1)

        if in_window:
             windows.append({
                "start_time": window_start,
                "end_time": end_time,
                "max_elevation": max_el
            })

        return windows

    def detect_collision_risk(self, tle1_1: str, tle1_2: str, tle2_1: str, tle2_2: str,
                              start_time: datetime.datetime, duration_minutes: int = 60) -> float:
        """
        Detect minimal distance between two satellites over a time window.
        """
        sat1 = Satrec.twoline2rv(tle1_1, tle1_2)
        sat2 = Satrec.twoline2rv(tle2_1, tle2_2)

        min_distance = float('inf')

        for i in range(duration_minutes):
            t = start_time + datetime.timedelta(minutes=i)
            jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)

            e1, r1, v1 = sat1.sgp4(jd, fr)
            e2, r2, v2 = sat2.sgp4(jd, fr)

            if e1 == 0 and e2 == 0:
                dist = np.linalg.norm(np.array(r1) - np.array(r2))
                if dist < min_distance:
                    min_distance = dist

        return float(min_distance)
