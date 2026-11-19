# Resources

## Timing APIs
- Python `time.perf_counter()`: https://docs.python.org/3/library/time.html#time.perf_counter
- Python `timeit` module (and its notes on why it disables garbage collection and repeats runs): https://docs.python.org/3/library/timeit.html
- Linux `clock_gettime(2)` man page (`CLOCK_MONOTONIC` vs `CLOCK_REALTIME`): https://man7.org/linux/man-pages/man2/clock_gettime.2.html
- `time(1)` man page (real / user / sys): https://man7.org/linux/man-pages/man1/time.1.html

## Benchmarking tools
- hyperfine, a command-line benchmarking tool with warm-ups and statistics: https://github.com/sharkdp/hyperfine
- pyperf, a toolkit for writing reliable Python benchmarks: https://pyperf.readthedocs.io/
- Linux `perf` (hardware counters such as cache misses): https://perfwiki.github.io/main/
- Google Benchmark (C++), whose `DoNotOptimize` exists because of dead-code elimination: https://github.com/google/benchmark/blob/main/docs/user_guide.md

## Compilers & libraries
- GCC optimization options (`-O0`, `-O2`, …): https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html
- NumPy `matmul` / `@`: https://numpy.org/doc/stable/reference/generated/numpy.matmul.html
- NumPy's BLAS/LAPACK build docs (it calls an optimized BLAS like OpenBLAS): https://numpy.org/doc/stable/building/blas_lapack.html

## Background reading
- Bryant & O'Hallaron, *Computer Systems: A Programmer's Perspective* (CS:APP), Ch. 6 "The Memory Hierarchy". Section 6.6 analyzes all six loop orderings of matrix multiply and why `ikj`/`kij` are fastest. http://csapp.cs.cmu.edu/
- Mytkowicz, Diwan, Hauswirth, Sweeney, "Producing Wrong Data Without Doing Anything Obviously Wrong!" (ASPLOS 2009). Shows that even environment-variable size and link order can change benchmark results. https://dl.acm.org/doi/10.1145/1508244.1508275

## AI conversation
- See [`ai-conversation.md`](ai-conversation.md) and the permalink in [`REFLECTION.md`](REFLECTION.md).
