import heapq
import time
import os
from futoshiki_env import FutoshikiEnv

file_path = "Inputs/input-09.txt"

def check_constraint(x, y, r1, c1, r2, c2, env):
    if r1 == r2 and x == y: return False
    if c1 == c2 and x == y: return False

    if r1 == r2:
        if c1 == c2 - 1: 
            op = env.horiz_constraints[r1][c1]
            if op == 1 and not (x < y): return False
            if op == -1 and not (x > y): return False
        elif c1 == c2 + 1: 
            op = env.horiz_constraints[r2][c2]
            if op == 1 and not (y < x): return False
            if op == -1 and not (y > x): return False
            
    if c1 == c2:
        if r1 == r2 - 1: 
            op = env.vert_constraints[r1][c1]
            if op == 1 and not (x < y): return False
            if op == -1 and not (x > y): return False
        elif r1 == r2 + 1: 
            op = env.vert_constraints[r2][c2]
            if op == 1 and not (y < x): return False
            if op == -1 and not (y > x): return False
            
    return True

def revise(domains, r1, c1, r2, c2, env):
    revised = False
    to_remove = set()
    
    for x in domains[r1][c1]:
        satisfies = False
        for y in domains[r2][c2]:
            if check_constraint(x, y, r1, c1, r2, c2, env):
                satisfies = True
                break
        if not satisfies:
            to_remove.add(x)
            revised = True
            
    if revised:
        domains[r1][c1] -= to_remove
        
    return revised

def true_ac3(domains, env, initial_queue=None):
    n = env.n
    queue = initial_queue
    
    if queue is None:
        queue = []
        for r in range(n):
            for c in range(n):
                for i in range(n):
                    if i != c: queue.append(((r, c), (r, i)))
                    if i != r: queue.append(((r, c), (i, c)))
                    
    while queue:
        (r1, c1), (r2, c2) = queue.pop(0)
        
        if revise(domains, r1, c1, r2, c2, env):
            if len(domains[r1][c1]) == 0:
                return False 

            for i in range(n):
                if i != c1 and i != c2: queue.append(((r1, i), (r1, c1)))
                if i != r1 and i != r2: queue.append(((i, c1), (r1, c1)))
                
    return True

def heuristic_mac(domains, n):
    """Heuristic đếm số ô còn trống dựa trên Domain size."""
    unassigned = 0
    for r in range(n):
        for c in range(n):
            if len(domains[r][c]) == 0:
                return float('inf') # Ngõ cụt
            elif len(domains[r][c]) > 1:
                unassigned += 1
    return unassigned

def get_state_tuple(domains):
    """Chuyển mảng Domains thành Tuple để băm (Hash) vào tập visited."""
    return tuple(tuple(tuple(sorted(d)) for d in row) for row in domains)

def extract_grid(domains, n):
    """Trích xuất mảng 2D kết quả khi mọi Domain chỉ còn 1 số."""
    return [[list(domains[r][c])[0] for c in range(n)] for r in range(n)]

def solve_astar_mac_ac3(env):
    n = env.n
    initial_domains = [[set(range(1, n + 1)) for _ in range(n)] for _ in range(n)]
    
    for r in range(n):
        for c in range(n):
            if env.grid[r][c] != 0:
                initial_domains[r][c] = {env.grid[r][c]}
                
    if not true_ac3(initial_domains, env):
        return None, 0
        
    g_cost = 0
    h_cost = heuristic_mac(initial_domains, n)
    tie_breaker = 0
    nodes_expanded = 0
    
    pq = []
    heapq.heappush(pq, (g_cost + h_cost, -g_cost, tie_breaker, get_state_tuple(initial_domains), initial_domains))
    visited = set()
    
    while pq:
        f, neg_g, _, state_tup, current_domains = heapq.heappop(pq)
        nodes_expanded += 1
        g = -neg_g
        
        if state_tup in visited: continue
        visited.add(state_tup)
        
        best_r, best_c = -1, -1
        min_options = n + 1
        
        for r in range(n):
            for c in range(n):
                opts = len(current_domains[r][c])
                if 1 < opts < min_options:
                    min_options = opts
                    best_r, best_c = r, c
                    
        if best_r == -1:
            return extract_grid(current_domains, n), nodes_expanded
            
        for val in current_domains[best_r][best_c]:
            next_domains = [[set(d) for d in row] for row in current_domains]
            next_domains[best_r][best_c] = {val}
            
            queue = []
            for i in range(n):
                if i != best_c: queue.append(((best_r, i), (best_r, best_c)))
                if i != best_r: queue.append(((i, best_c), (best_r, best_c)))
                
            if true_ac3(next_domains, env, initial_queue=queue):
                new_state_tup = get_state_tuple(next_domains)
                if new_state_tup not in visited:
                    new_g = g + 1
                    new_h = heuristic_mac(next_domains, n)
                    tie_breaker += 1
                    heapq.heappush(pq, (new_g + new_h, -new_g, tie_breaker, new_state_tup, next_domains))
                    
    return None, nodes_expanded

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
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(n):
            row_str = ""
            for j in range(n):
                row_str += str(grid[i][j])
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
    
    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Outputs", file_name)

    try:
        env = load_env_from_file(input_file)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file!")
        exit()

    print(f"--- Đang giải Futoshiki {env.n}x{env.n} bằng A* kết hợp TRUE MAC (AC-3 chuẩn) ---")
    start_time = time.time()
    
    solution_grid, nodes_expanded = solve_astar_mac_ac3(env)
    
    if solution_grid:
        print(f"\n======= KẾT QUẢ FUTOSHIKI =======")
        print_solution(env.n, solution_grid, env)
        print(f"\nTIME: {time.time() - start_time:.4f}s")
        print(f"EXPANSION COUNT (Nodes opened): {nodes_expanded}")

        save_solution_to_file(output_file, env.n, solution_grid, env)
        print(f"--> Đã lưu kết quả thành công vào: {output_file}")
    else:
        print("\nKHÔNG TÌM THẤY GIẢI PHÁP HOẶC BÀI TOÁN VÔ NGHIỆM.")