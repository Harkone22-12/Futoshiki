import os
import time
import csv
import psutil
import gc

# --- IMPORT MÔI TRƯỜNG ---
from futoshiki_env import FutoshikiEnv

# --- IMPORT CÁC THUẬT TOÁN ĐÃ ĐƯỢC CHUẨN HÓA ---
from satsolver import FutoshikiSATSolver
from Bruteforce import solve_bruteforce
from Backtracking import solve_backtracking
from Backtracking_Forward import solve_with_bfc, KnowledgeBase as KB_BTF, ForwardChaining as FC_BTF
from Backward_chaining import SLDResolutionEngine
from Forward_chaining import solve_pure_fc

# Import 3 biến thể A* Pure
from Astar_ac3 import solve_astar_ac3
from Astar_mbdt import solve_astar_mbdt
from Astar_mrc import solve_astar_mrc

# Import 3 biến thể A* + Forward Chaining (MAC)
from Astar_ac3_Forward import solve_astar_mac_ac3
from Astar_mbdt_Forward import solve_astar_mac_mbdt
from Astar_mrc_Forward import solve_astar_mac_mrc


def load_env_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    n = int(lines[0])
    env = FutoshikiEnv(n)
    
    for i in range(1, n + 1):
        row_vals = [int(x) for x in lines[i].split(',')]
        for j in range(n):
            if row_vals[j] != 0:
                env.set_given_value(i-1, j, row_vals[j])
                
    for i in range(n + 1, 2 * n + 1):
        row_vals = [int(x) for x in lines[i].split(',')]
        for j in range(n-1):
            if row_vals[j] != 0:
                env.add_horizontal_constraint(i - (n + 1), j, row_vals[j])
                
    for i in range(2 * n + 1, 3 * n):
        row_vals = [int(x) for x in lines[i].split(',')]
        for j in range(n):
            if row_vals[j] != 0:
                env.add_vertical_constraint(i - (2 * n + 1), j, row_vals[j])
    return env

def extract_nodes(res):
    """
    Hàm helper: Cố gắng lấy số Node từ kết quả trả về của thuật toán.
    Giả định thuật toán trả về dạng tuple: (solution/bool, nodes_expanded)
    """
    if isinstance(res, tuple) and len(res) >= 2 and isinstance(res[1], int):
        return res[1]
    return "N/A"

def measure_memory():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def run_algorithm_with_memory(algo_func, *args, timeout_sec=120):
    """
    Run algorithm and measure time + memory usage.
    Returns: (result, elapsed_time, memory_used_mb)
    """
    import gc
    gc.collect()
    
    mem_before = measure_memory()
    start_time = time.time()
    
    try:
        result = algo_func(*args)
        elapsed = time.time() - start_time
        mem_after = measure_memory()
        memory_used = mem_after - mem_before
        return result, elapsed, abs(memory_used)
    except Exception as e:
        elapsed = time.time() - start_time
        return None, elapsed, 0.0

