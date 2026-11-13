from itertools import combinations
import time

def brute_force_set_cover(universe, subsets):
    m = len(subsets)

    for k in range(m + 1):
        for indices in combinations(range(m), k):
            covered = set()

            for i in indices:
                covered.update(subsets[i])

            if covered == universe:
                return list(indices), k

    return None, None

def load_sts(filename):
    with open(filename, 'r') as file:
        numbers = list(map(int, file.read().split()))

    m = numbers[0]      # number of subsets
    n = numbers[1]      # size of the elements

    universe = set(range(1, n + 1))
    subsets = [set() for _ in range(m)]

    for element in range(n):
        start = 2 + element * 3
        triple = numbers[start:start + 3]

        for subset_index in triple:
            subsets[subset_index - 1].add(element + 1)

    return universe, subsets

U,S = load_sts("/Users/jayden/Desktop/MLDM/Semester_1/Advanced_Algorithms/Projects/Benchmarks/data.9")

start = time.perf_counter()     # starts measuring execution time

indices, size = brute_force_set_cover(U, S)     # runs the brute force algorithm

end = time.perf_counter()       # stops measuing execution time

print("Selected subsets:")      # displays results

for i in indices:
    print(f"S{i + 1}: {sorted(S[i])}")

print("Minimum cover size:", size)
print(f"Execution time: {end - start:.6f} seconds")