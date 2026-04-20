class FutoshikiEnv:
    def __init__(self, n):
        self.n = n
        self.grid = [[0 for _ in range(n)] for _ in range(n)]
        
        self.horiz_constraints = [[0 for _ in range(n-1)] for _ in range(n)]
        self.vert_constraints = [[0 for _ in range(n)] for _ in range(n-1)]

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
