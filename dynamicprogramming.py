"""Minimum Set Cover using Dynamic Programming
   By Jayden Tan
   This implementation uses a recursive approach with memoization to find the minimum set cover.
   The algorithm explores all possible combinations of subsets to find the optimal solution.
"""
# python3 -m setcover solve -a dynamicprogramming STS9 --show 

from functools import lru_cache     # lru_cache is used for memoization to optimize the recursive function.
from .base import Algorithm, register

@register
class DynamicProgrammingSetCover(Algorithm):
    name = "dynamicprogramming"     # name used to identify the algorithm in the command line interface
    exact = True                    # exact = True indicates that this algorithm finds the optimal solution.

    def solve(self, instance, ctx):
        universe = frozenset(range(instance.n))     # the set of all elements that need to be covered, represented as a frozenset for immutability and hashing.
        subsets = [frozenset(s) for s in instance.subsets]      # the available subsets, stored as frozensets for immutability and hashing.

        @lru_cache(maxsize=None)        # stores each result 
        def dp(covered):
            ctx.check_time()
            if covered == universe:     # all elements are covered, so no more subsets are needed.
                return 0
            
            best = float("inf")         # initialize best to infinity, representing the worst case where no valid cover is found.
            for s in subsets:
                if not s <= covered:
                    best = min(best, 1 + dp(covered | s))        
            return best

        optimum = dp(frozenset())       # compute the minimum number of subsets needed to cover the universe starting from an empty set of covered elements.
        if optimum == float("inf"):
            raise ValueError("No valid cover exists for the given instance.")

        # rebuild the solution
        selected, covered = [], frozenset()
        while covered != universe:
            for j, s in enumerate(subsets):
                if not s <= covered and 1 + dp(covered | s) == dp(covered):     # if adding subset s leads to the optimal solution, select it and update the covered elements.
                    selected.append(j)
                    covered = covered | s
                    break

        ctx.stats["dp_states"] = dp.cache_info().currsize
        ctx.stats["optimal_size"] = optimum
        return selected