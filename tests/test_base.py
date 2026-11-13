"""Tests de la base commune. Lancer depuis la racine du dépôt :

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import itertools
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setcover import (Instance, Algorithm, generate, get_algorithm, is_cover, read_instance,
                      read_solution, run, verify, write_orlib, write_solution)
from setcover import benchmarks
from setcover.algorithms import TimeLimitExceeded

# n = 6, m = 4 : optimum = 2 ({0,1,2} + {3,4,5})
SMALL = Instance.from_subsets(6, [{0, 1, 2}, {2, 3}, {3, 4, 5}, {0, 5}], name="small")


def brute_force_optimum(inst: Instance) -> int:
    """Optimum by enumeration (tiny instances only), used as a test oracle."""
    for k in range(1, inst.m + 1):
        for comb in itertools.combinations(range(inst.m), k):
            if is_cover(inst, comb):
                return k
    raise ValueError("infaisable")


class TestInstance(unittest.TestCase):
    def test_derived(self):
        self.assertEqual(SMALL.covering[0], (0, 3))
        self.assertEqual(SMALL.masks[0], 0b000111)
        self.assertEqual(SMALL.full_mask, 0b111111)
        self.assertTrue(SMALL.is_feasible)
        self.assertAlmostEqual(SMALL.density, 10 / 24)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            Instance.from_subsets(3, [{0, 5}])

    def test_infeasible(self):
        inst = Instance.from_subsets(3, [{0}, {1}])
        self.assertEqual(inst.uncoverable, (2,))


class TestVerify(unittest.TestCase):
    def test_valid(self):
        v = verify(SMALL, [0, 2])
        self.assertTrue(v.feasible)
        self.assertEqual(v.cost, 2)
        self.assertEqual(v.redundant, [])

    def test_uncovered(self):
        v = verify(SMALL, [0, 1])
        self.assertFalse(v.feasible)
        self.assertEqual(v.uncovered, [4, 5])

    def test_invalid_and_duplicates(self):
        self.assertFalse(verify(SMALL, [0, 2, 9]).feasible)
        v = verify(SMALL, [0, 2, 2])
        self.assertTrue(v.feasible)
        self.assertEqual(v.cost, 2)
        self.assertEqual(v.duplicates, [2])

    def test_redundant(self):
        self.assertEqual(verify(SMALL, [0, 1, 2, 3]).redundant, [1, 3])


class TestIO(unittest.TestCase):
    def test_roundtrip(self):
        inst = generate(40, 25, 0.1, seed=3)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.txt")
            write_orlib(inst, p)
            back = read_instance(p)
            self.assertEqual(back.subsets, inst.subsets)
            write_solution([4, 1, 7], os.path.join(d, "x.sol"), comment="test")
            self.assertEqual(read_solution(os.path.join(d, "x.sol")), [1, 4, 7])


class TestGenerator(unittest.TestCase):
    def test_reproducible_and_feasible(self):
        a, b = generate(50, 30, 0.05, seed=7), generate(50, 30, 0.05, seed=7)
        self.assertEqual(a.subsets, b.subsets)
        self.assertNotEqual(a.subsets, generate(50, 30, 0.05, seed=8).subsets)
        self.assertTrue(a.is_feasible)
        self.assertTrue(all(a.subsets))

    def test_density(self):
        inst = generate(200, 200, 0.3, seed=1)
        self.assertAlmostEqual(inst.density, 0.3, delta=0.02)


class TestExample(unittest.TestCase):
    def test_small(self):
        res = run(get_algorithm("example"), SMALL)
        self.assertEqual(res.status, "ok")
        self.assertEqual(res.cost, SMALL.m)          # takes every subset
        self.assertEqual(res.stats["subsets_scanned"], SMALL.m)

    def test_bruteforce_solutions_are_verified(self):
        """verify() and is_cover() agree on optimal solutions of random instances."""
        for seed in range(15):
            inst = generate(12, 10, 0.25, seed=seed)
            opt = brute_force_optimum(inst)
            res = run(get_algorithm("example"), inst, known=opt, known_status="optimal")
            self.assertTrue(res.feasible)
            self.assertGreaterEqual(res.cost, opt)


class TestRunner(unittest.TestCase):
    def test_timeout_returns_incumbent(self):
        class Slow(Algorithm):
            name = "slow-test"

            def solve(self, inst, ctx):
                ctx.improve(range(inst.m))
                while True:
                    ctx.check_time()

        res = run(Slow(), SMALL, time_limit=0.05)
        self.assertEqual(res.status, "timeout")
        self.assertEqual(res.cost, 4)

    def test_infeasible_output_detected(self):
        class Bad(Algorithm):
            name = "bad-test"

            def solve(self, inst, ctx):
                return [0]

        self.assertEqual(run(Bad(), SMALL).status, "infeasible")


@unittest.skipUnless(os.path.isdir(benchmarks.DEFAULT_DIR), "dossier USPC-instances absent")
class TestBenchmarks(unittest.TestCase):
    def test_load_all_small(self):
        for b in benchmarks.list_benchmarks():
            if os.path.getsize(b.path) > 2_000_000:   # on saute les plus gros pour aller vite
                continue
            inst = b.load()
            self.assertTrue(inst.is_feasible, b.name)
            res = run(get_algorithm("example"), inst, known=b.known, known_status=b.status)
            self.assertTrue(res.feasible, b.name)
            self.assertEqual(res.cost, inst.m, b.name)


if __name__ == "__main__":
    unittest.main()
