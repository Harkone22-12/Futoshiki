import time
import os
from futoshiki_env import FutoshikiEnv
file_path = "Inputs/input-08.txt"

class SLDResolutionEngine:
    def __init__(self, env):
        self.env = env
        self.n = env.n
        self.grid = [[env.grid[i][j] for j in range(self.n)] for i in range(self.n)]
        self.is_solved = False 
        self.nodes_expanded = 0

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
        if c > 0 and self.grid[r][c-1] != 0:
            if self.env.horiz_constraints[r][c-1] == 1 and not (self.grid[r][c-1] < val): return False
            if self.env.horiz_constraints[r][c-1] == -1 and not (self.grid[r][c-1] > val): return False
        if c < self.n - 1 and self.grid[r][c+1] != 0:
            if self.env.horiz_constraints[r][c] == 1 and not (val < self.grid[r][c+1]): return False
            if self.env.horiz_constraints[r][c] == -1 and not (val > self.grid[r][c+1]): return False
            
        if r > 0 and self.grid[r-1][c] != 0:
            if self.env.vert_constraints[r-1][c] == 1 and not (self.grid[r-1][c] < val): return False
            if self.env.vert_constraints[r-1][c] == -1 and not (self.grid[r-1][c] > val): return False
        if r < self.n - 1 and self.grid[r+1][c] != 0:
            if self.env.vert_constraints[r][c] == 1 and not (val < self.grid[r+1][c]): return False
            if self.env.vert_constraints[r][c] == -1 and not (val > self.grid[r+1][c]): return False
        
        return True

    def check_all_subgoals(self, r, c, val):
        return self.goal_alldiff_row(r, c, val) and \
               self.goal_alldiff_col(r, c, val) and \
               self.goal_inequalities(r, c, val)

    def prove_board(self, r=0, c=0):
        self.nodes_expanded += 1
        if r == self.n:
            return True
            
        next_r, next_c = (r, c + 1) if c < self.n - 1 else (r + 1, 0)

        if self.env.grid[r][c] != 0:
            self.grid[r][c] = self.env.grid[r][c]
            return self.prove_board(next_r, next_c)
        
        for v in range(1, self.n + 1):
            if self.check_all_subgoals(r, c, v):
                self.grid[r][c] = v
                
                if self.prove_board(next_r, next_c):
                    return True
                    
                self.grid[r][c] = 0
                
        return False 

    def query_value(self, r, c):
        """
        Prolog-style Query: ?- Val(r, c, V).
        Hệ thống sẽ chạy chứng minh và trả về V.
        """
        print(f"?- Val({r}, {c}, V).")
        
        if not self.is_solved:
            if self.prove_board():
                self.is_solved = True
            else:
                print("-> False. (Bài toán không có nghiệm)")
                return None
                
        val = self.grid[r][c]
        print(f"-> Hệ thống SLD suy diễn: V = {val}")
        return val

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


# AUTO QUERYING (3 QUERY)

if __name__ == "__main__":
    input_file = file_path
    
    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Outputs", file_name)
    
    try:
        env = load_env_from_file(input_file)
        print(f"--- MÔ PHỎNG PROLOG SLD RESOLUTION (Bảng {env.n}x{env.n}) ---")
        
        sld_engine = SLDResolutionEngine(env)
        
        print("\n=== DEMO TRUY VẤN THEO YÊU CẦU ĐỒ ÁN ===")
        print("Người dùng nhập câu lệnh truy vấn giá trị của các ô (Prolog Query):")
        
        start_time = time.time()
        
        sld_engine.query_value(0, 0)  
        sld_engine.query_value(0, 1)  
        sld_engine.query_value(env.n - 1, env.n - 1)  
        
        print(f"\n[Thời gian chứng minh (Resolution Time): {time.time() - start_time:.4f}s]")
        print(f"[Số Node đã mở rộng trong quá trình suy diễn: {sld_engine.nodes_expanded}]")
        
        print("\n=== KẾT QUẢ TOÀN BỘ BẢNG TỪ WORKING MEMORY ===")
        for row in sld_engine.grid:
            print(row)
            
        if sld_engine.is_solved:
            save_solution_to_file(output_file, env.n, sld_engine.grid, env)
            print(f"\n--> Đã lưu kết quả thành công vào: {output_file}")
            
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {input_file}.")


# INTERACTABLE QUERYING (uncomment the code below and comment the code above to use)

# if __name__ == "__main__":
#     input_file = file_path # Đổi lại file test của bạn
    
#     file_name = os.path.basename(input_file).replace("input", "output")
#     output_file = os.path.join("Source", "Outputs", file_name)
    
#     try:
#         env = load_env_from_file(input_file)
#         print(f"--- MÔ PHỎNG PROLOG SLD RESOLUTION (Bảng {env.n}x{env.n}) ---")
        
#         sld_engine = SLDResolutionEngine(env)
        
#         print("\n=== DEMO TRUY VẤN THEO YÊU CẦU ĐỒ ÁN ===")
#         print("Hướng dẫn: Nhập tọa độ hàng và cột (từ 0 đến n-1) cách nhau bởi khoảng trắng.")
#         print("Ví dụ nhập: 0 5 (để truy vấn hàng 0, cột 5). Gõ 'exit' để thoát.\n")
        
#         while True:
#             user_input = input("Prolog Query ?- Val(r, c, V) => Nhập r c: ").strip()
            
#             if user_input.lower() == 'exit':
#                 print("\n=== KẾT QUẢ TOÀN BỘ BẢNG TỪ WORKING MEMORY ===")
#                 for row in sld_engine.grid:
#                     print(row)
                    
#                 if sld_engine.is_solved:
#                     save_solution_to_file(output_file, env.n, sld_engine.grid, env)
#                     print(f"--> Đã lưu kết quả thành công vào: {output_file}")
                    
#                 print("\nĐã thoát chương trình.")
#                 break
                
#             try:
#                 r_str, c_str = user_input.split()
#                 r, c = int(r_str), int(c_str)
                
#                 if 0 <= r < env.n and 0 <= c < env.n:
#                     start_time = time.time()
#                     sld_engine.query_value(r, c)
#                     print(f"[Thời gian phản hồi: {time.time() - start_time:.4f}s]")
#                     print(f"[Số Node đã mở rộng (Total): {sld_engine.nodes_expanded}]\n")
#                 else:
#                     print(f"Lỗi: Tọa độ phải nằm trong khoảng từ 0 đến {env.n - 1}.\n")
#             except ValueError:
#                 print("Lỗi cú pháp. Vui lòng nhập 2 số nguyên cách nhau bởi khoảng trắng.\n")
            
#     except FileNotFoundError:
#         print(f"Lỗi: Không tìm thấy file {input_file}.")