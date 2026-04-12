class FutoshikiKB:
    def __init__(self, n):
        self.n = n
        # Domain ban đầu: mỗi ô có thể nhận giá trị từ 1 đến N
        self.domains = [[set(range(1, n + 1)) for _ in range(n)] for _ in range(n)]
        
        # Lưu trữ các sự kiện (ô đã chốt số)
        self.facts = []
        
        # Lưu trữ các luật dưới dạng chuỗi (để in ra hoặc nạp vào bộ giải logic)
        self.rules = []

    def add_fact(self, r, c, val):
        """Thêm một sự kiện mới và chốt domain của ô đó"""
        if val in self.domains[r][c]:
            self.domains[r][c] = {val}
            self.facts.append((r, c, val))

    def generate_kb(self, env):
        """Sinh tập luật FOL và nạp Facts từ trạng thái Environment"""
        
        self.rules.append("# ==========================================")
        self.rules.append("# FUTOSHIKI KNOWLEDGE BASE (10 AXIOMS)")
        self.rules.append("# ==========================================\n")
        
        # [A9] Thu thập Facts ban đầu từ grid
        self.rules.append("# [A9] Tôn trọng các gợi ý cho trước (Given Clues)")
        for r in range(self.n):
            for c in range(self.n):
                val = env.grid[r][c]
                if val != 0:
                    self.add_fact(r, c, val)
                    self.rules.append(f"FACT [A9]: Cell({r+1}, {c+1}) = {val}")

        # [A3, A4] Sinh luật All-Different (Hàng và Cột không được trùng số)
        self.rules.append("\n# [A3] Duy nhất theo hàng (Row Uniqueness)")
        for i in range(self.n):
            for j in range(self.n):
                for k in range(j + 1, self.n):
                    self.rules.append(f"RULE [A3]: IF Cell({i+1}, {j+1}) = X THEN Cell({i+1}, {k+1}) != X")
                    
        self.rules.append("\n# [A4] Duy nhất theo cột (Column Uniqueness)")
        for i in range(self.n):
            for j in range(self.n):
                for k in range(j + 1, self.n):
                    self.rules.append(f"RULE [A4]: IF Cell({j+1}, {i+1}) = X THEN Cell({k+1}, {i+1}) != X")

        # [A5-A8] Sinh luật Bất đẳng thức (Dựa vào constraints_list của Env)
        self.rules.append("\n# [A5-A8] Ràng buộc Bất đẳng thức (Inequalities)")
        for constraint in env.constraints_list:
            ctype, r1, c1, r2, c2 = constraint
            if ctype == '<':
                if r1 == r2:
                    self.rules.append(f"RULE [A5]: IF Cell({r1+1}, {c1+1}) = X THEN Cell({r2+1}, {c2+1}) > X (LessH)")
                else:
                    self.rules.append(f"RULE [A6]: IF Cell({r1+1}, {c1+1}) = X THEN Cell({r2+1}, {c2+1}) > X (LessV)")
            elif ctype == '>':
                if r1 == r2:
                    self.rules.append(f"RULE [A7]: IF Cell({r1+1}, {c1+1}) = X THEN Cell({r2+1}, {c2+1}) < X (GreaterH)")
                else:
                    self.rules.append(f"RULE [A8]: IF Cell({r1+1}, {c1+1}) = X THEN Cell({r2+1}, {c2+1}) < X (GreaterV)")

        # [A1, A2, A10] Các tiên đề ngầm định
        self.rules.append("\n# [A1, A2, A10] Các tiên đề về miền giá trị (Implicit in domains)")
        self.rules.append(f"RULE [A10]: Mọi giá trị phải nằm trong khoảng 1 đến {self.n}")
        self.rules.append("RULE [A1]: Mỗi ô phải có ít nhất một giá trị")
        self.rules.append("RULE [A2]: Mỗi ô chỉ có tối đa một giá trị")

    def print_rules(self, limit=30):
        """In ra màn hình các luật trong Knowledge Base"""
        print(f"\n--- Đã sinh {len(self.rules)} luật và sự kiện trong Knowledge Base ---")
        for i, rule in enumerate(self.rules[:limit]):
            print(rule)
        if len(self.rules) > limit:
            print(f"... (đã ẩn {len(self.rules) - limit} luật còn lại)")
        print("=" * 50)