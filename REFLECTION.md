# Written Reflection: Using AI to Learn Performance Benchmarking

**Gokul Kannan · COMP 211 · Fall 2026**
**AI conversation permalink:** `PASTE-PERMALINK-HERE`

## How did I engage with AI?

I used Claude as a tutor and a sparring partner, not an answer key. I started by asking for a *short checklist* of what
makes a benchmark trustworthy so I had a framework before writing code. From there, my pattern was: ask a question → get an
explanation → **write a small experiment to test it** → bring my numbers back to the AI and ask it to explain them.

A few times this changed what I believed:

- **Startup cost.** The AI said shell `time` includes interpreter startup. I measured it (C ≈ 1 ms, Python ≈ 13 ms, Python + NumPy ≈ 88 ms)
  and realized that for small inputs, whole-process timing would mostly measure Python *starting up*, not the multiply.
- **Dead-code elimination.** I didn't believe a compiler was allowed to delete my loop, so I pushed back and asked why. After the AI explained the
  "as-if" rule, I wrote `dce_demo.c` and watched a 0.24 s loop drop to 0.000001 s at `-O2`. This is why my benchmarks print a checksum.
- **Challenging the AI.** The AI said `-O2` is typically several times faster than `-O0`. My data at N = 1024 showed **no** speedup.
  I brought that contradiction back, and the explanation (column-stride access missing in cache, memory-bound loop) connected directly to
  COMP 211's memory hierarchy unit. I then proposed swapping loop order myself, tested it, and got a 13× speedup.
- **Testing a claim that turned out weaker than stated.** The AI listed warm-up as an important factor. I measured it for pure Python and found
  only a ~2% effect. The AI then clarified *when* warm-up matters (JIT runtimes, page faults, file caches), which was more useful than the original blanket statement.

I also explained concepts back in my own words (cache lines and stride, why the C/Python ratio shrinks at larger N) and asked the AI to check my
understanding. It confirmed and refined my explanation by pointing out that i‑k‑j also lets the compiler vectorize.

## Representative prompts

1. **Testing a claim:** *"Let me check that claim. I timed just starting each program with N = 1 … C ≈ 1.1 ms, Python ≈ 12.8 ms, Python + import numpy ≈ 88 ms.
   So for N = 64 `time` would mostly be measuring Python startup … Right?"*
   This is where I started treating the AI's statements as hypotheses to check.

2. **Challenging an explanation with my own data:** *"At N = 1024, -O2 took 8.46 s and -O0 took 8.06 s. You said -O2 can be several times faster.
   Why is it not faster at all here, even slightly slower?"*
   This led to the most interesting part of my project (cache behavior), which I wouldn't have found by only asking questions.

3. **Explaining in my own words:** *"Let me explain this in my own words to check myself: the computer doesn't fetch single numbers from memory; it fetches 64-byte
   cache lines. Walking down a column wastes 56 of every 64 bytes … Is that accurate?"*

## What would I do differently?

**What worked:** Running experiments between questions. The AI's explanations made much more sense once I had my own numbers in front of me, and
contradictions between its general claims and my specific data led to the best follow-up questions. Asking for "short checklists" instead of essays
also kept the conversation focused.

**What I'd change:**
- I'd ask the AI for **sources earlier** (e.g., the CS:APP section on loop orderings, the `clock_gettime` man page) and read them myself, rather than
  verifying only by experiment. Some claims, like the "as-if" rule, are easier to confirm from documentation than from measurement.
- I'd **ask the AI to predict results before running** each experiment. Comparing its prediction to reality would have been a sharper test of
  its explanations than asking it to explain results after the fact.
- I'd use a dedicated tool like `hyperfine` or `pyperf` from the start instead of writing my own harness. I learned a lot building the harness, but those tools
  handle things like outlier detection and calibration that I only partly covered.
- I'd try `perf stat` to **directly measure cache misses** instead of inferring them from timing.
