import unittest
from datetime import date, datetime
from distribution.models import Movie, Theater, ScreeningContract, ScreeningSchedule

class TestDistribution(unittest.TestCase):
    def test_movie_creation(self):
        movie = Movie(
            title="Inception",
            release_date=date(2010, 7, 16),
            rating="PG-13",
            distributor="Warner Bros."
        )
        self.assertEqual(movie.title, "Inception")
        self.assertEqual(movie.release_date, date(2010, 7, 16))
        self.assertEqual(movie.rating, "PG-13")
        self.assertEqual(movie.distributor, "Warner Bros.")

    def test_theater_creation(self):
        theater = Theater(
            name="AMC Empire 25",
            location="New York, NY",
            capacity=300
        )
        self.assertEqual(theater.name, "AMC Empire 25")
        self.assertEqual(theater.location, "New York, NY")
        self.assertEqual(theater.capacity, 300)

    def test_screening_contract(self):
        movie = Movie("Inception", date(2010, 7, 16), "PG-13", "Warner Bros.")
        theater = Theater("AMC Empire 25", "New York, NY", 300)
        contract = ScreeningContract(
            movie=movie,
            theater=theater,
            revenue_share_percentage=50.0,
            minimum_guarantee=10000.0
        )
        self.assertEqual(contract.movie, movie)
        self.assertEqual(contract.theater, theater)
        self.assertEqual(contract.revenue_share_percentage, 50.0)
        self.assertEqual(contract.minimum_guarantee, 10000.0)

    def test_screening_schedule(self):
        movie = Movie("Inception", date(2010, 7, 16), "PG-13", "Warner Bros.")
        theater = Theater("AMC Empire 25", "New York, NY", 300)
        showtimes = [
            datetime(2010, 7, 16, 10, 0),
            datetime(2010, 7, 16, 13, 0),
            datetime(2010, 7, 16, 16, 0)
        ]
        schedule = ScreeningSchedule(
            movie=movie,
            theater=theater,
            start_date=date(2010, 7, 16),
            end_date=date(2010, 7, 30),
            showtimes=showtimes
        )
        self.assertEqual(schedule.movie, movie)
        self.assertEqual(schedule.theater, theater)
        self.assertEqual(schedule.start_date, date(2010, 7, 16))
        self.assertEqual(schedule.end_date, date(2010, 7, 30))
        self.assertEqual(schedule.showtimes, showtimes)

if __name__ == '__main__':
    unittest.main()
