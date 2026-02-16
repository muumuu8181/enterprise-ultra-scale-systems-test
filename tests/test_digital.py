import unittest
from datetime import date, datetime, timedelta
from distribution.models import Movie, Theater
from digital.models import DCP, KDM

class TestDigital(unittest.TestCase):
    def test_dcp_creation(self):
        movie = Movie("Inception", date(2010, 7, 16), "PG-13", "Warner Bros.")
        dcp = DCP(
            movie=movie,
            version="v1.0",
            size_gb=150.5
        )
        self.assertEqual(dcp.movie, movie)
        self.assertEqual(dcp.version, "v1.0")
        self.assertEqual(dcp.format, "JPEG 2000")
        self.assertTrue(dcp.encrypted)
        self.assertEqual(dcp.size_gb, 150.5)

    def test_kdm_validity(self):
        movie = Movie("Inception", date(2010, 7, 16), "PG-13", "Warner Bros.")
        theater = Theater("AMC Empire 25", "New York, NY", 300)
        dcp = DCP(movie, "v1.0")

        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=1)

        kdm = KDM(
            dcp=dcp,
            theater=theater,
            valid_from=start_time,
            valid_until=end_time,
            uuid="1234-5678-90AB-CDEF"
        )

        self.assertTrue(kdm.is_valid())
        self.assertFalse(kdm.is_valid(start_time - timedelta(minutes=1)))
        self.assertFalse(kdm.is_valid(end_time + timedelta(minutes=1)))

if __name__ == '__main__':
    unittest.main()
