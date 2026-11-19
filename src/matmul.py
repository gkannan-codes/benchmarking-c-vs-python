"""
matmul.py — naive matrix multiplication benchmark (Python version)

Usage:   python3 matmul.py <N> <reps> [impl]
  N      matrix dimension
  reps   number of timed repetitions (one untimed warm-up run first)
  impl   "pure"  (default) triple loop over lists of lists — same algorithm as matmul.c
         "numpy" NumPy's A @ B (calls an optimized BLAS library written in C/assembly)

Output:  one line per repetition:  <seconds> <checksum>

Design notes:
  - time.perf_counter() is Python's highest-resolution monotonic clock — the
    equivalent of clock_gettime(CLOCK_MONOTONIC) in C. time.time() can jump if
    the system clock changes, so it's the wrong tool for benchmarking.
  - The matrices are filled with exactly the same values as matmul.c so both
    programs do identical arithmetic (we verify with the checksum).
  - Only the multiply is timed, not interpreter startup or matrix creation.
"""
import sys
import time


def fill(n, seed):
    return [[((i * 31 + j * 17 + seed) % 100) / 10.0 for j in range(n)] for i in range(n)]


def matmul_pure(A, B, n):
    # Same i-j-k order and same work as the C version.
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        Ai = A[i]
        Ci = C[i]
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += Ai[k] * B[k][j]
            Ci[j] = s
    return C


def main():
    if len(sys.argv) < 3:
        print("usage: matmul.py N reps [pure|numpy]", file=sys.stderr)
        sys.exit(1)
    n, reps = int(sys.argv[1]), int(sys.argv[2])
    impl = sys.argv[3] if len(sys.argv) > 3 else "pure"

    if impl == "numpy":
        import numpy as np
        A = np.array(fill(n, 1))
        B = np.array(fill(n, 2))
        mm = lambda: A @ B
        checksum = lambda C: float(C.sum())
    else:
        A, B = fill(n, 1), fill(n, 2)
        mm = lambda: matmul_pure(A, B, n)
        checksum = lambda C: sum(map(sum, C))

    mm()  # warm-up run (not timed)

    for _ in range(reps):
        t0 = time.perf_counter()
        C = mm()
        t1 = time.perf_counter()
        print(f"{t1 - t0:.9f} {checksum(C):.6f}")


if __name__ == "__main__":
    main()
