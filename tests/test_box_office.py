import unittest
from datetime import date
from distribution.models import Movie, Theater, ScreeningContract
from box_office.models import DailyRevenue, Settlement

class TestBoxOffice(unittest.TestCase):
    def test_daily_revenue_calculation(self):
        movie = Movie("Inception", date(2010, 7, 16), "PG-13", "Warner Bros.")
        theater = Theater("AMC Empire 25", "New York, NY", 300)
        contract = ScreeningContract(
            movie=movie,
            theater=theater,
            revenue_share_percentage=60.0
        )

        daily_revenue = DailyRevenue(
            date=date(2010, 7, 16),
            theater=theater,
            movie=movie,
            gross_revenue=10000.0,
            attendance=500
        )

        share = daily_revenue.calculate_distributor_share(contract)
        # Expected share: 10000 * 0.6 = 6000
        self.assertEqual(share, 6000.0)

    def test_settlement_calculation(self):
        movie = Movie("Inception", date(2010, 7, 16), "PG-13", "Warner Bros.")
        theater = Theater("AMC Empire 25", "New York, NY", 300)
        contract = ScreeningContract(
            movie=movie,
            theater=theater,
            revenue_share_percentage=50.0,
            minimum_guarantee=15000.0  # MG is 15000
        )

        daily_revenue_1 = DailyRevenue(date(2010, 7, 16), theater, movie, 10000.0, 500)
        daily_revenue_2 = DailyRevenue(date(2010, 7, 17), theater, movie, 12000.0, 600)

        settlement = Settlement(
            contract=contract,
            daily_revenues=[daily_revenue_1, daily_revenue_2]
        )

        total_share = settlement.calculate_total_distributor_share()

        # Share 1: 10000 * 0.5 = 5000
        # Share 2: 12000 * 0.5 = 6000
        # Total Share: 11000
        # MG: 15000
        # Expected: 15000
        self.assertEqual(total_share, 15000.0)

    def test_settlement_calculation_exceeds_mg(self):
        movie = Movie("Inception", date(2010, 7, 16), "PG-13", "Warner Bros.")
        theater = Theater("AMC Empire 25", "New York, NY", 300)
        contract = ScreeningContract(
            movie=movie,
            theater=theater,
            revenue_share_percentage=50.0,
            minimum_guarantee=10000.0  # MG is 10000
        )

        daily_revenue_1 = DailyRevenue(date(2010, 7, 16), theater, movie, 10000.0, 500)
        daily_revenue_2 = DailyRevenue(date(2010, 7, 17), theater, movie, 12000.0, 600)

        settlement = Settlement(
            contract=contract,
            daily_revenues=[daily_revenue_1, daily_revenue_2]
        )

        total_share = settlement.calculate_total_distributor_share()

        # Share 1: 10000 * 0.5 = 5000
        # Share 2: 12000 * 0.5 = 6000
        # Total Share: 11000
        # MG: 10000
        # Expected: 11000
        self.assertEqual(total_share, 11000.0)

if __name__ == '__main__':
    unittest.main()
