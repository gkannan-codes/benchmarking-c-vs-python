"""
bench.py — benchmark harness: compiles the C code, runs every configuration
many times, checks that all versions agree, and writes results/results.csv.

Usage:   python3 bench.py            (full run, ~3-5 minutes)
         python3 bench.py --quick    (smaller sizes, fewer reps, ~30 s)

What it measures
  c_O0         matmul.c compiled with  gcc -O0   (no optimization)
  c_O2         matmul.c compiled with  gcc -O2   (standard optimization)
  c_O2_ikj     same, but loops reordered i-k-j (cache-friendly)
  py_pure      matmul.py, plain Python lists, same algorithm as C
  py_numpy     matmul.py using NumPy (A @ B), pinned to 1 thread for fairness

Each program does its own warm-up run and times only the multiply. We report
the MEDIAN of the repetitions (robust to the occasional slow outlier caused by
the OS scheduling something else) along with min, mean and standard deviation.
"""
import csv
import os
import platform
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
QUICK = "--quick" in sys.argv

# NumPy's BLAS backend may use several threads. Pin it to one so we compare
# one core vs one core. (Remove this line to see the multithreaded number.)
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def compile_c():
    for opt in ("O0", "O2"):
        subprocess.run(["gcc", f"-{opt}", "-o", os.path.join(HERE, f"matmul_{opt}"),
                        os.path.join(HERE, "matmul.c")], check=True)


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV).stdout
    times, checks = [], set()
    for line in out.strip().splitlines():
        t, c = line.split()
        times.append(float(t))
        checks.add(round(float(c), 2))
    return times, checks


IMPLS = ["c_O0", "c_O2", "c_O2_ikj", "py_pure", "py_numpy"]


def configs(n, reps):
    c = lambda opt: os.path.join(HERE, f"matmul_{opt}")
    py = [sys.executable, os.path.join(HERE, "matmul.py")]
    return {
        "c_O0":     [c("O0"), str(n), str(reps), "ijk"],
        "c_O2":     [c("O2"), str(n), str(reps), "ijk"],
        "c_O2_ikj": [c("O2"), str(n), str(reps), "ikj"],
        "py_pure":  py + [str(n), str(reps), "pure"],
        "py_numpy": py + [str(n), str(reps), "numpy"],
    }


def main():
    os.makedirs(RESULTS, exist_ok=True)
    compile_c()
    sizes = [32, 64, 128, 256] if QUICK else [64, 128, 256, 512, 1024]
    rows = []
    for n in sizes:
        checks_seen = set()
        for name in IMPLS:
            if name == "py_pure" and n > 512:
                continue  # pure Python at 1024 takes ~45 s per run; skip
            reps = 3 if QUICK else (5 if (name == "py_pure" and n >= 512) else 10)
            times, checks = run(configs(n, reps)[name])
            checks_seen |= checks
            med = statistics.median(times)
            sd = statistics.stdev(times) if len(times) > 1 else 0.0
            rows.append(dict(impl=name, n=n, reps=reps, median_s=med, min_s=min(times),
                             mean_s=statistics.mean(times), stdev_s=sd,
                             cv_pct=100 * sd / statistics.mean(times)))
            print(f"N={n:5d}  {name:9s}  median={med:10.5f}s  "
                  f"min={min(times):10.5f}s  cv={rows[-1]['cv_pct']:5.1f}%")
        # Every implementation must produce the same answer, or the comparison is meaningless.
        assert len({round(c, -1) for c in checks_seen}) == 1, f"checksums disagree at N={n}: {checks_seen}"

    out = os.path.join(RESULTS, "results_quick.csv" if QUICK else "results.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    with open(os.path.join(RESULTS, "environment.txt"), "w") as f:
        gcc = subprocess.run(["gcc", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
        import numpy
        f.write(f"platform: {platform.platform()}\nprocessor: {platform.processor() or 'see lscpu'}\n"
                f"cpu_count: {os.cpu_count()}\ngcc: {gcc}\npython: {platform.python_version()}\n"
                f"numpy: {numpy.__version__}\nnumpy threads: 1 (pinned)\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
