import time
import os
from futoshiki_env import FutoshikiEnv
from pysat.solvers import Glucose3

# ==========================================
# 2. CLASS SAT SOLVER (GIẢI BẰNG PURE LOGIC / CNF)
# ==========================================
class FutoshikiSATSolver:
    def __init__(self, env):
        self.env = env
        self.n = env.n
        self.solver = Glucose3() # Khởi tạo cỗ máy suy diễn logic Glucose3
        self.cnf_strings = [] 
        
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

    def build_cnf_clauses(self):
        """Dịch tất cả các Axioms thành Mệnh đề chuẩn CNF và nạp vào Solver."""
        self.cnf_strings.clear()
        
        def add_and_record(clause):
            self.solver.add_clause(clause)
            self.cnf_strings.append(self.clause_to_string(clause))
        
        # A1: Mọi ô phải có ÍT NHẤT 1 giá trị
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                clause = [self.var_id(r, c, v) for v in range(1, self.n + 1)]
                add_and_record(clause)

        # A2: Mọi ô có TỐI ĐA 1 giá trị
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                for v1 in range(1, self.n + 1):
                    for v2 in range(v1 + 1, self.n + 1):
                        add_and_record([-self.var_id(r, c, v1), -self.var_id(r, c, v2)])

        # A3 & A3b: Duy nhất trên Hàng và Cột
        for v in range(1, self.n + 1):
            for i in range(1, self.n + 1):
                for j1 in range(1, self.n + 1):
                    for j2 in range(j1 + 1, self.n + 1):
                        add_and_record([-self.var_id(i, j1, v), -self.var_id(i, j2, v)]) # Hàng
                        add_and_record([-self.var_id(j1, i, v), -self.var_id(j2, i, v)]) # Cột

        # A5: Sự thật hiển nhiên (Given Clues từ Env)
        for r in range(self.n):
            for c in range(self.n):
                val = self.env.grid[r][c]
                if val != 0:
                    add_and_record([self.var_id(r + 1, c + 1, val)])

        # A4 & A6: Ràng buộc Ngang (Horizontal Constraints)
        for r in range(self.n):
            for c in range(self.n - 1):
                ctype = self.env.horiz_constraints[r][c]
                if ctype != 0:
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if ctype == 1 and v1 >= v2:    # Dấu <
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 1, c + 2, v2)])
                            elif ctype == -1 and v1 <= v2: # Dấu >
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 1, c + 2, v2)])

        # A8 & A9: Ràng buộc Dọc (Vertical Constraints)
        for r in range(self.n - 1):
            for c in range(self.n):
                ctype = self.env.vert_constraints[r][c]
                if ctype != 0:
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if ctype == 1 and v1 >= v2:    # Dấu ^ (top < bottom)
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 2, c + 1, v2)])
                            elif ctype == -1 and v1 <= v2: # Dấu v (top > bottom)
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 2, c + 1, v2)])

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
    # Thay đổi đường dẫn file input ở đây
    input_file = "Source/Inputs/input-10.txt"
    
    # --- TỰ ĐỘNG SINH ĐƯỜNG DẪN OUTPUT ---
    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Source", "Outputs", file_name)
    
    try:
        env = load_env_from_file(input_file)
        print(f"--- Đang giải Futoshiki {env.n}x{env.n} bằng SAT SOLVER (Pysat/Glucose3) ---")
        
        sat_solver = FutoshikiSATSolver(env)
        sat_solver.build_cnf_clauses()

        total_clauses = len(sat_solver.cnf_strings)
        print(f"-> SAT Solver đã tạo ra {total_clauses} mệnh đề CNF.")

        os.makedirs("Source/Outputs", exist_ok=True)
        with open("Source/Outputs/cnf_clauses_log.txt", "w", encoding="utf-8") as f:
            f.write(f"TỔNG SỐ MỆNH ĐỀ CNF: {total_clauses}\n")
            f.write("\n".join(sat_solver.cnf_strings))
        print("-> Đã lưu toàn bộ Ground KB (CNF) ra file 'Source/Outputs/cnf_clauses_log.txt'")
        
        start_time = time.time()
        
        # GỠ GÓI TUPLE
        solution, decisions = sat_solver.solve()
        
        end_time = time.time()
        
        if solution:
            print(f"\n======= KẾT QUẢ FUTOSHIKI =======")
            print_solution(env.n, solution, env)
            print(f"\nTIME: {end_time - start_time:.4f}s")
            print(f"Số Node đã mở rộng (Decisions count): {decisions}")
            
            save_solution_to_file(output_file, env.n, solution, env)
            print(f"--> Đã lưu kết quả thành công vào: {output_file}")
            
        else:
            print("\nSAT Solver kết luận: BÀI TOÁN VÔ NGHIỆM.")
            print(f"Số Node đã duyệt trước khi kết luận: {decisions}")
            
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {input_file}.")
    except ImportError:
        print("Lỗi: Bạn chưa cài thư viện 'python-sat'.")
        print("Vui lòng mở Terminal và chạy lệnh: pip install python-sat")