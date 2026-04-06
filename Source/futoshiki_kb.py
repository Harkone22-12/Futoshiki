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
        
        # 1. Thu thập Facts ban đầu từ grid
        for r in range(self.n):
            for c in range(self.n):
                val = env.grid[r][c]
                if val != 0:
                    self.add_fact(r, c, val)
                    self.rules.append(f"FACT: Cell({r}, {c}) = {val}")

        # 2. Sinh luật All-Different (Hàng và Cột không được trùng số)
        for i in range(self.n):
            for j in range(self.n):
                for k in range(j + 1, self.n):
                    # Ràng buộc hàng
                    self.rules.append(f"RULE: IF Cell({i}, {j}) = X THEN Cell({i}, {k}) != X")
                    # Ràng buộc cột
                    self.rules.append(f"RULE: IF Cell({j}, {i}) = X THEN Cell({k}, {i}) != X")

        # 3. Sinh luật Bất đẳng thức (Dựa vào constraints_list của Env)
        for constraint in env.constraints_list:
            ctype, r1, c1, r2, c2 = constraint
            if ctype == '<':
                self.rules.append(f"RULE: IF Cell({r1}, {c1}) = X THEN Cell({r2}, {c2}) > X")
            elif ctype == '>':
                self.rules.append(f"RULE: IF Cell({r1}, {c1}) = X THEN Cell({r2}, {c2}) < X")

    def print_rules(self, limit=30):
        """In ra màn hình các luật trong Knowledge Base"""
        print(f"\n--- Đã sinh {len(self.rules)} luật và sự kiện trong Knowledge Base ---")
        for i, rule in enumerate(self.rules[:limit]):
            print(rule)
        if len(self.rules) > limit:
            print(f"... (đã ẩn {len(self.rules) - limit} luật còn lại)")
        print("=" * 50)