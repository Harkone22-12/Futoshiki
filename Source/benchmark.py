import argparse
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from main import SAT_AVAILABLE, load_env_from_file

BASE_DIR = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "Inputs"
OUTPUTS_DIR = BASE_DIR / "Outputs"
BENCHMARK_FILE = OUTPUTS_DIR / "benchmark-results.csv"
SAT_SOLVER_FILE = BASE_DIR / "satsolver.py"
BRUTE_FORCE_LABEL = "Brute Force"

BENCHMARK_HEADER = [
    "timestamp",
    "input_file",
    "size",
    "algorithm_variant",
    "algorithm",
    "heuristic",
    "fc_prune",
    "status",
    "elapsed_sec",
    "nodes",
    "peak_memory_mb",
    "note",
]


def build_algorithm_matrix(*, include_sat=True, include_bruteforce=True, sat_only=False):
    if sat_only:
        if include_sat and SAT_SOLVER_FILE.exists():
            return [{"label": "SAT Solver", "algo": "SAT Solver", "heur": "", "fc": False}]
        return []

    matrix = [
        {"label": BRUTE_FORCE_LABEL, "algo": BRUTE_FORCE_LABEL, "heur": "", "fc": False},
        {"label": "Backtracking", "algo": "Backtracking", "heur": "", "fc": False},
        {
            "label": "Backtracking + Forward Chaining",
            "algo": "Backtracking + Forward Chaining",
            "heur": "",
            "fc": False,
        },
        {"label": "Pure Forward Chaining", "algo": "Pure Forward Chaining", "heur": "", "fc": False},
        {
            "label": "Backward Chaining (SLD)",
            "algo": "Backward Chaining (SLD)",
            "heur": "",
            "fc": False,
        },
        {"label": "A* AC3", "algo": "A* Search", "heur": "AC3", "fc": False},
        {"label": "A* MBDT", "algo": "A* Search", "heur": "MBDT", "fc": False},
        {"label": "A* MRC", "algo": "A* Search", "heur": "MRC", "fc": False},
        {"label": "A* AC3 + MAC", "algo": "A* Search", "heur": "AC3", "fc": True},
        {"label": "A* MBDT + MAC", "algo": "A* Search", "heur": "MBDT", "fc": True},
        {"label": "A* MRC + MAC", "algo": "A* Search", "heur": "MRC", "fc": True},
    ]

    if not include_bruteforce:
        matrix = [case for case in matrix if case["algo"] != BRUTE_FORCE_LABEL]

    if include_sat and SAT_SOLVER_FILE.exists():
        matrix.append({"label": "SAT Solver", "algo": "SAT Solver", "heur": "", "fc": False})

    return matrix


def collect_inputs(limit=10):
    return sorted(INPUTS_DIR.glob("input-*.txt"))[:limit]


def _as_elapsed_text(value):
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return str(value)


def _as_memory_text(value):
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return ""


def _extract_json_packet(stdout_text):
    lines = [ln.strip() for ln in str(stdout_text).splitlines() if ln.strip()]
    for line in reversed(lines):
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            return json.loads(line)
        except Exception:
            continue
    return None


def _stderr_tail(stderr_text):
    lines = [ln.strip() for ln in str(stderr_text).splitlines() if ln.strip()]
    if not lines:
        return ""
    return lines[-1]


def run_case(payload, timeout_sec=120.0):
    started = time.perf_counter()
    worker_path = BASE_DIR / "benchmark_worker.py"
    command = [
        sys.executable,
        str(worker_path),
        "--path",
        str(payload["path"]),
        "--algo",
        str(payload["algo"]),
        "--heur",
        str(payload["heur"]),
        "--fc",
        "1" if payload["fc"] else "0",
    ]

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=(None if timeout_sec <= 0 else timeout_sec),
        )
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - started
        return {
            "status": "timeout",
            "elapsed": elapsed,
            "nodes": "N/A",
            "peak_memory_mb": "",
            "note": f"Timed out after {timeout_sec:.1f}s",
        }

    packet = _extract_json_packet(proc.stdout)
    if not isinstance(packet, dict):
        elapsed = time.perf_counter() - started
        err_tail = _stderr_tail(proc.stderr)
        note = "Worker produced no parseable JSON output"
        if err_tail:
            note = f"{note}: {err_tail}"
        return {
            "status": "error",
            "elapsed": elapsed,
            "nodes": "N/A",
            "peak_memory_mb": "",
            "note": note,
        }

    if not packet.get("ok"):
        elapsed = time.perf_counter() - started
        return {
            "status": "error",
            "elapsed": elapsed,
            "nodes": "N/A",
            "peak_memory_mb": "",
            "note": str(packet.get("error", "Unknown worker error")).strip(),
        }

    result = packet.get("result") or {}
    return {
        "status": "solved" if result.get("solved") else "failed",
        "elapsed": float(result.get("elapsed", time.perf_counter() - started)),
        "nodes": result.get("nodes", "N/A"),
        "peak_memory_mb": result.get("peak_memory_mb", ""),
        "note": str(result.get("note", "")).strip(),
    }


