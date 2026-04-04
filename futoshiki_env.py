class FutoshikiEnv:
    def __init__(self, n):
        self.n = n
        # Ma trận NxN lưu giá trị các ô. 0 nghĩa là ô trống[cite: 317].
        self.grid = [[0 for _ in range(n)] for _ in range(n)]
        
        # --- DÀNH CHO QUÂN & PHÁT (Tra cứu O(1) cho A* / Backtrack) ---
        # Ràng buộc ngang: mảng N x (N-1). 1="<", -1=">" [cite: 324]
        self.horiz_constraints = [[0 for _ in range(n-1)] for _ in range(n)]
        # Ràng buộc dọc: mảng (N-1) x N. 1="<" (trên<dưới), -1=">" (trên>dưới) [cite: 330]
        self.vert_constraints = [[0 for _ in range(n)] for _ in range(n-1)]

        # --- DÀNH CHO HÀO (Duyệt nhanh để sinh luật FOL) ---
        # Chứa tuple (loại_ràng_buộc, r1, c1, r2, c2). Ví dụ: ('<', 0, 0, 0, 1)
        self.constraints_list = []

    def set_given_value(self, row, col, val):
        self.grid[row][col] = val

    def add_horizontal_constraint(self, row, col, constraint_val):
        """constraint_val: 1 là '<', -1 là '>'"""
        self.horiz_constraints[row][col] = constraint_val
        if constraint_val == 1:
            self.constraints_list.append(('<', row, col, row, col+1))
        elif constraint_val == -1:
            self.constraints_list.append(('>', row, col, row, col+1))

    def add_vertical_constraint(self, row, col, constraint_val):
        """constraint_val: 1 là top < bottom, -1 là top > bottom"""
        self.vert_constraints[row][col] = constraint_val
        if constraint_val == 1:
            self.constraints_list.append(('<', row, col, row+1, col))
        elif constraint_val == -1:
            self.constraints_list.append(('>', row, col, row+1, col))

    def print_grid(self):
        for row in self.grid:
            print(row)
