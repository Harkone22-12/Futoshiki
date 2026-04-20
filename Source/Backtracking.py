import time
import os
file_path = "Inputs/input-07.txt"

def read_input(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    n = int(lines[0])
    grid = [[int(x) for x in lines[i].split(',')] for i in range(1, n + 1)]
    h_cons = [[int(x) for x in lines[i].split(',')] for i in range(n + 1, 2 * n + 1)]
    v_cons = [[int(x) for x in lines[i].split(',')] for i in range(2 * n + 1, 3 * n)]
    return n, grid, h_cons, v_cons

def print_output(n, grid, h_cons, v_cons):
    for i in range(n):
        row_str = ""
        for j in range(n):
            row_str += str(grid[i][j]) if grid[i][j] != 0 else "."
            if j < n - 1:
                if h_cons[i][j] == 1: row_str += " < "
                elif h_cons[i][j] == -1: row_str += " > "
                else: row_str += "   "
        print(row_str)
        if i < n - 1:
            v_str = ""
            for j in range(n):
                if v_cons[i][j] == 1: v_str += "^   "
                elif v_cons[i][j] == -1: v_str += "v   "
                else: v_str += "    "
            print(v_str.rstrip())

def is_valid(grid, n, r, c, val, h_cons, v_cons):
    for i in range(n):
        if grid[r][i] == val or grid[i][c] == val: return False
    
    if c > 0 and grid[r][c-1] != 0:
        if h_cons[r][c-1] == 1 and not (grid[r][c-1] < val): return False
        if h_cons[r][c-1] == -1 and not (grid[r][c-1] > val): return False
    if c < n - 1 and grid[r][c+1] != 0:
        if h_cons[r][c] == 1 and not (val < grid[r][c+1]): return False
        if h_cons[r][c] == -1 and not (val > grid[r][c+1]): return False
        
    if r > 0 and grid[r-1][c] != 0:
        if v_cons[r-1][c] == 1 and not (grid[r-1][c] < val): return False
        if v_cons[r-1][c] == -1 and not (grid[r-1][c] > val): return False
    if r < n - 1 and grid[r+1][c] != 0:
        if v_cons[r][c] == 1 and not (val < grid[r+1][c]): return False
        if v_cons[r][c] == -1 and not (val > grid[r+1][c]): return False
        
    return True

def solve_backtracking(grid, n, h_cons, v_cons, node_counter=None):
    if node_counter is None:
        node_counter = [0]
        
    node_counter[0] += 1 

    for r in range(n):
        for c in range(n):
            if grid[r][c] == 0:
                for val in range(1, n + 1):
                    if is_valid(grid, n, r, c, val, h_cons, v_cons):
                        grid[r][c] = val
                        
                        result = solve_backtracking(grid, n, h_cons, v_cons, node_counter)
                        
                        if result[0] == True:
                            return True, node_counter[0]
                            
                        grid[r][c] = 0
                        
                return False, node_counter[0]
                
    return True, node_counter[0]

def save_solution_to_file(output_path, n, grid, h_cons, v_cons):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(n):
            row_str = ""
            for j in range(n):
                row_str += str(grid[i][j]) if grid[i][j] != 0 else "."
                if j < n - 1:
                    if h_cons[i][j] == 1: row_str += " < "
                    elif h_cons[i][j] == -1: row_str += " > "
                    else: row_str += "   "
            f.write(row_str + "\n")
            
            if i < n - 1:
                v_str = ""
                for j in range(n):
                    if v_cons[i][j] == 1: v_str += "^   "
                    elif v_cons[i][j] == -1: v_str += "v   "
                    else: v_str += "    "
                f.write(v_str.rstrip() + "\n")

if __name__ == "__main__":
    input_file = file_path 

    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Outputs", file_name)

    try:
        n, grid, h_cons, v_cons = read_input(input_file)
        print(f"--- Đang giải Futoshiki {n}x{n} bằng Backtracking ---")
        
        start_time = time.time()
        result = solve_backtracking(grid, n, h_cons, v_cons)
        
        if result[0] == True:
            print("\nKết quả:")
            print_output(n, grid, h_cons, v_cons)
            print(f"\nThời gian chạy: {time.time() - start_time:.4f}s")
            print(f"Số Node đã mở rộng: {result[1]}")

            save_solution_to_file(output_file, n, grid, h_cons, v_cons)
            print(f"--> Đã lưu kết quả thành công vào: {output_file}")
        else:
            print("Không tìm thấy giải pháp.")
    except FileNotFoundError:
        print(f"Không tìm thấy file {input_file}.")