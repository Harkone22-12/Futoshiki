import os
import time
import csv

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

def run_benchmark():
    input_folder = "Source/Inputs" 
    output_folder = "Source/Benchmarks"
    os.makedirs(output_folder, exist_ok=True)
    output_csv = os.path.join(output_folder, "benchmark_results_full.csv")

    files = [f for f in os.listdir(input_folder) if f.startswith("input") and f.endswith(".txt")]
    files.sort()

    results = []

    print(f"BẮT ĐẦU CHẠY BENCHMARK TOÀN DIỆN TRÊN {len(files)} FILE...")
    print("Cảnh báo: Quá trình này có thể mất vài phút. Vui lòng kiên nhẫn đợi!")
    print("-" * 80)

    for filename in files:
        file_path = os.path.join(input_folder, filename)
        env = load_env_from_file(file_path)
        n = env.n
        print(f"Đang xử lý: {filename} (Size: {n}x{n})")

        row_data = {"File": filename, "Size": f"{n}x{n}"}

        # 1. BRUTE FORCE
        if n >= 4:
            row_data["BruteForce (s)"] = "Timeout"
            row_data["Nodes BruteForce"] = "N/A"
        else:
            env_bf = load_env_from_file(file_path)
            st = time.time()
            res = solve_bruteforce(env_bf.grid, n, env_bf.horiz_constraints, env_bf.vert_constraints)
            row_data["BruteForce (s)"] = round(time.time() - st, 4)
            row_data["Nodes BruteForce"] = extract_nodes(res)

        # 2. BACKTRACKING PURE
        if n >= 8:
            row_data["Backtrack Pure (s)"] = "Timeout"
            row_data["Nodes Backtrack Pure"] = "N/A"
        else:
            env_bt = load_env_from_file(file_path)
            st = time.time()
            res = solve_backtracking(env_bt.grid, n, env_bt.horiz_constraints, env_bt.vert_constraints)
            row_data["Backtrack Pure (s)"] = round(time.time() - st, 4)
            row_data["Nodes Backtrack Pure"] = extract_nodes(res)

        # 3. BACKTRACKING + FORWARD CHAINING
        env_btf = load_env_from_file(file_path)
        kb_btf = KB_BTF(n)
        for r in range(n):
            for c in range(n):
                if env_btf.grid[r][c] != 0:
                    kb_btf.domains[r][c] = {env_btf.grid[r][c]}
                    kb_btf.facts.append((r, c, env_btf.grid[r][c]))
        st = time.time()
        fc_init = FC_BTF(kb_btf, env_btf)
        if fc_init.execute():
            res = solve_with_bfc(kb_btf, env_btf) 
            row_data["Nodes Backtrack+FC"] = extract_nodes(res)
        else:
            row_data["Nodes Backtrack+FC"] = "N/A"
        row_data["Backtrack+FC (s)"] = round(time.time() - st, 4)

        # 4. BACKWARD CHAINING (SLD)
        if n >= 9:
            row_data["Backward Chaining (s)"] = "Timeout"
            row_data["Nodes Backward"] = "N/A"
        else:
            env_bw = load_env_from_file(file_path)
            sld = SLDResolutionEngine(env_bw)
            st = time.time()
            sld.prove_board() # Nếu bạn có đếm node trong class này, hãy trích xuất ở đây
            row_data["Backward Chaining (s)"] = round(time.time() - st, 4)
            row_data["Nodes Backward"] = getattr(sld, 'nodes_expanded', "N/A")

        # 5. PURE FORWARD CHAINING (Không rẽ nhánh nên số Node = 0 hoặc N/A)
        env_fc = load_env_from_file(file_path)
        st = time.time()
        solve_pure_fc(env_fc)
        row_data["Pure FC (s)"] = round(time.time() - st, 4)

        # 6. ASTAR PURE VARIANTS
        if n >= 9:
            row_data["A* AC3 (s)"] = row_data["A* MBDT (s)"] = row_data["A* MRC (s)"] = "Timeout"
            row_data["Nodes AC3"] = row_data["Nodes MBDT"] = row_data["Nodes MRC"] = "N/A"
        else:
            env_a = load_env_from_file(file_path)
            st = time.time()
            res_a = solve_astar_ac3(env_a.grid, n, env_a.horiz_constraints, env_a.vert_constraints)
            row_data["A* AC3 (s)"] = round(time.time() - st, 4)
            row_data["Nodes AC3"] = extract_nodes(res_a)
            
            env_b = load_env_from_file(file_path)
            st = time.time()
            res_b = solve_astar_mbdt(env_b.grid, n, env_b.horiz_constraints, env_b.vert_constraints)
            row_data["A* MBDT (s)"] = round(time.time() - st, 4)
            row_data["Nodes MBDT"] = extract_nodes(res_b)
            
            env_c = load_env_from_file(file_path)
            st = time.time()
            res_c = solve_astar_mrc(env_c.grid, n, env_c.horiz_constraints, env_c.vert_constraints)
            row_data["A* MRC (s)"] = round(time.time() - st, 4)
            row_data["Nodes MRC"] = extract_nodes(res_c)

        # 7. ASTAR + MAC VARIANTS
        env_mac_ac3 = load_env_from_file(file_path)
        st = time.time()
        _, nd_ac3 = solve_astar_mac_ac3(env_mac_ac3)
        row_data["A* MAC AC3 (s)"] = round(time.time() - st, 4)
        row_data["Nodes MAC AC3"] = nd_ac3
        
        env_mac_mbdt = load_env_from_file(file_path)
        st = time.time()
        _, nd_mbdt = solve_astar_mac_mbdt(env_mac_mbdt)
        row_data["A* MAC MBDT (s)"] = round(time.time() - st, 4)
        row_data["Nodes MAC MBDT"] = nd_mbdt
        
        env_mac_mrc = load_env_from_file(file_path)
        st = time.time()
        _, nd_mrc = solve_astar_mac_mrc(env_mac_mrc)
        row_data["A* MAC MRC (s)"] = round(time.time() - st, 4)
        row_data["Nodes MAC MRC"] = nd_mrc

        # 8. SAT SOLVER
        sat = FutoshikiSATSolver(load_env_from_file(file_path))
        st = time.time()
        solution, decisions = sat.solve() 
        
        row_data["SAT (s)"] = round(time.time() - st, 4)
        row_data["Nodes SAT (Decisions)"] = decisions # Lưu số Node vào row_data
        row_data["SAT Clauses"] = len(sat.cnf_strings) if hasattr(sat, 'cnf_strings') else "N/A"

        results.append(row_data)

    # --- XUẤT RA FILE CSV ---
    print("\nĐANG XUẤT DỮ LIỆU RA FILE CSV...")
    
    # Định nghĩa cấu trúc cột (Đã bổ sung các cột Nodes)
    fieldnames = [
        "File", "Size", 
        "BruteForce (s)", "Nodes BruteForce",
        "Backtrack Pure (s)", "Nodes Backtrack Pure", 
        "Backtrack+FC (s)", "Nodes Backtrack+FC",
        "Backward Chaining (s)", "Nodes Backward", 
        "Pure FC (s)", 
        "A* AC3 (s)", "Nodes AC3", 
        "A* MBDT (s)", "Nodes MBDT", 
        "A* MRC (s)", "Nodes MRC",
        "A* MAC AC3 (s)", "Nodes MAC AC3", 
        "A* MAC MBDT (s)", "Nodes MAC MBDT", 
        "A* MAC MRC (s)", "Nodes MAC MRC",
        "SAT (s)", "Nodes SAT (Decisions)", "SAT Clauses"
    ]
    
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"🎉 HOÀN TẤT! Đã lưu báo cáo tại: {output_csv}")

if __name__ == "__main__":
    run_benchmark()