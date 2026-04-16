import time
import os
from futoshiki_env import FutoshikiEnv
file_path = "Source/Inputs/input-01.txt"

class SLDResolutionEngine:
    def __init__(self, env):
        self.env = env
        self.n = env.n
        # Working Memory để lưu các biến đã được Unify
        self.grid = [[env.grid[i][j] for j in range(self.n)] for i in range(self.n)]
        self.is_solved = False # Cờ đánh dấu đã chứng minh xong toàn bộ bảng
        self.nodes_expanded = 0

   # Sub-goals
    def goal_alldiff_row(self, r, c, val):
        """Rule: Giá trị val không được trùng lặp trên hàng r."""
        for i in range(self.n):
            if self.grid[r][i] == val: return False
        return True

    def goal_alldiff_col(self, r, c, val):
        """Rule: Giá trị val không được trùng lặp trên cột c."""
        for i in range(self.n):
            if self.grid[i][c] == val: return False
        return True

    def goal_inequalities(self, r, c, val):
        """Rule: Bất đẳng thức ngang và dọc phải được thỏa mãn."""
        # Ngang
        if c > 0 and self.grid[r][c-1] != 0:
            if self.env.horiz_constraints[r][c-1] == 1 and not (self.grid[r][c-1] < val): return False
            if self.env.horiz_constraints[r][c-1] == -1 and not (self.grid[r][c-1] > val): return False
        if c < self.n - 1 and self.grid[r][c+1] != 0:
            if self.env.horiz_constraints[r][c] == 1 and not (val < self.grid[r][c+1]): return False
            if self.env.horiz_constraints[r][c] == -1 and not (val > self.grid[r][c+1]): return False
            
        # Dọc
        if r > 0 and self.grid[r-1][c] != 0:
            if self.env.vert_constraints[r-1][c] == 1 and not (self.grid[r-1][c] < val): return False
            if self.env.vert_constraints[r-1][c] == -1 and not (self.grid[r-1][c] > val): return False
        if r < self.n - 1 and self.grid[r+1][c] != 0:
            if self.env.vert_constraints[r][c] == 1 and not (val < self.grid[r+1][c]): return False
            if self.env.vert_constraints[r][c] == -1 and not (val > self.grid[r+1][c]): return False
        
        return True

    def check_all_subgoals(self, r, c, val):
        """Gộp các subgoals lại (Toán tử AND trong Prolog)."""
        return self.goal_alldiff_row(r, c, val) and \
               self.goal_alldiff_col(r, c, val) and \
               self.goal_inequalities(r, c, val)

    # Chứng minh đệ quy
    def prove_board(self, r=0, c=0):
        """
        Hàm đệ quy chứng minh toàn bộ bảng. 
        Tương đương với SLD Tree Traversal.
        """
        self.nodes_expanded += 1
        # Base case: Nếu đã duyệt qua hết bảng -> C/m thành công (Tautology)
        if r == self.n:
            return True
            
        next_r, next_c = (r, c + 1) if c < self.n - 1 else (r + 1, 0)

        # Clause 1: Nếu ô đã là Fact (Given từ đề bài), đi tiếp không cần gán
        if self.env.grid[r][c] != 0:
            self.grid[r][c] = self.env.grid[r][c]
            return self.prove_board(next_r, next_c)

        # Clause 2: Nếu ô trống, thực hiện Unification (Gán thử giá trị V)
        for v in range(1, self.n + 1):
            # Nếu tất cả các Subgoals (Tiền đề) đều True
            if self.check_all_subgoals(r, c, v):
                # Unify biến
                self.grid[r][c] = v
                
                # Gọi đệ quy để chứng minh các node con trong SLD Tree
                if self.prove_board(next_r, next_c):
                    return True
                    
                # Hủy Unify nếu nhánh chứng minh thất bại (Backtracking)
                self.grid[r][c] = 0
                
        return False # Fail mục tiêu

    # Truy vấn
    def query_value(self, r, c):
        """
        Prolog-style Query: ?- Val(r, c, V).
        Hệ thống sẽ chạy chứng minh và trả về V.
        """
        print(f"?- Val({r}, {c}, V).")
        
        # Chỉ chạy SLD Resolution 1 lần, nếu đã có kết quả thì dùng
        if not self.is_solved:
            if self.prove_board():
                self.is_solved = True
            else:
                print("-> False. (Bài toán không có nghiệm)")
                return None
                
        # Trích xuất giá trị V đã được hệ thống "chứng minh" thành công
        val = self.grid[r][c]
        print(f"-> Hệ thống SLD suy diễn: V = {val}")
        return val

# Helpers với main
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
    input_file = file_path # Đổi lại file test tại đây
    
    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Source", "Outputs", file_name)
    
    try:
        env = load_env_from_file(input_file)
        print(f"--- MÔ PHỎNG PROLOG SLD RESOLUTION (Bảng {env.n}x{env.n}) ---")
        
        sld_engine = SLDResolutionEngine(env)
        
        print("\n=== DEMO TRUY VẤN THEO YÊU CẦU ĐỒ ÁN ===")
        print("Người dùng nhập câu lệnh truy vấn giá trị của các ô (Prolog Query):")
        
        # Biểu diễn việc truy vấn vài ô bất kỳ
        start_time = time.time()
        
        sld_engine.query_value(0, 0)  # Truy vấn ô góc trên cùng bên trái
        sld_engine.query_value(0, 1)  # Truy vấn ô kế bên
        sld_engine.query_value(env.n - 1, env.n - 1)  # Truy vấn ô góc dưới cùng bên phải
        
        print(f"\n[Thời gian chứng minh (Resolution Time): {time.time() - start_time:.4f}s]")
        print(f"[Số Node đã mở rộng trong quá trình suy diễn: {sld_engine.nodes_expanded}]")
        
        print("\n=== KẾT QUẢ TOÀN BỘ BẢNG TỪ WORKING MEMORY ===")
        for row in sld_engine.grid:
            print(row)
            
        # --- LƯU RA FILE ---
        if sld_engine.is_solved:
            save_solution_to_file(output_file, env.n, sld_engine.grid, env)
            print(f"\n--> Đã lưu kết quả thành công vào: {output_file}")
            
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {input_file}.")