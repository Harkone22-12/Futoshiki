import heapq
import time
file_path = "Source/Inputs/input-10.txt"

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

def heuristic(grid, n):
    return sum(1 for r in range(n) for c in range(n) if grid[r][c] == 0)

def solve_astar(initial_grid, n, h_cons, v_cons):
    initial_state = tuple(tuple(row) for row in initial_grid)
    g_cost = 0
    h_cost = heuristic(initial_grid, n)
    tie_breaker = 0
    
    pq = []
    heapq.heappush(pq, (g_cost + h_cost, -g_cost, tie_breaker, initial_state))
    visited = set()
    
    while pq:
        f, g, _, state = heapq.heappop(pq)
        
        if state in visited:
            continue
        visited.add(state)
        
        current_grid = [list(row) for row in state]
        
        best_r, best_c = -1, -1
        min_options = n + 1
        
        for r in range(n):
            for c in range(n):
                if current_grid[r][c] == 0:
                    options = sum(1 for val in range(1, n + 1) if is_valid(current_grid, n, r, c, val, h_cons, v_cons))
                    if options < min_options:
                        min_options = options
                        best_r, best_c = r, c
        
        if best_r == -1:
            for i in range(n):
                for j in range(n):
                    initial_grid[i][j] = current_grid[i][j]
            return True
            
        if min_options == 0:
            continue
            
        for val in range(1, n + 1):
            if is_valid(current_grid, n, best_r, best_c, val, h_cons, v_cons):
                next_grid = [list(row) for row in current_grid]
                next_grid[best_r][best_c] = val
                next_state = tuple(tuple(row) for row in next_grid)
                
                if next_state not in visited:
                    new_g = g + 1
                    new_h = heuristic(next_grid, n)
                    tie_breaker += 1
                    heapq.heappush(pq, (new_g + new_h, -new_g, tie_breaker, next_state))
                    
    return False

if __name__ == "__main__":
    input_file = file_path
    try:
        n, grid, h_cons, v_cons = read_input(input_file)
        print(f"--- Đang giải Futoshiki {n}x{n} bằng A* Search ---")
        
        start_time = time.time()
        if solve_astar(grid, n, h_cons, v_cons):
            print("\nKết quả:")
            print_output(n, grid, h_cons, v_cons)
            print(f"\nThời gian chạy: {time.time() - start_time:.4f}s")
        else:
            print("Không tìm thấy giải pháp.")
    except FileNotFoundError:
        print(f"Không tìm thấy file {input_file}.")