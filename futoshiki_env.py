class FutoshikiGrid:
    def __init__(self, n):
        self.n = n
        # Ma trận NxN lưu giá trị các ô. 0 nghĩa là ô trống.
        self.cells = [[0 for _ in range(n)] for _ in range(n)]
        
        # Danh sách các ràng buộc.
        # Mỗi ràng buộc có thể lưu dưới dạng tuple: (loại_ràng_buộc, r1, c1, r2, c2)
        # Ví dụ: ('<', 0, 0, 0, 1) nghĩa là cell(0,0) < cell(0,1)
        self.constraints = []

    def set_given_value(self, row, col, val):
        """Gán giá trị cho các ô clue có sẵn từ đề bài[cite: 254]."""
        self.cells[row][col] = val

    def add_constraint(self, constraint_type, r1, c1, r2, c2):
        """Thêm ràng buộc bất đẳng thức giữa 2 ô liền kề[cite: 255]."""
        self.constraints.append((constraint_type, r1, c1, r2, c2))

    def is_complete(self):
        """Kiểm tra xem lưới đã được điền kín chưa."""
        pass

    def is_valid(self):
        """Kiểm tra xem lưới hiện tại có vi phạm luật nào không (dành cho Backtracking/A*)."""
        pass
