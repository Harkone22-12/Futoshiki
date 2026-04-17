# Futoshiki Solver

Futoshiki puzzle solver with a GUI, benchmark runner, and SAT + Knowledge Base flow.

The project includes multiple approaches:

- Brute Force
- Backtracking
- Backtracking + Forward Chaining
- Pure Forward Chaining
- Backward Chaining (SLD)
- A\* (AC3, MBDT, MRC)
- A\* + MAC (AC3, MBDT, MRC)
- SAT Solver (optional)

## Project Layout

- `Source/main.py`: GUI app (Tkinter)
- `Source/benchmark.py`: Benchmark runner
- `Source/benchmark_worker.py`: Subprocess worker used by benchmark
- `Source/satsolver.py`: SAT solver (Glucose3) that consumes grounded CNF from KB
- `Source/KB_generator.py`: Generates FOL facts and grounded CNF clauses
- `Source/Inputs/`: Input puzzle files
- `Source/Outputs/`: Generated outputs and logs

## Requirements

- Python 3.10 or newer
- pip

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Notes:

- On Windows, `tkinter` is usually included with Python.
- `python-sat` is required for the SAT solver.
- `matplotlib` is required for the GUI's charting feature.

## Run the GUI (`main.py`)

From project root:

```bash
python Source/main.py
```

In the GUI you can:

- Choose an input file from `Source/Inputs`
- Choose algorithm and heuristic
- Run the solver and inspect results
- Save outputs to `Source/Outputs`
- View charts and logs

## Run Benchmark

Basic run:

```bash
python Source/benchmark.py
```

Current default benchmark behavior:

- Up to 10 input files
- Brute Force enabled
- Brute Force runs fully only for the first 2 input files
- Brute Force has no timeout on those first 2 inputs
- All other algorithm cases use 120s timeout
- SAT case is included if `Source/satsolver.py` exists

Recommended full command:

```bash
python Source/benchmark.py --limit 10 --bruteforce-input-limit 2 --case-timeout-sec 120
```

SAT-only benchmark command:

```bash
python Source/benchmark.py --only-sat --limit 10 --case-timeout-sec 120
```

Useful options:

- `--limit N`: number of input files
- `--with-sat` / `--no-with-sat`
- `--with-bruteforce` / `--no-with-bruteforce`
- `--only-sat`: run SAT Solver only
- `--bruteforce-input-limit N`
- `--case-timeout-sec N`
- `--case-timeout N` (alias)

## Run SAT Solver Script

Run SAT solver directly (default input is configured in `Source/satsolver.py`):

```bash
python Source/satsolver.py
```

This script writes:

- `Source/Outputs/output-xx.txt`: solved board format
- `Source/Outputs/cnf_clauses_log_input-xx.txt`: grounded CNF log used by SAT solver

## Generate KB / Grounded CNF

Run KB generation directly:

```bash
python Source/KB_generator.py
```

This script writes:

- `Source/Outputs/ground_kb_input-xx.txt`: fact-oriented KB view
- `Source/Outputs/KB_ground_CNF_input-xx.txt`: grounded CNF clauses

## Input File Format

Each file contains:

1. board size `n`
2. `n` grid rows
3. `n` horizontal-constraint rows (`n-1` values each)
4. `n-1` vertical-constraint rows (`n` values each)

Example (`4x4`):

```text
4
# Grid
0,0,0,0
0,0,0,4
0,2,1,0
0,0,0,0
# Horizontal constraints
0,0,-1
1,-1,0
0,0,0
0,0,0
# Vertical constraints
0,0,-1,0
1,-1,0,0
0,0,0,0
```

## Outputs

- `Source/Outputs/output-*.txt`: solved boards from GUI runs
- `Source/Outputs/solve-log.csv`: run log from GUI
- `Source/Outputs/benchmark-results.csv`: benchmark results

## Troubleshooting

- SAT shows error in benchmark:
  Install SAT dependency:

  ```bash
  python -m pip install python-sat
  ```
