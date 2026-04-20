import random
import os

def generate_futoshiki(n, filename, num_clues, num_h_cons, num_v_cons):
    base = list(range(1, n + 1))
    random.shuffle(base)
    grid = []
    for i in range(n):
        grid.append(base[i:] + base[:i])
    
    random.shuffle(grid)
    grid = list(map(list, zip(*grid)))
    random.shuffle(grid)
    grid = list(map(list, zip(*grid))) 

    solved_grid = [row[:] for row in grid]

    puzzle_grid = [[0]*n for _ in range(n)]
    all_cells = [(r, c) for r in range(n) for c in range(n)]
    clues = random.sample(all_cells, min(num_clues, n * n))
    for r, c in clues:
        puzzle_grid[r][c] = solved_grid[r][c]

    h_cons = [[0]*(n-1) for _ in range(n)]
    v_cons = [[0]*n for _ in range(n-1)]

    h_adj = [(r, c) for r in range(n) for c in range(n-1)]
    for r, c in random.sample(h_adj, min(num_h_cons, len(h_adj))):
        if solved_grid[r][c] < solved_grid[r][c+1]:
            h_cons[r][c] = 1
        else:
            h_cons[r][c] = -1

    v_adj = [(r, c) for r in range(n-1) for c in range(n)]
    for r, c in random.sample(v_adj, min(num_v_cons, len(v_adj))):
        if solved_grid[r][c] < solved_grid[r+1][c]:
            v_cons[r][c] = 1
        else:
            v_cons[r][c] = -1

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(f"{n}\n")
        f.write("# Grid\n")
        for row in puzzle_grid:
            f.write(",".join(map(str, row)) + "\n")
        f.write("# Horizontal constraints\n")
        for row in h_cons:
            f.write(",".join(map(str, row)) + "\n")
        f.write("# Vertical constraints\n")
        for row in v_cons:
            f.write(",".join(map(str, row)) + "\n")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_dir = os.path.join(current_dir, "Inputs")
    
    configs = [
        (4, 3, 3, 3),   # input-01: 4x4
        (4, 2, 4, 4),   # input-02: 4x4
        (5, 5, 4, 4),   # input-03: 5x5
        (5, 3, 6, 6),   # input-04: 5x5
        (6, 6, 6, 6),   # input-05: 6x6
        (6, 4, 8, 8),   # input-06: 6x6
        (7, 8, 8, 8),   # input-07: 7x7
        (7, 6, 12, 12), # input-08: 7x7
        (9, 15, 12, 12),# input-09: 9x9
        (9, 10, 20, 20) # input-10: 9x9 
    ]

    print("Đang tạo 10 files test ngẫu nhiên (chắc chắn có nghiệm)...")
    for i, (n, clues, h, v) in enumerate(configs, 1):
        filename = os.path.join(inputs_dir, f"input-{i:02d}.txt")
        generate_futoshiki(n, filename, clues, h, v)
        print(f"  Đã tạo {filename} (Size: {n}x{n})")
    
    print("\nHoàn tất! Bạn có thể vào thư mục Inputs để kiểm tra.")