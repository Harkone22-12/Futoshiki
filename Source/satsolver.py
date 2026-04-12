import time
import os
import re
from futoshiki_env import FutoshikiEnv
from KB_generator import KBGenerator
from pysat.solvers import Glucose3

file_path = "Source/Inputs/input-01.txt"

# ==========================================
# 2. CLASS SAT SOLVER (GIẢI BẰNG PURE LOGIC / CNF)
# ==========================================
class FutoshikiSATSolver:
    def __init__(self, env):
        self.env = env
        self.n = env.n
        self.solver = Glucose3() # Khởi tạo cỗ máy suy diễn logic Glucose3
        self.cnf_strings = []
        self.kb_gen = KBGenerator(env)  # Sử dụng KB Generator
        
    def var_id(self, r, c, v):
        """Ánh xạ trạng thái Val(r, c, v) thành 1 số nguyên dương duy nhất."""
        return (r - 1) * self.n * self.n + (c - 1) * self.n + v
    
    def clause_to_string(self, clause):
        """Dịch ngược từ mảng số [-2, -11] thành chuỗi '~Val_1_1_2 V ~Val_1_2_2'"""
        str_vars = []
        for var in clause:
            is_neg = var < 0
            abs_var = abs(var)
            v = (abs_var - 1) % self.n + 1
            c = ((abs_var - 1) // self.n) % self.n + 1
            r = ((abs_var - 1) // (self.n * self.n)) + 1
            
            prefix = "~" if is_neg else ""
            str_vars.append(f"{prefix}Val_{r}_{c}_{v}")
        return " V ".join(str_vars)

    def string_to_clause(self, clause_str):
        """
        Dịch chuỗi CNF như '(Val(1,1,1) ∨ Val(1,1,2) ∨ ~Val(2,1,3))'
        thành danh sách ID biến có dấu [-2, 3, 4, ...]
        """
        # Lấy string đã strip
        clause_str = clause_str.strip()
        
        # Loại bỏ ngoặc đơn đầu và cuối (CHỈ một cặp)
        if clause_str.startswith('(') and clause_str.endswith(')'):
            clause_str = clause_str[1:-1]
        
        # Tách các literal qua dấu ∨ (chỉ dấu ∨, không phải V)
        # Hoặc split by ' V ' (V với spaces) để tránh tách từ trong Val
        literals = re.split(r'∨|\s+V\s+', clause_str)
        
        clause = []
        for lit in literals:
            lit = lit.strip()
            if not lit:
                continue
            
            # Kiểm tra negation
            is_neg = lit.startswith('¬') or lit.startswith('~')
            if is_neg:
                lit = lit[1:].strip()
            
            # Parse Val(r, c, v) - extract numbers inside Val(...)
            match = re.search(r'Val\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', lit)
            if match:
                r, c, v = int(match.group(1)), int(match.group(2)), int(match.group(3))
                var_id = self.var_id(r, c, v)
                clause.append(-var_id if is_neg else var_id)
        
        return clause

    def build_cnf_clauses(self):
        """
        Sử dụng KB_generator để sinh ra các mệnh đề CNF
        thay vì xây dựng chúng một cách thủ công.
        """
        self.cnf_strings.clear()
        
        # Generate ground axioms từ KB Generator
        grounded_axioms = self.kb_gen.ground_axioms()
        
        # Parse và add từng clause vào solver
        for clause_str in grounded_axioms:
            # Bỏ qua comment lines và empty lines
            if clause_str.startswith("#") or not clause_str.strip():
                continue
            
            # Convert string clause to integer clause
            clause = self.string_to_clause(clause_str)
            if clause:  # Nếu clause không rỗng
                self.solver.add_clause(clause)
                self.cnf_strings.append(clause_str)

    def solve(self):
        """Kích hoạt SAT Solver và dịch mảng kết quả thành Grid."""
        self.build_cnf_clauses()
        
        if self.solver.solve():
            model = self.solver.get_model()
            
            # ĐÃ XÓA DÒNG PRINT Ở ĐÂY. Chỉ ngầm lấy số liệu để truyền ra ngoài.
            stats = self.solver.accum_stats()
            decisions = stats['decisions'] 

            solution_grid = [[0 for _ in range(self.n)] for _ in range(self.n)]
            for var in model:
                if var > 0: # Chỉ lấy các mệnh đề Đúng (True)
                    v = (var - 1) % self.n + 1
                    c = ((var - 1) // self.n) % self.n + 1
                    r = ((var - 1) // (self.n * self.n)) + 1
                    solution_grid[r - 1][c - 1] = v
                    
            return solution_grid, decisions
        else:
            # Nếu vô nghiệm, vẫn trả về decisions để đo xem đã tìm bao nhiêu node rồi bỏ cuộc
            stats = self.solver.accum_stats()
            return None, stats['decisions'] 


# ==========================================
# 3. HELPER FUNCTIONS & MAIN EXECUTION
# ==========================================
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

def print_solution(n, grid, env):
    for i in range(n):
        row_str = ""
        for j in range(n):
            row_str += str(grid[i][j])
            if j < n - 1:
                if env.horiz_constraints[i][j] == 1: row_str += " < "
                elif env.horiz_constraints[i][j] == -1: row_str += " > "
                else: row_str += "   "
        print(row_str)
        if i < n - 1:
            v_str = ""
            for j in range(n):
                if env.vert_constraints[i][j] == 1: v_str += "^   "
                elif env.vert_constraints[i][j] == -1: v_str += "v   "
                else: v_str += "    "
            print(v_str.rstrip())

def save_solution_to_file(output_path, n, grid, env):
    """Hàm lưu kết quả ra file text với đầy đủ định dạng."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(n):
            row_str = ""
            for j in range(n):
                row_str += str(grid[i][j]) if grid[i][j] != 0 else "."
                if j < n - 1:
                    if env.horiz_constraints[i][j] == 1: row_str += " < "
                    elif env.horiz_constraints[i][j] == -1: row_str += " > "
                    else: row_str += "   "
            f.write(row_str + "\n")
            
            if i < n - 1:
                v_str = ""
                for j in range(n):
                    if env.vert_constraints[i][j] == 1: v_str += "^   "
                    elif env.vert_constraints[i][j] == -1: v_str += "v   "
                    else: v_str += "    "
                f.write(v_str.rstrip() + "\n")

if __name__ == "__main__":
    input_file = file_path
    
    # --- TỰ ĐỘNG SINH ĐƯỜNG DẪN OUTPUT ---
    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Source", "Outputs", file_name)
    
    try:
        env = load_env_from_file(input_file)
        print(f"[*] Solving Futoshiki {env.n}x{env.n} using SAT SOLVER (Pysat/Glucose3)")
        
        sat_solver = FutoshikiSATSolver(env)
        sat_solver.build_cnf_clauses()

        total_clauses = len(sat_solver.cnf_strings)
        print(f"[+] SAT Solver created {total_clauses} CNF clauses.")

        os.makedirs("Source/Outputs", exist_ok=True)
        with open("Source/Outputs/cnf_clauses_log.txt", "w", encoding="utf-8") as f:
            f.write(f"TOTAL CNF CLAUSES: {total_clauses}\n")
            f.write("\n".join(sat_solver.cnf_strings))
        print("[+] Saved CNF clauses to 'Source/Outputs/cnf_clauses_log.txt'")
        
        start_time = time.time()
        
        # Unpack tuple
        solution, decisions = sat_solver.solve()
        
        end_time = time.time()
        
        if solution:
            print(f"\n[SUCCESS] Futoshiki Solved!")
            print_solution(env.n, solution, env)
            print(f"\nTime: {end_time - start_time:.4f}s")
            print(f"Decisions made: {decisions}")
            
            save_solution_to_file(output_file, env.n, solution, env)
            print(f"[+] Solution saved to: {output_file}")
            
        else:
            print("\n[UNSAT] No solution found.")
            print(f"Decisions explored: {decisions}")
            
    except FileNotFoundError:
        print(f"[ERROR] File not found: {input_file}.")
    except ImportError:
        print("[ERROR] Missing required library 'python-sat'.")
        print("Install with: pip install python-sat")