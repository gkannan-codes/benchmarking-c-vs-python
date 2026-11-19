# AI Exploration Dialogue: Benchmarking C vs. Python

A record of my back-and-forth with Claude while exploring this topic. My prompts are under **Me**,
the AI's responses under **AI**, and my notes about what I did with each answer are in *italics*.
Full conversation permalink: see `REFLECTION.md`.

---

This is a AI summary of the conversation found in REFLECTION.md. To see the full original conversation follow the link in the designated file. 

---

### 1. Getting oriented

**Me:** I'm in COMP 211 (systems: C, memory, caches, processes). My final topic is benchmarking C vs. Python.
Before writing any code, what does a *good* benchmark need to have? Give me a short checklist, not an essay.

**AI:** A trustworthy benchmark needs:
1. **A precise question.** "Is C faster?" is vague; "How long does naive N×N matrix multiply take in C vs. Python for N = 64…1024?" is testable.
2. **Equivalent work.** Same algorithm, same inputs, and a way to *verify* both produce the same output.
3. **The right clock.** Monotonic, high-resolution, wall-clock time around only the code you care about.
4. **Repetition.** Many runs, then a robust summary (median) plus spread.
5. **Controlled conditions.** Same machine, quiet system, documented compiler flags and versions.
6. **Honest reporting.** Raw data, environment, and limitations.

**Me:** Why matrix multiplication rather than something simpler like summing numbers?

**AI:** Summing is fine, but matrix multiply is O(N³) arithmetic over O(N²) data, so it stresses both the
CPU *and* the memory hierarchy. You'll see interpreter overhead in Python and cache effects in C, which ties
directly to COMP 211's caching unit.

*I chose matrix multiplication because of that cache connection.*

---

### 2. Measuring time

**Me:** In C we've used `time()` before. Is that good enough for timing a function?

**AI:** Not really. `time()` returns whole seconds, so anything under a second rounds to 0 or 1. `clock()` gives
**CPU time** for your process, which isn't the same as elapsed time. For benchmarking, use
`clock_gettime(CLOCK_MONOTONIC, &ts)`: it has nanosecond resolution and is *monotonic*, meaning it never jumps
backward if the system clock is adjusted (e.g., by NTP). The Python equivalent is `time.perf_counter()`.

**Me:** What's the difference between timing inside the program and just running `time ./prog` in the shell?

**AI:** `time ./prog` measures the whole process: loading the executable, starting the runtime (for Python, the
whole interpreter), allocating and filling inputs, and the work itself. It reports `real` (wall clock), `user` and
`sys` (CPU time in user mode and kernel mode). Timing inside the program isolates only the code you care about.
For large workloads the difference is small; for tiny workloads, startup can dominate.

**Me:** Let me check that claim. *(I wrote `experiments.py` to time just starting each program with N = 1.)*
I got C ≈ 1.1 ms, Python ≈ 12.8 ms, Python + `import numpy` ≈ 88 ms. So for N = 64, where pure Python's multiply
takes 7 ms, `time` would mostly be measuring Python startup, and for NumPy (0.012 ms of actual work) it would be
~99.99% import time. Right?

**AI:** Exactly. That's a nice test. It also shows why "NumPy is slow for small problems" claims are often really
measuring the import. With in-program timing, you separate **startup cost** from **per-operation cost**, and
both are legitimate to report as long as you say which one you're measuring.

---

### 3. Why repeat?

**Me:** If a computer is deterministic, why would the same program take different amounts of time?

