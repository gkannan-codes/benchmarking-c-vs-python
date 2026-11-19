/*
 * dce_demo.c — "Dead Code Elimination": why benchmarks must USE their result.
 *
 * Build & run:
 *   gcc -O2 -o dce_demo dce_demo.c && ./dce_demo
 *
 * The loop in sum_unused() computes a sum but never uses it. With -O2 the
 * compiler is allowed to delete the whole loop, so it "takes" ~0 seconds.
 * sum_used() returns the result and we print it, so the work must really happen.
 * (Look at the assembly with:  gcc -O2 -S dce_demo.c  and search for the loops.)
 */
#include <stdio.h>
#include <time.h>

#define N 500000000L

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static void sum_unused(void) {
    long s = 0;
    for (long i = 0; i < N; i++) s += i ^ (i >> 3);
    (void)s;                                  /* result thrown away */
}

static long sum_used(void) {
    long s = 0;
    for (long i = 0; i < N; i++) s += i ^ (i >> 3);
    return s;                                 /* result returned and printed */
}

int main(void) {
    double t0 = now(); sum_unused(); double t1 = now();
    double t2 = now(); long s = sum_used(); double t3 = now();
    printf("result unused: %.6f s   (near 0 at -O2: the optimizer deleted the loop)\n", t1 - t0);
    printf("result used:   %.6f s   (sum = %ld)\n", t3 - t2, s);
    return 0;
}
