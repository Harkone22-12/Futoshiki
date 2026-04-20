import heapq
import time
import os

file_path = "Inputs/input-08.txt"

def read_input(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
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

def check_constraint(x, y, r1, c1, r2, c2, h_cons, v_cons):
    if r1 == r2 and x == y: return False
    if c1 == c2 and x == y: return False
    
    if r1 == r2:
        if c1 == c2 - 1:
            if h_cons[r1][c1] == 1 and not (x < y): return False
            if h_cons[r1][c1] == -1 and not (x > y): return False
        elif c1 == c2 + 1:
            if h_cons[r2][c2] == 1 and not (y < x): return False
            if h_cons[r2][c2] == -1 and not (y > x): return False
            
    if c1 == c2:
        if r1 == r2 - 1:
            if v_cons[r1][c1] == 1 and not (x < y): return False
            if v_cons[r1][c1] == -1 and not (x > y): return False
        elif r1 == r2 + 1:
            if v_cons[r2][c2] == 1 and not (y < x): return False
            if v_cons[r2][c2] == -1 and not (y > x): return False
            
    return True

def revise(domains, r1, c1, r2, c2, h_cons, v_cons):
    revised = False
    to_remove = set()
    for x in domains[r1][c1]:
        if not any(check_constraint(x, y, r1, c1, r2, c2, h_cons, v_cons) for y in domains[r2][c2]):
            to_remove.add(x)
            revised = True
            
    if revised:
        domains[r1][c1] -= to_remove
    return revised

def true_ac3(domains, n, h_cons, v_cons):
    queue = []
    for r in range(n):
        for c in range(n):
            for i in range(n):
                if i != c: queue.append(((r, c), (r, i)))
                if i != r: queue.append(((r, c), (i, c)))
                
    while queue:
        (r1, c1), (r2, c2) = queue.pop(0)
        if revise(domains, r1, c1, r2, c2, h_cons, v_cons):
            if len(domains[r1][c1]) == 0:
                return False
            for i in range(n):
                if i != c1 and i != c2: queue.append(((r1, i), (r1, c1)))
                if i != r1 and i != r2: queue.append(((i, c1), (r1, c1)))
    return True

def heuristic(grid, n, h_cons, v_cons):
    """
    Hàm Heuristic "hàng hiệu": Dùng AC-3 để đánh giá.
    Trọng số = Số ô trống CÒN LẠI sau khi đã chạy AC-3.
    """
    # 1. Khởi tạo domains nháp từ Grid
    domains = [[set(range(1, n + 1)) for _ in range(n)] for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if grid[r][c] != 0:
                domains[r][c] = {grid[r][c]}
                
    # 2. Chạy nháp AC-3
    if not true_ac3(domains, n, h_cons, v_cons):
        return float('inf') # Nhánh này chắc chắn tịt ngòi, cắt tỉa ngay!
        
    # 3. Đếm số ô chưa được chốt (domain size > 1)
    unassigned = sum(1 for r in range(n) for c in range(n) if len(domains[r][c]) > 1)
    return unassigned

def is_valid(grid, n, r, c, val, h_cons, v_cons):
    """Kiểm tra hợp lệ siêu tốc (Để sinh nhánh trong A*)."""
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

def solve_astar_ac3(initial_grid, n, h_cons, v_cons):
    initial_state = tuple(tuple(row) for row in initial_grid)
    g_cost = 0
    h_cost = heuristic(initial_grid, n, h_cons, v_cons)
    tie_breaker = 0
    nodes_expanded = 0
    
    pq = []
    heapq.heappush(pq, (g_cost + h_cost, -g_cost, tie_breaker, initial_state))
    visited = set()
    
    while pq:
        f, neg_g, _, state = heapq.heappop(pq)
        nodes_expanded += 1
        g = -neg_g
        
        if state in visited:
            continue
        visited.add(state)
        
        current_grid = [list(row) for row in state]
        
        # Chọn ô trống theo MRV
        best_r, best_c = -1, -1
        min_options = n + 1
        
        for r in range(n):
            for c in range(n):
                if current_grid[r][c] == 0:
                    options = sum(1 for val in range(1, n + 1) if is_valid(current_grid, n, r, c, val, h_cons, v_cons))
                    if options < min_options:
                        min_options = options
                        best_r, best_c = r, c
        
        # Đã lấp đầy bảng
        if best_r == -1:
            for i in range(n):
                for j in range(n):
                    initial_grid[i][j] = current_grid[i][j]
            return True, nodes_expanded
            
        if min_options == 0:
            continue
            
        # Rẽ nhánh
        for val in range(1, n + 1):
            if is_valid(current_grid, n, best_r, best_c, val, h_cons, v_cons):
                next_grid = [list(row) for row in current_grid]
                next_grid[best_r][best_c] = val
                next_state = tuple(tuple(row) for row in next_grid)
                
                if next_state not in visited:
                    new_g = g + 1
                    # KÍCH HOẠT TRUE AC-3 TẠI ĐÂY ĐỂ ĐÁNH GIÁ HEURISTIC
                    new_h = heuristic(next_grid, n, h_cons, v_cons)
                    tie_breaker += 1
                    heapq.heappush(pq, (new_g + new_h, -new_g, tie_breaker, next_state))
                    
    return False, nodes_expanded

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
        print(f"--- Đang giải Futoshiki {n}x{n} bằng A* Search (TRUE AC-3 Heuristic) ---")
        
        start_time = time.time()
        is_solved, nodes_expanded = solve_astar_ac3(grid, n, h_cons, v_cons)
        
        if is_solved:
            print("\nKết quả:")
            print_output(n, grid, h_cons, v_cons)
            print(f"\nThời gian chạy: {time.time() - start_time:.4f}s")
            print(f"Số Node đã mở rộng (Expansion count): {nodes_expanded}")
            
            save_solution_to_file(output_file, n, grid, h_cons, v_cons)
            print(f"--> Đã lưu kết quả thành công vào: {output_file}")
            
        else:
            print("\nKhông tìm thấy giải pháp (Hoặc bài toán vô nghiệm).")
            print(f"Số Node đã mở rộng trước khi bỏ cuộc: {nodes_expanded}")
            
    except FileNotFoundError:
        print(f"Không tìm thấy file {input_file}.")