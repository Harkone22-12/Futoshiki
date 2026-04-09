class KBGenerator:
    def __init__(self, env):
        self.env = env
        self.n = env.n
        self.facts = []   # Chứa các dữ kiện rút trích từ bàn cờ
        self.axioms = []  # Chứa các luật lệ cứng của trò chơi

    def generate_facts(self):
        """Dịch tất cả các Axioms thành Mệnh đề chuẩn CNF và nạp vào Solver."""
        self.cnf_strings.clear()
        
        # HÀM QUAN TRỌNG: Vừa nạp vào máy giải, vừa dịch ra chuỗi text
        def add_and_record(clause):
            self.solver.add_clause(clause)
            self.cnf_strings.append(self.clause_to_string(clause))
        
        # A1: Mọi ô phải có ÍT NHẤT 1 giá trị
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                clause = [self.var_id(r, c, v) for v in range(1, self.n + 1)]
                add_and_record(clause) # ĐÃ SỬA

        # A2: Mọi ô có TỐI ĐA 1 giá trị
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                for v1 in range(1, self.n + 1):
                    for v2 in range(v1 + 1, self.n + 1):
                        add_and_record([-self.var_id(r, c, v1), -self.var_id(r, c, v2)]) # ĐÃ SỬA

        # A3 & A3b: Duy nhất trên Hàng và Cột
        for v in range(1, self.n + 1):
            for i in range(1, self.n + 1):
                for j1 in range(1, self.n + 1):
                    for j2 in range(j1 + 1, self.n + 1):
                        add_and_record([-self.var_id(i, j1, v), -self.var_id(i, j2, v)]) # Hàng - ĐÃ SỬA
                        add_and_record([-self.var_id(j1, i, v), -self.var_id(j2, i, v)]) # Cột - ĐÃ SỬA

        # A5: Sự thật hiển nhiên (Given Clues từ Env)
        for r in range(self.n):
            for c in range(self.n):
                val = self.env.grid[r][c]
                if val != 0:
                    add_and_record([self.var_id(r + 1, c + 1, val)]) # ĐÃ SỬA

        # A4 & A6: Ràng buộc Ngang (Horizontal Constraints)
        for r in range(self.n):
            for c in range(self.n - 1):
                ctype = self.env.horiz_constraints[r][c]
                if ctype != 0:
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if ctype == 1 and v1 >= v2:    # Dấu <
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 1, c + 2, v2)]) # ĐÃ SỬA
                            elif ctype == -1 and v1 <= v2: # Dấu >
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 1, c + 2, v2)]) # ĐÃ SỬA

        # A8 & A9: Ràng buộc Dọc (Vertical Constraints)
        for r in range(self.n - 1):
            for c in range(self.n):
                ctype = self.env.vert_constraints[r][c]
                if ctype != 0:
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if ctype == 1 and v1 >= v2:    # Dấu ^ (top < bottom)
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 2, c + 1, v2)]) # ĐÃ SỬA
                            elif ctype == -1 and v1 <= v2: # Dấu v (top > bottom)
                                add_and_record([-self.var_id(r + 1, c + 1, v1), -self.var_id(r + 2, c + 1, v2)]) # ĐÃ SỬA

    def generate_axioms(self):
        """Định nghĩa các Tiên đề (Axioms) cứng của Futoshiki."""
        self.axioms.clear()
        
        # Các luật này được chép thẳng từ PDF của bạn
        self.axioms.append("A1 (Tồn tại ít nhất 1 giá trị): ∀i ∀j ∃v Val(i, j, v)")
        self.axioms.append("A2 (Nhiều nhất 1 giá trị):     ∀i ∀j ∀v1 ∀v2 (Val(i, j, v1) ∧ Val(i, j, v2) ⇒ v1 = v2)")
        self.axioms.append("A3 (Duy nhất trên hàng):       ∀i ∀j1 ∀j2 ∀v (Val(i, j1, v) ∧ Val(i, j2, v) ∧ j1 ≠ j2 ⇒ ⊥)")
        self.axioms.append("A3b (Duy nhất trên cột):       ∀i1 ∀i2 ∀j ∀v (Val(i1, j, v) ∧ Val(i2, j, v) ∧ i1 ≠ i2 ⇒ ⊥)")
        self.axioms.append("A4 (Luật LessH):             ∀i ∀j ∀v1 ∀v2 (LessH(i, j) ∧ Val(i, j, v1) ∧ Val(i, j+1, v2) ⇒ Less(v1, v2))")
        self.axioms.append("A5 (Luật Given):             ∀i ∀j ∀v (Given(i, j, v) ⇒ Val(i, j, v))")
        # Bạn có thể bổ sung thêm các luật GreaterH, LessV, GreaterV vào đây...

    def get_full_kb(self):
        """Gom toàn bộ Dữ kiện và Tiên đề thành một Knowledge Base hoàn chỉnh."""
        self.generate_facts()
        self.generate_axioms()
        
        kb_text = "=== TẬP DỮ KIỆN (FACTS) ===\n"
        kb_text += "\n".join(self.facts) if self.facts else "Không có dữ kiện."
        
        kb_text += "\n\n=== TẬP TIÊN ĐỀ (AXIOMS) ===\n"
        kb_text += "\n".join(self.axioms)
        
        return kb_text

    def get_cnf_clauses(self):
        """
        Nâng cao: Dành cho phần 2.3 (Ground the KB / Convert to CNF).
        Hàm này sẽ sinh ra các mệnh đề CNF thật sự để nạp vào SAT Solver (nếu nhóm có làm).
        """
        cnf_clauses = []
        # Chuyển Given(1,1,4) thành chuỗi/tuple CNF: ("Val_1_1_4",)
        for r in range(self.n):
            for c in range(self.n):
                val = self.env.grid[r][c]
                if val != 0:
                    cnf_clauses.append([(r+1, c+1, val)]) # Nghĩa là Val(r+1, c+1) BẮT BUỘC bằng val
        return cnf_clauses