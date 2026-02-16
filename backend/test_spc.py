import unittest
from spc import calculate_cpk, generate_control_chart_data

class TestSPC(unittest.TestCase):
    def test_cpk_calculation(self):
        # Test case: perfect centering
        data = [10.0, 10.0, 10.0, 10.0, 10.0]
        # std=0, should handle gracefully or return 0 (my implementation returns 0)
        self.assertEqual(calculate_cpk(data, 12, 8), 0.0)

        # Test case: normal distribution
        # Mean ~ 100, Std ~ 2
        data = [98, 102, 100, 99, 101]
        cpk = calculate_cpk(data, 106, 94)
        self.assertTrue(cpk > 0)
        print(f"Calculated Cpk: {cpk}")

    def test_chart_generation(self):
        result = generate_control_chart_data("temp")
        self.assertEqual(result["parameter"], "temp")
        self.assertTrue("cpk" in result)
        self.assertTrue(len(result["data"]) == 20)

if __name__ == "__main__":
    unittest.main()