def run_benchmark():
    input_folder = "Source/Inputs" 
    output_folder = "Source/Benchmarks"
    os.makedirs(output_folder, exist_ok=True)
    output_csv = os.path.join(output_folder, "benchmark_results_full.csv")

    files = [f for f in os.listdir(input_folder) if f.startswith("input") and f.endswith(".txt")]
    files.sort()

    results = []

    print(f"BẮT ĐẦU CHẠY BENCHMARK VỚI MEMORY TRACKING TRÊN {len(files)} FILE...")
    print("Cảnh báo: Quá trình này có thể mất vài phút. Vui lòng kiên nhẫn đợi!")
    print("-" * 80)

    for filename in files:
        file_path = os.path.join(input_folder, filename)
        env = load_env_from_file(file_path)
        n = env.n
        print(f"Đang xử lý: {filename} (Size: {n}x{n})")

        row_data = {"File": filename, "Size": f"{n}x{n}"}

        # 1. BRUTE FORCE - Timeout for n >= 4
        if n >= 4:
            row_data["BruteForce (s)"] = "Timeout"
            row_data["BruteForce (MB)"] = "N/A"
            row_data["Nodes BruteForce"] = "N/A"
        else:
            env_bf = load_env_from_file(file_path)
            res, elapsed, mem_used = run_algorithm_with_memory(
                solve_bruteforce, env_bf.grid, n, env_bf.horiz_constraints, env_bf.vert_constraints
            )
            row_data["BruteForce (s)"] = round(elapsed, 4)
            row_data["BruteForce (MB)"] = round(mem_used, 2)
            row_data["Nodes BruteForce"] = extract_nodes(res)

        # 2. BACKTRACKING PURE - Timeout for n >= 8
        if n >= 8:
            row_data["Backtrack Pure (s)"] = "Timeout"
            row_data["Backtrack Pure (MB)"] = "N/A"
            row_data["Nodes Backtrack Pure"] = "N/A"
        else:
            env_bt = load_env_from_file(file_path)
            res, elapsed, mem_used = run_algorithm_with_memory(
                solve_backtracking, env_bt.grid, n, env_bt.horiz_constraints, env_bt.vert_constraints
            )
            row_data["Backtrack Pure (s)"] = round(elapsed, 4)
            row_data["Backtrack Pure (MB)"] = round(mem_used, 2)
            row_data["Nodes Backtrack Pure"] = extract_nodes(res)

        # 3. BACKTRACKING + FORWARD CHAINING
        env_btf = load_env_from_file(file_path)
        kb_btf = KB_BTF(n)
        for r in range(n):
            for c in range(n):
                if env_btf.grid[r][c] != 0:
                    kb_btf.domains[r][c] = {env_btf.grid[r][c]}
                    kb_btf.facts.append((r, c, env_btf.grid[r][c]))
        gc.collect()
        mem_before = measure_memory()
        st = time.time()
        fc_init = FC_BTF(kb_btf, env_btf)
        if fc_init.execute():
            res = solve_with_bfc(kb_btf, env_btf) 
            row_data["Nodes Backtrack+FC"] = extract_nodes(res)
        else:
            row_data["Nodes Backtrack+FC"] = "N/A"
        elapsed = time.time() - st
        mem_after = measure_memory()
        row_data["Backtrack+FC (s)"] = round(elapsed, 4)
        row_data["Backtrack+FC (MB)"] = round(abs(mem_after - mem_before), 2)

        # 4. BACKWARD CHAINING (SLD)
        if n >= 9:
            row_data["Backward Chaining (s)"] = "Timeout"
            row_data["Backward Chaining (MB)"] = "N/A"
            row_data["Nodes Backward"] = "N/A"
        else:
            env_bw = load_env_from_file(file_path)
            sld = SLDResolutionEngine(env_bw)
            gc.collect()
            mem_before = measure_memory()
            st = time.time()
            sld.prove_board()
            elapsed = time.time() - st
            mem_after = measure_memory()
            row_data["Backward Chaining (s)"] = round(elapsed, 4)
            row_data["Backward Chaining (MB)"] = round(abs(mem_after - mem_before), 2)
            row_data["Nodes Backward"] = getattr(sld, 'nodes_expanded', "N/A")

        # 5. PURE FORWARD CHAINING
        env_fc = load_env_from_file(file_path)
        gc.collect()
        mem_before = measure_memory()
        st = time.time()
        solve_pure_fc(env_fc)
        elapsed = time.time() - st
        mem_after = measure_memory()
        row_data["Pure FC (s)"] = round(elapsed, 4)
        row_data["Pure FC (MB)"] = round(abs(mem_after - mem_before), 2)

        # 6. ASTAR PURE VARIANTS
        if n >= 9:
            row_data["A* AC3 (s)"] = "Timeout"
            row_data["A* AC3 (MB)"] = "N/A"
            row_data["A* MBDT (s)"] = "Timeout"
            row_data["A* MBDT (MB)"] = "N/A"
            row_data["A* MRC (s)"] = "Timeout"
            row_data["A* MRC (MB)"] = "N/A"
            row_data["Nodes AC3"] = row_data["Nodes MBDT"] = row_data["Nodes MRC"] = "N/A"
        else:
            env_a = load_env_from_file(file_path)
            res_a, elapsed_a, mem_a = run_algorithm_with_memory(
                solve_astar_ac3, env_a.grid, n, env_a.horiz_constraints, env_a.vert_constraints
            )
            row_data["A* AC3 (s)"] = round(elapsed_a, 4)
            row_data["A* AC3 (MB)"] = round(mem_a, 2)
            row_data["Nodes AC3"] = extract_nodes(res_a)
            
            env_b = load_env_from_file(file_path)
            res_b, elapsed_b, mem_b = run_algorithm_with_memory(
                solve_astar_mbdt, env_b.grid, n, env_b.horiz_constraints, env_b.vert_constraints
            )
            row_data["A* MBDT (s)"] = round(elapsed_b, 4)
            row_data["A* MBDT (MB)"] = round(mem_b, 2)
            row_data["Nodes MBDT"] = extract_nodes(res_b)
            
            env_c = load_env_from_file(file_path)
            res_c, elapsed_c, mem_c = run_algorithm_with_memory(
                solve_astar_mrc, env_c.grid, n, env_c.horiz_constraints, env_c.vert_constraints
            )
            row_data["A* MRC (s)"] = round(elapsed_c, 4)
            row_data["A* MRC (MB)"] = round(mem_c, 2)
            row_data["Nodes MRC"] = extract_nodes(res_c)

        # 7. ASTAR + MAC VARIANTS
        env_mac_ac3 = load_env_from_file(file_path)
        gc.collect()
        mem_before = measure_memory()
        st = time.time()
        _, nd_ac3 = solve_astar_mac_ac3(env_mac_ac3)
        elapsed_mac_ac3 = time.time() - st
        mem_after = measure_memory()
        row_data["A* MAC AC3 (s)"] = round(elapsed_mac_ac3, 4)
        row_data["A* MAC AC3 (MB)"] = round(abs(mem_after - mem_before), 2)
        row_data["Nodes MAC AC3"] = nd_ac3
        
        env_mac_mbdt = load_env_from_file(file_path)
        gc.collect()
        mem_before = measure_memory()
        st = time.time()
        _, nd_mbdt = solve_astar_mac_mbdt(env_mac_mbdt)
        elapsed_mac_mbdt = time.time() - st
        mem_after = measure_memory()
        row_data["A* MAC MBDT (s)"] = round(elapsed_mac_mbdt, 4)
        row_data["A* MAC MBDT (MB)"] = round(abs(mem_after - mem_before), 2)
        row_data["Nodes MAC MBDT"] = nd_mbdt
        
        env_mac_mrc = load_env_from_file(file_path)
        gc.collect()
        mem_before = measure_memory()
        st = time.time()
        _, nd_mrc = solve_astar_mac_mrc(env_mac_mrc)
        elapsed_mac_mrc = time.time() - st
        mem_after = measure_memory()
        row_data["A* MAC MRC (s)"] = round(elapsed_mac_mrc, 4)
        row_data["A* MAC MRC (MB)"] = round(abs(mem_after - mem_before), 2)
        row_data["Nodes MAC MRC"] = nd_mrc

        # 8. SAT SOLVER
        sat = FutoshikiSATSolver(load_env_from_file(file_path))
        gc.collect()
        mem_before = measure_memory()
        st = time.time()
        solution, decisions = sat.solve() 
        elapsed_sat = time.time() - st
        mem_after = measure_memory()
        row_data["SAT (s)"] = round(elapsed_sat, 4)
        row_data["SAT (MB)"] = round(abs(mem_after - mem_before), 2)
        row_data["Nodes SAT (Decisions)"] = decisions
        row_data["SAT Clauses"] = len(sat.cnf_strings) if hasattr(sat, 'cnf_strings') else "N/A"

        results.append(row_data)

    # --- XUẤT RA FILE CSV ---
    print("\nĐANG XUẤT DỮ LIỆU RA FILE CSV VỚI MEMORY TRACKING...")
    
    # Định nghĩa cấu trúc cột (Đã bổ sung các cột Memory)
    fieldnames = [
        "File", "Size", 
        "BruteForce (s)", "BruteForce (MB)", "Nodes BruteForce",
        "Backtrack Pure (s)", "Backtrack Pure (MB)", "Nodes Backtrack Pure", 
        "Backtrack+FC (s)", "Backtrack+FC (MB)", "Nodes Backtrack+FC",
        "Backward Chaining (s)", "Backward Chaining (MB)", "Nodes Backward", 
        "Pure FC (s)", "Pure FC (MB)",
        "A* AC3 (s)", "A* AC3 (MB)", "Nodes AC3", 
        "A* MBDT (s)", "A* MBDT (MB)", "Nodes MBDT", 
        "A* MRC (s)", "A* MRC (MB)", "Nodes MRC",
        "A* MAC AC3 (s)", "A* MAC AC3 (MB)", "Nodes MAC AC3", 
        "A* MAC MBDT (s)", "A* MAC MBDT (MB)", "Nodes MAC MBDT", 
        "A* MAC MRC (s)", "A* MAC MRC (MB)", "Nodes MAC MRC",
        "SAT (s)", "SAT (MB)", "Nodes SAT (Decisions)", "SAT Clauses"
    ]
    
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"🎉 HOÀN TẤT! Đã lưu báo cáo tại: {output_csv}")
    print(f"📊 CSV chứa {len(fieldnames)} cột và {len(results)} hàng dữ liệu")
    print("✅ Memory tracking đã được tích hợp thành công!")

if __name__ == "__main__":
    run_benchmark()