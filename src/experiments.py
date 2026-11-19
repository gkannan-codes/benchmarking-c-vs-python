"""
experiments.py — small side experiments about benchmarking itself.

Usage:  python3 experiments.py      (run bench.py first so the C binaries exist)

1. startup   How long does it take just to START each program (N=1)?
             Shows why timing a whole process with `time` is unfair for small inputs.
2. noise     Runs the same benchmark as 30 separate processes and records each
             timing, to show run-to-run variation (why one run is not enough).
3. cold      Times the very first multiply in a fresh process (no warm-up)
             vs. later ones — warm-up effects.
Writes CSVs into ../results/.
"""
import csv
import os
import subprocess
import sys
import time
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
C = os.path.join(HERE, "matmul_O2")
PY = [sys.executable, os.path.join(HERE, "matmul.py")]


def wall(cmd):
    t0 = time.perf_counter()
    subprocess.run(cmd, stdout=subprocess.DEVNULL, check=True)
    return time.perf_counter() - t0


def startup():
    rows = []
    for name, cmd in {"c_O2": [C, "1", "1"], "py_pure": PY + ["1", "1"],
                      "py_numpy": PY + ["1", "1", "numpy"]}.items():
        ts = [wall(cmd) for _ in range(20)]
        rows.append(dict(impl=name, median_startup_ms=1000 * statistics.median(ts)))
        print(f"startup  {name:9s} {rows[-1]['median_startup_ms']:7.2f} ms")
    return rows


def noise(n=128, procs=30):
    rows = []
    for name, cmd in {"c_O2": [C, str(n), "1"], "py_pure": PY + [str(n), "1"]}.items():
        for p in range(procs):
            out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
            rows.append(dict(impl=name, n=n, run=p, seconds=float(out.split()[0])))
        ts = [r["seconds"] for r in rows if r["impl"] == name]
        print(f"noise    {name:9s} min={min(ts):.5f} median={statistics.median(ts):.5f} "
              f"max={max(ts):.5f}  (max/min = {max(ts)/min(ts):.2f}x)")
    return rows


COLD_SNIPPET = r"""
import sys, time
sys.path.insert(0, sys.argv[1])
import matmul
n = int(sys.argv[2])
A, B = matmul.fill(n, 1), matmul.fill(n, 2)
for r in range(6):
    t0 = time.perf_counter(); matmul.matmul_pure(A, B, n); t1 = time.perf_counter()
    print(t1 - t0)
"""


def cold(n=128):
    out = subprocess.run([sys.executable, "-c", COLD_SNIPPET, HERE, str(n)],
                         capture_output=True, text=True, check=True).stdout.split()
    rows = [dict(impl="py_pure", n=n, run=i, seconds=float(t)) for i, t in enumerate(out)]
    print("cold     py_pure runs 0..5: " + ", ".join(f"{float(t)*1000:.1f}ms" for t in out))
    return rows


def save(name, rows):
    with open(os.path.join(RESULTS, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    os.makedirs(RESULTS, exist_ok=True)
    save("startup.csv", startup())
    save("noise.csv", noise())
    save("cold.csv", cold())
