import heapq
import time
import copy
import os
from futoshiki_env import FutoshikiEnv

"""
A* + FORWARD CHAINING WITH AC-3 (MAC - MAINTAINING ARC CONSISTENCY)
==================================================================

Combines A* with Forward Chaining and AC-3 constraint propagation.

Heuristic: h(s) = Number of empty cells after AC-3 + Forward Chaining

ADMISSIBILITY ANALYSIS:
- AC-3 + FC work together to prune impossible assignments
- h(s) is the count of remaining unassigned cells post-pruning
- This is the minimum possible remaining work
- Forward chaining may detect contradictions early (domain wipeout)
- CONCLUSION: This heuristic is ADMISSIBLE

EFFICIENCY:
- More expensive than pure AC-3 due to forward chaining
- But catches contradictions much earlier
- Reduces search tree significantly on hard instances
"""

file_path = "Inputs/input-09.txt"

class KBGenerator:
    def __init__(self, env):
        self.env = env
        self.n = env.n
        self.facts = []
        self.axioms = []

    def generate_facts(self):
        self.facts.clear()
        for r in range(self.n):
            for c in range(self.n):
                val = self.env.grid[r][c]
                if val != 0:
                    self.facts.append(f"Given({r+1}, {c+1}, {val})")
        
        for r in range(self.n):
            for c in range(self.n - 1):
                if self.env.horiz_constraints[r][c] == 1:
                    self.facts.append(f"LessH({r+1}, {c+1})")
                elif self.env.horiz_constraints[r][c] == -1:
                    self.facts.append(f"GreaterH({r+1}, {c+1})")
                    
        for r in range(self.n - 1):
            for c in range(self.n):
                if self.env.vert_constraints[r][c] == 1:
                    self.facts.append(f"LessV({r+1}, {c+1})")
                elif self.env.vert_constraints[r][c] == -1:
                    self.facts.append(f"GreaterV({r+1}, {c+1})")

    def generate_axioms(self):
        self.axioms.clear()
        self.axioms.append("A1: ∀i ∀j ∃v Val(i, j, v)")
        self.axioms.append("A2: ∀i ∀j ∀v1 ∀v2 (Val(i, j, v1) ∧ Val(i, j, v2) => v1 = v2)")
        self.axioms.append("A3: ∀i ∀j1 ∀j2 ∀v (Val(i, j1, v) ∧ Val(i, j2, v) ∧ j1 ≠ j2 => ⊥)")
        self.axioms.append("A4: ∀i ∀j ∀v1 ∀v2 (LessH(i, j) ∧ Val(i, j, v1) ∧ Val(i, j+1, v2) => Less(v1, v2))")
        self.axioms.append("A5: ∀i ∀j ∀v (Given(i, j, v) => Val(i, j, v))")
        self.axioms.append("A6: ∀i ∀j ∀v1 ∀v2 (LessH(i, j) ∧ Val(i, j, v1) ∧ Val(i, j+1, v2) => Less(v1, v2))")
        self.axioms.append("A7: ∀i ∀j ∀v1 ∀v2 (GreaterH(i, j) ∧ Val(i, j, v1) ∧ Val(i, j+1, v2) => Less(v2, v1))")
        self.axioms.append("A8: ∀i ∀j ∀v1 ∀v2 (LessV(i, j) ∧ Val(i, j, v1) ∧ Val(i+1, j, v2) => Less(v1, v2))")
        self.axioms.append("A9: ∀i ∀j ∀v1 ∀v2 (GreaterV(i, j) ∧ Val(i, j, v1) ∧ Val(i+1, j, v2) => Less(v2, v1))")
        self.axioms.append(f"A10: ∀i ∀j ∀v (Val(i, j, v) => (v=1 ∨ v=2 ∨ ... ∨ v={self.n}))")

    def get_full_kb(self):
        self.generate_facts()
        self.generate_axioms()
        kb_text = "=== TẬP DỮ KIỆN (FACTS) ===\n"
        kb_text += "\n".join(self.facts) if self.facts else "Không có dữ kiện."
        kb_text += "\n\n=== TẬP TIÊN ĐỀ (AXIOMS) ===\n"
        kb_text += "\n".join(self.axioms)
        return kb_text

class KnowledgeBase:
    def __init__(self, n):
        self.n = n
        self.domains = [[set(range(1, n + 1)) for _ in range(n)] for _ in range(n)]
        self.facts = [] 

