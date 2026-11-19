/*
 * matmul.c — naive matrix multiplication benchmark (C version)
 *
 * Usage:   ./matmul <N> <reps> [order]
 *   N      matrix dimension (multiplies two N x N matrices of doubles)
 *   reps   number of timed repetitions (one untimed warm-up run is done first)
 *   order  "ijk" (default, textbook order) or "ikj" (cache-friendly order)
 *
 * Output:  one line per repetition:  <seconds> <checksum>
 *
 * Design notes (why the benchmark looks like this):
 *   - Only the multiply is timed. Allocation and initialization happen before
 *     the clock starts, so we compare the *algorithm*, not malloc or startup.
 *   - clock_gettime(CLOCK_MONOTONIC) is used instead of time() (1 s resolution)
 *     or clock() (CPU time, not wall time). MONOTONIC never jumps backwards
 *     if the system clock is adjusted.
 *   - We print a checksum of C. Without it, an optimizing compiler (-O2) is
 *     allowed to notice the result is never used and delete the whole loop,
 *     which would make C look "infinitely fast".
 *   - Matrices are filled with the same deterministic values as the Python
 *     version, so both programs do exactly the same arithmetic.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

/* A[i][j] stored row-major in a flat array: A[i*n + j] */
static void fill(double *m, int n, int seed) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            m[i * n + j] = (double)((i * 31 + j * 17 + seed) % 100) / 10.0;
}

static void matmul_ijk(const double *A, const double *B, double *C, int n) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double sum = 0.0;
            for (int k = 0; k < n; k++)
                sum += A[i * n + k] * B[k * n + j];   /* B walks DOWN a column: stride n */
            C[i * n + j] = sum;
        }
}

static void matmul_ikj(const double *A, const double *B, double *C, int n) {
    memset(C, 0, sizeof(double) * (size_t)n * n);
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            double a = A[i * n + k];
            for (int j = 0; j < n; j++)
                C[i * n + j] += a * B[k * n + j];     /* B walks ACROSS a row: stride 1 */
        }
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s N reps [ijk|ikj]\n", argv[0]);
        return 1;
    }
    int n = atoi(argv[1]);
    int reps = atoi(argv[2]);
    const char *order = argc > 3 ? argv[3] : "ijk";
    void (*mm)(const double *, const double *, double *, int) =
        strcmp(order, "ikj") == 0 ? matmul_ikj : matmul_ijk;

    double *A = malloc(sizeof(double) * (size_t)n * n);
    double *B = malloc(sizeof(double) * (size_t)n * n);
    double *C = malloc(sizeof(double) * (size_t)n * n);
    if (!A || !B || !C) { fprintf(stderr, "out of memory\n"); return 1; }
    fill(A, n, 1);
    fill(B, n, 2);

    mm(A, B, C, n);                       /* warm-up: fault in pages, warm caches */

    for (int r = 0; r < reps; r++) {
        double t0 = now_seconds();
        mm(A, B, C, n);
        double t1 = now_seconds();
        double checksum = 0.0;
        for (int i = 0; i < n * n; i++) checksum += C[i];
        printf("%.9f %.6f\n", t1 - t0, checksum);
    }
    free(A); free(B); free(C);
    return 0;
}
