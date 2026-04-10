import time
import os

# --- CÁC HÀM ĐỌC/IN DỮ LIỆU TỪ MÔI TRƯỜNG CỦA BẠN ---
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

# HÀM MỚI: LƯU KẾT QUẢ RA FILE
def save_solution_to_file(output_path, n, grid, h_cons, v_cons):
    """Lưu lưới kết quả và các dấu bất đẳng thức ra file text."""
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

# ==========================================
# THUẬT TOÁN BRUTE-FORCE (GENERATE AND TEST)
# ==========================================

def check_whole_grid(grid, n, h_cons, v_cons):
    """
    Hàm này KHÔNG kiểm tra từng bước, mà nó đánh giá toàn bộ cái bảng ĐÃ ĐIỀN ĐẦY.
    Trả về True nếu cái bảng này hoàn toàn hợp lệ theo luật Futoshiki.
    """
    # 1. Kiểm tra không trùng lặp trên Hàng và Cột
    for i in range(n):
        row_set = set()
        col_set = set()
        for j in range(n):
            if grid[i][j] in row_set: return False
            row_set.add(grid[i][j])
            if grid[j][i] in col_set: return False
            col_set.add(grid[j][i])

    # 2. Kiểm tra các ràng buộc Ngang
    for r in range(n):
        for c in range(n - 1):
            if h_cons[r][c] == 1 and not (grid[r][c] < grid[r][c+1]):
                return False
            if h_cons[r][c] == -1 and not (grid[r][c] > grid[r][c+1]):
                return False

    # 3. Kiểm tra các ràng buộc Dọc
    for r in range(n - 1):
        for c in range(n):
            if v_cons[r][c] == 1 and not (grid[r][c] < grid[r+1][c]):
                return False
            if v_cons[r][c] == -1 and not (grid[r][c] > grid[r+1][c]):
                return False

    return True

# HÀM ĐƯỢC NÂNG CẤP: THÊM BIẾN ĐẾM NODE VÀ TRẢ VỀ TUPLE
def solve_bruteforce(grid, n, h_cons, v_cons, r=0, c=0, node_counter=None):
    """
    Hàm sinh mù quáng (Blind Generator): Điền bừa mọi tổ hợp có thể.
    """
    if node_counter is None:
        node_counter = [0]
        
    node_counter[0] += 1 # Tăng biến đếm mỗi khi mở 1 node (trạng thái) mới

    # Base Case: Nếu đã duyệt qua hết tất cả các ô (tức là r = n), bảng đã đầy.
    if r == n:
        return check_whole_grid(grid, n, h_cons, v_cons), node_counter[0]

    # Tính toán tọa độ ô tiếp theo
    next_c = c + 1
    next_r = r
    if next_c == n:
        next_c = 0
        next_r += 1

    # Nếu ô hiện tại đã có số, nhảy thẳng sang ô tiếp theo
    if grid[r][c] != 0:
        return solve_bruteforce(grid, n, h_cons, v_cons, next_r, next_c, node_counter)

    # Nếu ô trống, TẠO MỌI TỔ HỢP
    for val in range(1, n + 1):
        grid[r][c] = val
        
        # Gỡ gói đệ quy để nhận lại True/False
        is_solved, _ = solve_bruteforce(grid, n, h_cons, v_cons, next_r, next_c, node_counter)
        if is_solved:
            return True, node_counter[0]
            
    # Xóa đi để đệ quy thử tổ hợp khác
    grid[r][c] = 0
    return False, node_counter[0]

# ==========================================

if __name__ == "__main__":
    input_file = "Source/Inputs/input-01.txt"  # Đổi đường dẫn file
    
    # --- TỰ ĐỘNG SINH ĐƯỜNG DẪN OUTPUT ---
    file_name = os.path.basename(input_file).replace("input", "output")
    output_file = os.path.join("Source", "Outputs", file_name)
    
    try:
        n, grid, h_cons, v_cons = read_input(input_file)
        print(f"--- Đang giải Futoshiki {n}x{n} bằng BRUTE-FORCE PURE ---")
        
        start_time = time.time()
        
        # GỠ GÓI TUPLE KẾT QUẢ
        is_solved, nodes_expanded = solve_bruteforce(grid, n, h_cons, v_cons)
        
        if is_solved:
            print(f"\n=== KẾT QUẢ TÌM THẤY TRONG {time.time() - start_time:.4f}s ===")
            print_output(n, grid, h_cons, v_cons)
            print(f"Số Node đã mở rộng (Expansion count): {nodes_expanded}")
            
            save_solution_to_file(output_file, n, grid, h_cons, v_cons)
            print(f"--> Đã lưu kết quả thành công vào: {output_file}")
        else:
            print("\nKhông tìm thấy giải pháp.")
            print(f"Số Node đã mở rộng trước khi kết thúc: {nodes_expanded}")
            
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {input_file}.")