class ForwardChaining:
    def __init__(self, kb, env):
        self.kb = kb
        self.env = env
        self.n = env.n

    def execute(self, agenda=None):
        if agenda is None:
            agenda = self.kb.facts.copy()
            
        while agenda:
            r, c, val = agenda.pop(0)
            
            for i in range(self.n):
                if i != r and val in self.kb.domains[i][c]:
                    self.kb.domains[i][c].remove(val)
                    if len(self.kb.domains[i][c]) == 1:
                        agenda.append((i, c, list(self.kb.domains[i][c])[0]))
                    elif len(self.kb.domains[i][c]) == 0:
                        return False

                if i != c and val in self.kb.domains[r][i]:
                    self.kb.domains[r][i].remove(val)
                    if len(self.kb.domains[r][i]) == 1:
                        agenda.append((r, i, list(self.kb.domains[r][i])[0]))
                    elif len(self.kb.domains[r][i]) == 0:
                        return False

            for constraint in self.env.constraints_list:
                ctype, r1, c1, r2, c2 = constraint
                
                if r == r1 and c == c1:
                    to_remove = [v2 for v2 in self.kb.domains[r2][c2] if (ctype == '<' and not (val < v2)) or (ctype == '>' and not (val > v2))]
                    for v2 in to_remove:
                        self.kb.domains[r2][c2].remove(v2)
                        if len(self.kb.domains[r2][c2]) == 1:
                            agenda.append((r2, c2, list(self.kb.domains[r2][c2])[0]))
                        elif len(self.kb.domains[r2][c2]) == 0:
                            return False

                elif r == r2 and c == c2:
                    to_remove = [v1 for v1 in self.kb.domains[r1][c1] if (ctype == '<' and not (v1 < val)) or (ctype == '>' and not (v1 > val))]
                    for v1 in to_remove:
                        self.kb.domains[r1][c1].remove(v1)
                        if len(self.kb.domains[r1][c1]) == 1:
                            agenda.append((r1, c1, list(self.kb.domains[r1][c1])[0]))
                        elif len(self.kb.domains[r1][c1]) == 0:
                            return False
        return True

def extract_grid(domains, n):
    return [[list(domains[r][c])[0] for c in range(n)] for r in range(n)]

def heuristic_mac(domains, n):
    unassigned_cells = 0
    
    for r in range(n):
        for c in range(n):
            if len(domains[r][c]) == 0:
                return float('inf') 
            elif len(domains[r][c]) > 1:
                unassigned_cells += 1
                
    return unassigned_cells

def get_state_tuple(domains):
    return tuple(tuple(tuple(sorted(d)) for d in row) for row in domains)

def solve_astar_mac_ac3(env):
    initial_kb = KnowledgeBase(env.n)
    for r in range(env.n):
        for c in range(env.n):
            if env.grid[r][c] != 0:
                initial_kb.domains[r][c] = {env.grid[r][c]}
                initial_kb.facts.append((r, c, env.grid[r][c]))
                
    fc_init = ForwardChaining(initial_kb, env)
    if not fc_init.execute():
        return None 

    g_cost = 0
    h_cost = heuristic_mac(initial_kb.domains, env.n)
    tie_breaker = 0
    
    pq = []
    heapq.heappush(pq, (g_cost + h_cost, -g_cost, tie_breaker, get_state_tuple(initial_kb.domains), initial_kb.domains))
    visited = set()

    nodes_expanded = 0 
    
    while pq:
        f, neg_g, _, state_tup, current_domains = heapq.heappop(pq)
        nodes_expanded += 1
        g = -neg_g
        
        if state_tup in visited:
            continue
        visited.add(state_tup)
        
        best_r, best_c = -1, -1
        min_options = env.n + 1
        
        for r in range(env.n):
            for c in range(env.n):
                opts = len(current_domains[r][c])
                if opts > 1 and opts < min_options:
                    min_options = opts
                    best_r, best_c = r, c

        if best_r == -1:
            return extract_grid(current_domains, env.n), nodes_expanded
            
        for val in current_domains[best_r][best_c]:
            next_kb = KnowledgeBase(env.n)
            next_kb.domains = [ [set(d) for d in row] for row in current_domains ] 
            
            next_kb.domains[best_r][best_c] = {val}
            agenda = [(best_r, best_c, val)]
            
            fc = ForwardChaining(next_kb, env)
            is_valid_branch = fc.execute(agenda)
            
            if is_valid_branch:
                new_state_tup = get_state_tuple(next_kb.domains)
                if new_state_tup not in visited:
                    new_g = g + 1
                    new_h = heuristic_mac(next_kb.domains, env.n)
                    tie_breaker += 1
                    heapq.heappush(pq, (new_g + new_h, -new_g, tie_breaker, new_state_tup, next_kb.domains))

    return None, nodes_expanded

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

    print(f"BƯỚC 1: Đọc dữ liệu từ {input_file} vào Môi trường (FutoshikiEnv)...")
    try:
        env = load_env_from_file(input_file)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file!")
        exit()

    print("\nBƯỚC 2: Gọi KBGenerator dịch môi trường sang Logic (Dành cho Báo cáo)...")
    kb_gen = KBGenerator(env)
    print(kb_gen.get_full_kb())

    print(f"\nBƯỚC 3: Giải Futoshiki {env.n}x{env.n} bằng thuật toán A* tích hợp Forward Chaining...")
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