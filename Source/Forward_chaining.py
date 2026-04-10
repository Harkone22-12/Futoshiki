import time
import os
from futoshiki_env import FutoshikiEnv

# ==========================================
# 1. CLASS KNOWLEDGE BASE
# ==========================================
class KnowledgeBase:
    def __init__(self, n):
        self.n = n
        # Khởi tạo domain cho mọi ô là tập hợp {1, 2, ..., n}
        self.domains = [[set(range(1, n + 1)) for _ in range(n)] for _ in range(n)]
        self.facts = [] # Chứa các tuple (r, c, val) đã được chốt từ đề bài

# ==========================================
# 2. CLASS FORWARD CHAINING (GIỮ NGUYÊN CODE CỦA BẠN)
# ==========================================
class ForwardChaining:
    def __init__(self, kb, env):
        self.kb = kb
        self.env = env
        self.n = env.n

    def execute(self):
        """
        Thực thi thuật toán Forward Chaining.
        Trả về True nếu suy diễn thành công (không có mâu thuẫn).
        Trả về False nếu phát hiện mâu thuẫn logic (domain rỗng).
        """
        # Khởi tạo hàng đợi với các sự kiện ban đầu từ KB
        agenda = self.kb.facts.copy()
        
        while agenda:
            r, c, val = agenda.pop(0)
            
            # --- 1. Áp dụng luật All-Different (Hàng và Cột) ---
            for i in range(self.n):
                # Thu hẹp domain trên cùng Cột
                if i != r and val in self.kb.domains[i][c]:
                    self.kb.domains[i][c].remove(val)
                    if len(self.kb.domains[i][c]) == 1:
                        agenda.append((i, c, list(self.kb.domains[i][c])[0]))
                    elif len(self.kb.domains[i][c]) == 0:
                        return False

                # Thu hẹp domain trên cùng Hàng
                if i != c and val in self.kb.domains[r][i]:
                    self.kb.domains[r][i].remove(val)
                    if len(self.kb.domains[r][i]) == 1:
                        agenda.append((r, i, list(self.kb.domains[r][i])[0]))
                    elif len(self.kb.domains[r][i]) == 0:
                        return False

            # --- 2. Áp dụng luật Bất đẳng thức ---
            for constraint in self.env.constraints_list:
                ctype, r1, c1, r2, c2 = constraint
                
                # TH1: Sự kiện hiện tại nằm ở Vế Trái của bất đẳng thức
                if r == r1 and c == c1:
                    to_remove = []
                    for v2 in self.kb.domains[r2][c2]:
                        if (ctype == '<' and not (val < v2)) or (ctype == '>' and not (val > v2)):
                            to_remove.append(v2)
                            
                    for v2 in to_remove:
                        self.kb.domains[r2][c2].remove(v2)
                        if len(self.kb.domains[r2][c2]) == 1:
                            agenda.append((r2, c2, list(self.kb.domains[r2][c2])[0]))
                        elif len(self.kb.domains[r2][c2]) == 0:
                            return False

                # TH2: Sự kiện hiện tại nằm ở Vế Phải của bất đẳng thức
                elif r == r2 and c == c2:
                    to_remove = []
                    for v1 in self.kb.domains[r1][c1]:
                        if (ctype == '<' and not (v1 < val)) or (ctype == '>' and not (v1 > val)):
                            to_remove.append(v1)
                            
                    for v1 in to_remove:
                        self.kb.domains[r1][c1].remove(v1)
                        if len(self.kb.domains[r1][c1]) == 1:
                            agenda.append((r1, c1, list(self.kb.domains[r1][c1])[0]))
                        elif len(self.kb.domains[r1][c1]) == 0:
                            return False
                            
        return True

# ==========================================
# 3. HÀM CHẠY PURE FORWARD CHAINING
# ==========================================
def solve_pure_fc(env):
    """
    Chỉ dùng Pure Forward Chaining để giải bảng.
    """
    kb = KnowledgeBase(env.n)
    
    # 1. Đưa dữ kiện ban đầu (Givens) vào Knowledge Base
    for r in range(env.n):
        for c in range(env.n):
            if env.grid[r][c] != 0:
                kb.domains[r][c] = {env.grid[r][c]}
                kb.facts.append((r, c, env.grid[r][c]))

    # 2. Chạy cơ chế suy diễn Forward Chaining
    fc = ForwardChaining(kb, env)
    success = fc.execute()

    # 3. Kiểm tra kết quả
    if not success:
        return None, "Vô nghiệm ngay từ đầu (Mâu thuẫn logic)."

    # 4. Kiểm tra xem toàn bộ các ô đã về đúng 1 giá trị chưa
    solution_grid = [[0 for _ in range(env.n)] for _ in range(env.n)]
    for r in range(env.n):
        for c in range(env.n):
            if len(kb.domains[r][c]) == 1:
                solution_grid[r][c] = list(kb.domains[r][c])[0]
            else:
                # Nếu có bất kỳ ô nào vẫn còn > 1 sự lựa chọn -> Bị kẹt
                return None, "KHÔNG THỂ GIẢI ĐƯỢC chỉ bằng Pure FC (Cần thuật toán tìm kiếm rẽ nhánh)."

    return solution_grid, "Giải thành công!"

# ==========================================
# 4. HELPER FUNCTIONS & MAIN
# ==========================================
def load_env_from_file(file_path):
    with open(file_path, 'r') as f:
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
    input_file = r"Source/Inputs/input-11.txt" # Thay đổi file test ở đây

    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Source", "Outputs", file_name)
    
    try:
        env = load_env_from_file(input_file)
        print(f"--- Đang giải Futoshiki {env.n}x{env.n} bằng PURE FORWARD CHAINING ---")
        
        start_time = time.time()
        solution_grid, message = solve_pure_fc(env)
        end_time = time.time()

        if solution_grid:
            print(f"\n======= KẾT QUẢ TÌM THẤY TRONG {end_time - start_time:.4f}s =======")
            print_solution(env.n, solution_grid, env)

            save_solution_to_file(output_file, env.n, solution_grid, env)
            print(f"\n--> Đã lưu kết quả thành công vào: {output_file}")
        else:
            print(f"\n[Kết quả]: {message}")

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {input_file}.")