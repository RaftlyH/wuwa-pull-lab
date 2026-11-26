import unittest
import numpy as np
from rules import Rules, maximum_pulls
from simulator import simulate
from analysis import exact_cdf

class ProbabilityTests(unittest.TestCase):
    def test_first_pull(self):
        self.assertAlmostEqual(exact_cdf(Rules())[1], .004)
        self.assertAlmostEqual(exact_cdf(Rules(), guaranteed=True)[1], .008)

    def test_hard_pity(self):
        self.assertAlmostEqual(exact_cdf(Rules(), pity=79, guaranteed=True)[1], 1)
        self.assertAlmostEqual(exact_cdf(Rules(), pity=79)[1], .5)
        self.assertTrue(np.all(simulate(Rules(), 79, True, runs=100) == 1))

    def test_bounds_and_monotonicity(self):
        for soft in [False, True]:
            for guarantee in [False, True]:
                for copies in [1, 3, 7]:
                    cdf = exact_cdf(Rules(soft), 35, guarantee, copies)
                    self.assertTrue(np.all(np.diff(cdf) >= -1e-12))
                    self.assertAlmostEqual(cdf[-1], 1)
                    self.assertEqual(len(cdf)-1, maximum_pulls(35, guarantee, copies))

    def test_monte_carlo_matches_exact(self):
        for soft in [False, True]:
            times = simulate(Rules(soft), 35, False, 2, 30000, 123)
            cdf = exact_cdf(Rules(soft), 35, False, 2)
            for budget in [1, 60, 100, 160, 240]:
                observed = np.mean(times[:, -1] <= budget)
                self.assertLess(abs(observed - cdf[budget]), .015)
            self.assertTrue(np.all(np.diff(times, axis=1) > 0))

    def test_reproducible(self):
        np.testing.assert_array_equal(simulate(Rules(), runs=100), simulate(Rules(), runs=100))

    def test_invalid_pity(self):
        with self.assertRaises(ValueError):
            exact_cdf(Rules(), pity=80)

if __name__ == '__main__':
    unittest.main()
