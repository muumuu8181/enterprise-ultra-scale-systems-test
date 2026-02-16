import unittest
from common.voting import VotingSystem

class TestVotingSystem(unittest.TestCase):
    def setUp(self):
        self.voting = VotingSystem()

    def test_no_trip(self):
        self.assertFalse(self.voting.two_out_of_four([False, False, False, False]))

    def test_one_trip(self):
        self.assertFalse(self.voting.two_out_of_four([True, False, False, False]))

    def test_two_trip(self):
        self.assertTrue(self.voting.two_out_of_four([True, True, False, False]))

    def test_three_trip(self):
        self.assertTrue(self.voting.two_out_of_four([True, True, True, False]))

    def test_four_trip(self):
        self.assertTrue(self.voting.two_out_of_four([True, True, True, True]))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            self.voting.two_out_of_four([True, True])
