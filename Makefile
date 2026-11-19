# Convenience targets. Everything can also be run by hand (see README).
CC = gcc

all: src/matmul_O0 src/matmul_O2 src/dce_demo

src/matmul_O0: src/matmul.c
	$(CC) -O0 -o $@ $<

src/matmul_O2: src/matmul.c
	$(CC) -O2 -o $@ $<

src/dce_demo: src/dce_demo.c
	$(CC) -O2 -o $@ $<

bench: all
	python3 src/bench.py

quick: all
	python3 src/bench.py --quick

experiments: all
	python3 src/experiments.py

plots:
	python3 src/plot.py

dce: src/dce_demo
	./src/dce_demo

clean:
	rm -f src/matmul_O0 src/matmul_O2 src/dce_demo

.PHONY: all bench quick experiments plots dce clean