def run_benchmark(
    limit=10,
    include_sat=True,
    include_bruteforce=True,
    bruteforce_input_limit=2,
    case_timeout_sec=120.0,
    sat_only=False,
):
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    input_files = collect_inputs(limit=limit)
    if not input_files:
        raise RuntimeError(f"No input files found in {INPUTS_DIR}")

    matrix = build_algorithm_matrix(
        include_sat=include_sat,
        include_bruteforce=include_bruteforce,
        sat_only=sat_only,
    )
    if not matrix:
        raise RuntimeError("No algorithm variants selected. Use --with-sat when running --only-sat.")

    total_runs = len(input_files) * len(matrix)

    print(f"Starting benchmark on {len(input_files)} input files")
    print(f"Algorithm variants: {len(matrix)}")
    if case_timeout_sec > 0:
        print(f"Per-case timeout: {case_timeout_sec:.1f}s")
    else:
        print("Per-case timeout: disabled")
    if sat_only:
        print("Mode: SAT Solver only")
    elif include_bruteforce:
        if bruteforce_input_limit > 0:
            print(f"Brute Force mode: run only first {bruteforce_input_limit} input(s)")
            print("Brute Force timeout: disabled for these inputs")
        else:
            print("Brute Force mode: enabled but skipped for all inputs (limit <= 0)")
    else:
        print("Brute Force mode: excluded from benchmark")
    if include_sat and SAT_SOLVER_FILE.exists():
        sat_state = "available" if SAT_AVAILABLE else "present but dependency missing"
        print(f"SAT mode: included ({sat_state})")
    else:
        print("SAT mode: excluded")
    print(f"Total runs: {total_runs}")
    print("-" * 72)

    rows = []
    run_counter = 0

    for file_index, input_path in enumerate(input_files, start=1):
        env = load_env_from_file(input_path)
        size_text = f"{env.n}x{env.n}"
        print(f"[{file_index}/{len(input_files)}] {input_path.name} ({size_text})")

        for algo_index, case in enumerate(matrix, start=1):
            run_counter += 1
            payload = {
                "path": str(input_path),
                "algo": case["algo"],
                "heur": case["heur"],
                "fc": bool(case["fc"]),
            }

            print(
                f"  ({algo_index}/{len(matrix)}) {case['label']} ... ",
                end="",
                flush=True,
            )

            if (
                include_bruteforce
                and case["algo"] == BRUTE_FORCE_LABEL
                and file_index > bruteforce_input_limit
            ):
                result = {
                    "status": "skipped",
                    "elapsed": 0.0,
                    "nodes": "N/A",
                    "peak_memory_mb": "",
                    "note": f"Skipped: Brute Force runs only for first {bruteforce_input_limit} input(s)",
                }
            elif (
                include_bruteforce
                and case["algo"] == BRUTE_FORCE_LABEL
                and file_index <= bruteforce_input_limit
            ):
                # Run full brute force for the first N inputs with no timeout.
                result = run_case(payload, timeout_sec=0.0)
            else:
                result = run_case(payload, timeout_sec=case_timeout_sec)

            print(f"{result['status']} ({result['elapsed']:.4f}s)")

            rows.append(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "input_file": input_path.name,
                    "size": size_text,
                    "algorithm_variant": case["label"],
                    "algorithm": case["algo"],
                    "heuristic": case["heur"],
                    "fc_prune": "yes" if case["fc"] else "no",
                    "status": result["status"],
                    "elapsed_sec": _as_elapsed_text(result["elapsed"]),
                    "nodes": str(result["nodes"]),
                    "peak_memory_mb": _as_memory_text(result["peak_memory_mb"]),
                    "note": result["note"],
                }
            )

    with open(BENCHMARK_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BENCHMARK_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    print("-" * 72)
    print(f"Completed {run_counter}/{total_runs} runs")
    print(f"Benchmark saved to: {BENCHMARK_FILE}")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark Futoshiki solvers across input files")
    parser.add_argument("--limit", type=int, default=10, help="Number of input files to run (default: 10)")
    parser.add_argument(
        "--with-sat",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include SAT Solver case when satsolver.py is present (default: enabled)",
    )
    parser.add_argument(
        "--with-bruteforce",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include Brute Force in benchmark matrix (default: enabled)",
    )
    parser.add_argument(
        "--bruteforce-input-limit",
        type=int,
        default=1,
        help="Run Brute Force only for the first N input files (default: 1)",
    )
    parser.add_argument(
        "--case-timeout-sec",
        "--case-timeout",
        dest="case_timeout_sec",
        type=float,
        default=120.0,
        help="Timeout per algorithm case in seconds (default: 120, 0 disables timeout)",
    )
    parser.add_argument(
        "--only-sat",
        action="store_true",
        help="Run benchmark with SAT Solver only",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_benchmark(
        limit=max(1, args.limit),
        include_sat=args.with_sat,
        include_bruteforce=args.with_bruteforce,
        bruteforce_input_limit=max(0, args.bruteforce_input_limit),
        case_timeout_sec=max(0.0, args.case_timeout_sec),
        sat_only=args.only_sat,
    )