**AI:** The *result* is deterministic, but the *timing* depends on things outside your program:
- the OS scheduler running other processes or interrupts on your core,
- CPU frequency scaling and turbo boost,
- the cache state (what's already in L1/L2/L3),
- memory/page placement, which can differ per process,
- for Python, garbage collection and memory allocator behavior.

That's why you run many times and report the median (robust to occasional slow outliers) or the minimum
(closest to the "noise-free" cost), plus the spread.

**Me:** How much variation are we talking about? Like 1%?

**AI:** On a quiet machine for a CPU-bound loop, often a few percent. On a busy laptop it can be much more.
Best to measure it on your own system instead of trusting a number from me.

*I ran each program as 30 separate processes (`experiments.py`, "noise").*

**Me:** Results: C -O2 at N = 128 ranged from 2.09 to 2.85 ms (slowest/fastest = 1.36×), and Python from
56 to 85 ms (1.52×). Most runs cluster tightly around the median, but a few outliers are 30–50% slower. So if I'd
done one run and gotten an outlier, my C/Python ratio could be off by a lot. That's my argument for medians.

**AI:** Yes, and notice the outliers are always *slower*, never faster. Noise only adds time, which is why
some tools report the minimum. Median is a good, defensible choice for a presentation.

---

### 4. Making it fair

**Me:** What would make a C vs. Python comparison *unfair*?

**AI:** Common traps:
1. **Different algorithms.** E.g., Python's built-in `sorted()` (Timsort, in C) vs. your hand-written bubble sort in C.
2. **Timing different things.** Including file I/O or input generation in one but not the other.
3. **Unstated compiler flags.** `-O0` vs. `-O2` can differ several-fold.
4. **Libraries vs. language.** NumPy is Python *calling* highly optimized C/Fortran/assembly. Fine to include, but label it.
5. **Hidden parallelism.** NumPy's BLAS may use all your cores while your C code uses one.
6. **Dead-code elimination.** If the C result is never used, the optimizer can delete the computation entirely.

**Me:** Wait, #6. The compiler is allowed to just *delete* my loop? That seems like it would break programs.

**AI:** It's allowed under the "as-if" rule: the compiler may make any transformation that doesn't change the
program's *observable behavior* (output, volatile accesses, etc.). If a loop computes a value that's never printed,
returned, or stored anywhere visible, deleting it doesn't change observable behavior. Time isn't considered
observable behavior. Try it: compute a sum in a loop, don't use it, compile with `-O2`, and time it.

**Me:** *(Wrote `dce_demo.c`.)* Unused result: 0.000001 s. Used result: 0.24 s. At `-O0` both take ~1.1 s.
So in my matmul benchmark I need to print a checksum of C. That's also how I verify that C, Python, and NumPy
compute the same thing. Two birds, one stone.

**AI:** Exactly right. Checksums do double duty: they defeat dead-code elimination *and* validate equivalence.
One caution: with floating point, different summation orders can give slightly different results, so compare
with a tolerance.

*All five versions gave identical checksums (e.g., 3288669703.04 at N = 512). NumPy's BLAS sums in a different
order, but matched to the digits I printed. My harness compares after rounding, per the AI's tolerance warning.*

---

### 5. The results, and a challenge

**Me:** Here are my medians at N = 512: Python 9.83 s, C -O0 0.86 s, C -O2 0.444 s, NumPy 0.005 s. So C is
22× faster than Python, and NumPy is 89× faster than my C?! How is Python code beating C?

**AI:** It isn't *Python* beating C. It's a better *algorithm implementation* beating a naive one. NumPy hands the
multiply to a BLAS library that (1) uses **blocking/tiling** so sub-matrices stay in cache, (2) uses **SIMD**
instructions to do several multiply-adds per instruction, and (3) is hand-tuned per CPU. Your C triple loop does
none of that. The Python layer only costs a few microseconds of overhead per call.

**Me:** Then here's something I didn't expect. At N = 1024, `-O2` took **8.46 s** and `-O0` took **8.06 s**.
You said `-O2` can be several times faster. Why is it not faster at all here, even slightly slower?

**AI:** Good catch. That contradicts the simple story, and the explanation is memory. In i‑j‑k order the inner loop
reads `B[k][j]` for k = 0, 1, 2, …, walking *down a column*. In row-major storage, each step jumps N × 8 bytes:
8 KB at N = 1024. Every access touches a new cache line, and only 8 bytes of each 64-byte line get used. At
N = 1024, B is 8 MB, bigger than the caches, so nearly every access misses. The CPU then spends most of its
time *waiting for memory*. `-O2` makes the arithmetic faster, but arithmetic isn't the bottleneck anymore.
(The slight slowdown is within noise.) Power-of-two sizes also make this worse, because those addresses map to
the same cache sets (conflict misses).

**Me:** So if I make the inner loop walk across a *row* instead, it should help? Like swapping j and k: for i, for k, for j:
`C[i][j] += A[i][k] * B[k][j]`. Now `B[k][j]` and `C[i][j]` are both stride-1 in the inner loop.

**AI:** That's the i‑k‑j ordering, which CS:APP §6.6 shows is among the fastest of the six orderings for exactly that
reason: unit stride on both arrays touched in the inner loop. Same arithmetic, same O(N³). Measure it.

*(Added an `ikj` mode to `matmul.c`.)*

**Me:** i‑k‑j at N = 1024: **0.638 s**, 13× faster than i‑j‑k with the same flags. At N = 512: 0.076 s vs 0.444 s (5.9×).
Let me explain this in my own words to check myself: *the computer doesn't fetch single numbers from memory; it fetches 64-byte
cache lines. Walking down a column wastes 56 of every 64 bytes and misses constantly. Walking across a row uses all 8 doubles in
every line, and the hardware prefetcher can predict the next one.* Is that accurate?

**AI:** That's accurate. One refinement: in i‑k‑j, `A[i][k]` is loaded once per middle iteration and kept in a register,
so the inner loop is pure streaming over two rows. That's also why the compiler can **vectorize** it (SIMD) at `-O2`.
In i‑j‑k, the strided access blocks that. So loop order helps twice: better cache use *and* it unlocks compiler optimizations.

**Me:** That also explains something else in my data. The C/Python ratio *drops* from 39× at N = 256 to 22× at N = 512.
Python's per-operation overhead is so large that cache misses barely matter to it, but C at N = 512 starts missing a
lot. So C slows down "more" relative to Python as N grows. The ratio depends on input size.

**AI:** Yes. That's an important reporting point: a single "C is X× faster" number hides that X depends on the workload.

---

### 6. Testing one of the AI's claims that didn't hold up as strongly

**Me:** Earlier you listed "warm-up" as important. I tested it for pure Python: in one process, runs 1–6 at N = 128 were
58.6, 59.3, 57.9, 57.4, 57.3, 57.5 ms. The first run is only ~2% slower. So warm-up barely matters here?

**AI:** For standard CPython it's a small effect, because the interpreter doesn't compile hot loops into machine code
(CPython 3.13's experimental JIT is off by default). Warm-up matters much more for JIT runtimes (PyPy, Java, JavaScript),
for the first touch of large freshly allocated arrays (page faults), and for disk caches when reading files.
Your measurement is the right way to settle it: keep the warm-up as cheap insurance, but don't overclaim its effect.

*I kept a warm-up run in both programs but describe its effect honestly in my README.*

---

### 7. Reporting

**Me:** How should I present this so it's honest and not misleading?

**AI:**
- Use a **log-scale** y-axis, since your times span 10⁻⁵ to 10¹ s.
- Report the **median, number of runs, and spread** (I'd include the coefficient of variation).
- Include the **environment**: CPU, core count, compiler + flags, Python/NumPy versions, threads.
- Show **multiple sizes**, not one.
- Keep NumPy as a separate, labeled line: it's "Python + optimized library," not "Python."
- State **limitations**: one algorithm, one machine.

**Me:** Final check of my takeaway: *"For the same naive algorithm, C is roughly 10–60× faster than Python because the
interpreter adds overhead to every operation. But how you use memory can matter more than which language or compiler flag
you pick, and the fastest option from Python is to call a library that's already optimized in C."* Fair?

**AI:** Fair, and well supported by your data. I'd only add "on this machine" to the first sentence.
