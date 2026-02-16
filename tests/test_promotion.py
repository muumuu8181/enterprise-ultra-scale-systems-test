import unittest
from datetime import date
from promotion.models import PromotionType, PromotionMaterial, PromotionCost

class TestPromotion(unittest.TestCase):
    def test_promotion_material(self):
        material = PromotionMaterial(
            title="Inception Trailer 1",
            type=PromotionType.TRAILER,
            url="http://example.com/trailer.mp4"
        )
        self.assertEqual(material.title, "Inception Trailer 1")
        self.assertEqual(material.type, PromotionType.TRAILER)
        self.assertEqual(material.url, "http://example.com/trailer.mp4")

    def test_promotion_cost(self):
        cost = PromotionCost(
            title="TV CM Campaign",
            type=PromotionType.TV_CM,
            cost=50000.0,
            date=date(2010, 7, 10)
        )
        self.assertEqual(cost.title, "TV CM Campaign")
        self.assertEqual(cost.type, PromotionType.TV_CM)
        self.assertEqual(cost.cost, 50000.0)
        self.assertEqual(cost.date, date(2010, 7, 10))

if __name__ == '__main__':
    unittest.main()
