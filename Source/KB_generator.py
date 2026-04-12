class KBGenerator:
    """
    Knowledge Base Generator cho Futoshiki Puzzle.
    Sinh ra các dữ kiện (Facts) từ puzzle instance và các tiên đề (Axioms) FOL.
    """
    
    def __init__(self, env):
        """
        Khởi tạo KB Generator.
        :param env: FutoshikiEnv object chứa grid, constraints
        """
        self.env = env
        self.n = env.n
        self.facts = []      # Chứa các dữ kiện From Puzzle Instance
        self.axioms = []     # Chứa các tiên đề FOL của Futoshiki
    
    @staticmethod
    def load_from_file(file_path):
        """
        Tạo KBGenerator từ file input.
        :param file_path: Đường dẫn đến file input (ví dụ: Source/Inputs/input-01.txt)
        :return: KBGenerator object
        """
        from futoshiki_env import FutoshikiEnv
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() 
                    if line.strip() and not line.startswith('#')]
        
        n = int(lines[0])
        env = FutoshikiEnv(n)
        
        # === Đọc Grid (Given Values) ===
        for i in range(1, n + 1):
            row_vals = [int(x) for x in lines[i].split(',')]
            for j in range(n):
                if row_vals[j] != 0:
                    env.set_given_value(i - 1, j, row_vals[j])
        
        # === Đọc Horizontal Constraints ===
        for i in range(n + 1, 2 * n + 1):
            row_vals = [int(x) for x in lines[i].split(',')]
            for j in range(n - 1):
                if row_vals[j] != 0:
                    env.add_horizontal_constraint(i - (n + 1), j, row_vals[j])
        
        # === Đọc Vertical Constraints ===
        for i in range(2 * n + 1, 3 * n):
            row_vals = [int(x) for x in lines[i].split(',')]
            for j in range(n):
                if row_vals[j] != 0:
                    env.add_vertical_constraint(i - (2 * n + 1), j, row_vals[j])
        
        return KBGenerator(env)

    def generate_facts(self):
        """
        Trích xuất dữ kiện (Facts) từ puzzle instance.
        - Given clues: Các ô đã được điền
        - Constraint facts: LessH, GreaterH, LessV, GreaterV
        """
        self.facts.clear()
        
        # === DỮ KIỆN 1: Các ô cho trước (Given Clues) ===
        self.facts.append("# --- Given Clues (A9) ---")
        for r in range(self.n):
            for c in range(self.n):
                val = self.env.grid[r][c]
                if val != 0:
                    self.facts.append(f"Given({r+1}, {c+1}, {val})")
        
        # === DỮ KIỆN 2: Ràng buộc ngang (Horizontal Constraints) ===
        self.facts.append("\n# --- Horizontal Constraints (A5, A7) ---")
        for r in range(self.n):
            for c in range(self.n - 1):
                ctype = self.env.horiz_constraints[r][c]
                if ctype == 1:
                    self.facts.append(f"LessH({r+1}, {c+1})")
                elif ctype == -1:
                    self.facts.append(f"GreaterH({r+1}, {c+1})")
        
        # === DỮ KIỆN 3: Ràng buộc dọc (Vertical Constraints) ===
        self.facts.append("\n# --- Vertical Constraints (A6, A8) ---")
        for r in range(self.n - 1):
            for c in range(self.n):
                ctype = self.env.vert_constraints[r][c]
                if ctype == 1:
                    self.facts.append(f"LessV({r+1}, {c+1})")
                elif ctype == -1:
                    self.facts.append(f"GreaterV({r+1}, {c+1})")

    def generate_axioms(self):
        """
        Định nghĩa tất cả 10 Tiên đề (Axioms) FOL của Futoshiki.
        """
        self.axioms.clear()
        
        self.axioms.append("# ============================================")
        self.axioms.append("# 10 AXIOMS OF FUTOSHIKI (First-Order Logic)")
        self.axioms.append("# ============================================\n")
        
        self.axioms.append("A1. Sự tồn tại giá trị (Cell has at least one value):")
        self.axioms.append("    ∀i∀j∃v Val(i, j, v)  với 1 ≤ i, j, v ≤ N")
        self.axioms.append("    Mỗi ô trong lưới phải chứa ít nhất một giá trị.\n")
        
        self.axioms.append("A2. Sự duy nhất giá trị (Cell has at most one value):")
        self.axioms.append("    ∀i∀j∀v1∀v2 (Val(i, j, v1) ∧ Val(i, j, v2)) ⇒ v1 = v2")
        self.axioms.append("    Mỗi ô không thể chứa hai giá trị khác nhau.\n")
        
        self.axioms.append("A3. Duy nhất theo hàng (Row Uniqueness):")
        self.axioms.append("    ∀i∀j1∀j2∀v (Val(i, j1, v) ∧ Val(i, j2, v) ∧ j1≠j2) ⇒ ⊥")
        self.axioms.append("    Trong cùng một hàng, không có hai cột chứa cùng một giá trị.\n")
        
        self.axioms.append("A4. Duy nhất theo cột (Column Uniqueness):")
        self.axioms.append("    ∀j∀i1∀i2∀v (Val(i1, j, v) ∧ Val(i2, j, v) ∧ i1≠i2) ⇒ ⊥")
        self.axioms.append("    Trong cùng một cột, không có hai hàng chứa cùng một giá trị.\n")
        
        self.axioms.append("A5. Ràng buộc bé hơn theo hàng (Horizontal Less-than):")
        self.axioms.append("    ∀i∀j∀v1∀v2 (LessH(i, j) ∧ Val(i, j, v1) ∧ Val(i, j+1, v2)) ⇒ Less(v1, v2)")
        self.axioms.append("    Nếu ký hiệu < giữa ô (i,j) và (i,j+1), giá trị trái < phải.\n")
        
        self.axioms.append("A6. Ràng buộc bé hơn theo cột (Vertical Less-than):")
        self.axioms.append("    ∀i∀j∀v1∀v2 (LessV(i, j) ∧ Val(i, j, v1) ∧ Val(i+1, j, v2)) ⇒ Less(v1, v2)")
        self.axioms.append("    Nếu ký hiệu bé hơn dọc giữa ô (i,j) và (i+1,j), giá trị trên < dưới.\n")
        
        self.axioms.append("A7. Ràng buộc lớn hơn theo hàng (Horizontal Greater-than):")
        self.axioms.append("    ∀i∀j∀v1∀v2 (GreaterH(i, j) ∧ Val(i, j, v1) ∧ Val(i, j+1, v2)) ⇒ Greater(v1, v2)")
        self.axioms.append("    Nếu ký hiệu > giữa ô (i,j) và (i,j+1), giá trị trái > phải.\n")
        
        self.axioms.append("A8. Ràng buộc lớn hơn theo cột (Vertical Greater-than):")
        self.axioms.append("    ∀i∀j∀v1∀v2 (GreaterV(i, j) ∧ Val(i, j, v1) ∧ Val(i+1, j, v2)) ⇒ Greater(v1, v2)")
        self.axioms.append("    Nếu ký hiệu lớn hơn dọc giữa ô (i,j) và (i+1,j), giá trị trên > dưới.\n")
        
        self.axioms.append("A9. Tôn trọng các gợi ý cho trước (Given Clues):")
        self.axioms.append("    ∀i∀j∀v (Given(i, j, v) ⇒ Val(i, j, v))")
        self.axioms.append("    Nếu ô (i,j) đã được điền giá trị v, ô đó phải giữ nguyên giá trị.\n")
        
        self.axioms.append("A10. Ràng buộc miền giá trị (Domain Completeness):")
        self.axioms.append("    ∀i∀j∀v (Val(i, j, v) ⇒ (v ≥ 1 ∧ v ≤ N))")
        self.axioms.append("    Mọi giá trị v trong các ô phải nằm trong khoảng từ 1 đến N.\n")

    def get_full_kb(self):
        """
        Trả về Knowledge Base FOL chỉ chứa Facts (không chứa Axioms).
        :return: String chứa FOL Facts
        """
        self.generate_facts()
        
        kb_text = "=" * 70 + "\n"
        kb_text += "FUTOSHIKI KNOWLEDGE BASE (FOL Facts)\n"
        kb_text += "=" * 70 + "\n\n"
        
        kb_text += "GRID SIZE: {}x{}\n".format(self.n, self.n)
        kb_text += "\n" + "=" * 70 + "\n"
        kb_text += "FACTS (từ Puzzle Instance)\n"
        kb_text += "=" * 70 + "\n\n"
        kb_text += "\n".join(self.facts) if self.facts else "Không có dữ kiện."
        
        kb_text += "\n" + "=" * 70 + "\n"
        
        return kb_text

    def get_facts_only(self):
        """Trả về danh sách facts (không bao gồm comments)."""
        self.generate_facts()
        return [f for f in self.facts if not f.startswith("#")]

    def get_axioms_only(self):
        """Trả về danh sách axioms (dạng FOL text)."""
        self.generate_axioms()
        return [a for a in self.axioms if not a.startswith("#")]

    def ground_axioms(self):
        """
        Ground tất cả FOL Axioms với domain {1, 2, ..., N}.
        Instantiate mỗi universally quantified variable với tất cả giá trị từ 1 đến N.
        
        :return: List of grounded clauses (dạng text)
        """
        grounded = []
        
        # ============= A1: Cell has at least one value =============
        # ∀i∀j∃v Val(i, j, v)  →  Val(i,j,1) ∨ Val(i,j,2) ∨ ... ∨ Val(i,j,N)
        grounded.append("# A1: Cell has at least one value")
        for i in range(1, self.n + 1):
            for j in range(1, self.n + 1):
                clause_vars = [f"Val({i},{j},{v})" for v in range(1, self.n + 1)]
                grounded.append(f"({' ∨ '.join(clause_vars)})")
        
        # ============= A2: Cell has at most one value =============
        # ∀i∀j∀v1∀v2 (Val(i,j,v1) ∧ Val(i,j,v2)) ⇒ v1=v2
        # CNF: ¬Val(i,j,v1) ∨ ¬Val(i,j,v2)  for v1 ≠ v2
        grounded.append("\n# A2: Cell has at most one value")
        for i in range(1, self.n + 1):
            for j in range(1, self.n + 1):
                for v1 in range(1, self.n + 1):
                    for v2 in range(v1 + 1, self.n + 1):
                        grounded.append(f"(¬Val({i},{j},{v1}) ∨ ¬Val({i},{j},{v2}))")
        
        # ============= A3: Row Uniqueness =============
        # ∀i∀j1∀j2∀v (Val(i,j1,v) ∧ Val(i,j2,v) ∧ j1≠j2) ⇒ ⊥
        # CNF: ¬Val(i,j1,v) ∨ ¬Val(i,j2,v)  for j1 ≠ j2
        grounded.append("\n# A3: Row Uniqueness")
        for i in range(1, self.n + 1):
            for v in range(1, self.n + 1):
                for j1 in range(1, self.n + 1):
                    for j2 in range(j1 + 1, self.n + 1):
                        grounded.append(f"(¬Val({i},{j1},{v}) ∨ ¬Val({i},{j2},{v}))")
        
        # ============= A4: Column Uniqueness =============
        # ∀j∀i1∀i2∀v (Val(i1,j,v) ∧ Val(i2,j,v) ∧ i1≠i2) ⇒ ⊥
        # CNF: ¬Val(i1,j,v) ∨ ¬Val(i2,j,v)  for i1 ≠ i2
        grounded.append("\n# A4: Column Uniqueness")
        for j in range(1, self.n + 1):
            for v in range(1, self.n + 1):
                for i1 in range(1, self.n + 1):
                    for i2 in range(i1 + 1, self.n + 1):
                        grounded.append(f"(¬Val({i1},{j},{v}) ∨ ¬Val({i2},{j},{v}))")
        
        # ============= A5: Horizontal Less-than =============
        # ∀i∀j∀v1∀v2 (LessH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2)) ⇒ Less(v1,v2)
        # CNF: ¬LessH(i,j) ∨ ¬Val(i,j,v1) ∨ ¬Val(i,j+1,v2) ∨ Less(v1,v2)
        #      Simplify: If LessH exists, add implications
        grounded.append("\n# A5: Horizontal Less-than")
        for i in range(self.n):
            for j in range(self.n - 1):
                if self.env.horiz_constraints[i][j] == 1:  # LessH
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if v1 >= v2:  # v1 < v2 must hold
                                grounded.append(f"(¬Val({i+1},{j+1},{v1}) ∨ ¬Val({i+1},{j+2},{v2}))")
        
        # ============= A6: Vertical Less-than =============
        # ∀i∀j∀v1∀v2 (LessV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2)) ⇒ Less(v1,v2)
        grounded.append("\n# A6: Vertical Less-than")
        for i in range(self.n - 1):
            for j in range(self.n):
                if self.env.vert_constraints[i][j] == 1:  # LessV
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if v1 >= v2:  # v1 < v2 must hold
                                grounded.append(f"(¬Val({i+1},{j+1},{v1}) ∨ ¬Val({i+2},{j+1},{v2}))")
        
        # ============= A7: Horizontal Greater-than =============
        # ∀i∀j∀v1∀v2 (GreaterH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2)) ⇒ Greater(v1,v2)
        grounded.append("\n# A7: Horizontal Greater-than")
        for i in range(self.n):
            for j in range(self.n - 1):
                if self.env.horiz_constraints[i][j] == -1:  # GreaterH
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if v1 <= v2:  # v1 > v2 must hold
                                grounded.append(f"(¬Val({i+1},{j+1},{v1}) ∨ ¬Val({i+1},{j+2},{v2}))")
        
        # ============= A8: Vertical Greater-than =============
        # ∀i∀j∀v1∀v2 (GreaterV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2)) ⇒ Greater(v1,v2)
        grounded.append("\n# A8: Vertical Greater-than")
        for i in range(self.n - 1):
            for j in range(self.n):
                if self.env.vert_constraints[i][j] == -1:  # GreaterV
                    for v1 in range(1, self.n + 1):
                        for v2 in range(1, self.n + 1):
                            if v1 <= v2:  # v1 > v2 must hold
                                grounded.append(f"(¬Val({i+1},{j+1},{v1}) ∨ ¬Val({i+2},{j+1},{v2}))")
        
        # ============= A9: Given Clues =============
        # ∀i∀j∀v (Given(i,j,v) ⇒ Val(i,j,v))
        # CNF: Val(i,j,v)  [unit clause]
        grounded.append("\n# A9: Given Clues")
        for i in range(self.n):
            for j in range(self.n):
                val = self.env.grid[i][j]
                if val != 0:
                    grounded.append(f"(Val({i+1},{j+1},{val}))")
        
        # ============= A10: Domain Completeness =============
        # ∀i∀j∀v (Val(i,j,v) ⇒ (v ≥ 1 ∧ v ≤ N))
        # This is implicitly satisfied by our grounding
        grounded.append("\n# A10: Domain Completeness (implicit)")
        
        return grounded

    def get_ground_kb(self):
        """
        Trả về Knowledge Base CNF chứa các mệnh đề CNF (có kèm comment phân loại).
        
        :return: String chứa CNF clauses
        """
        grounded_axioms = self.ground_axioms()
        
        kb_text = ""
        
        # === Đếm số mệnh đề thực sự (bỏ comment và dòng trống) ===
        actual_clauses = [c for c in grounded_axioms if not c.strip().startswith("#") and c.strip()]
        kb_text += f"Total CNF Clauses: {len(actual_clauses)}\n"
        kb_text += "\n"
        
        # Ghi toàn bộ nội dung gồm cả comment ra file
        for line in grounded_axioms:
            kb_text += f"{line}\n"
        
        return kb_text

    def save_kb_to_file(self, output_path):
        """
        Lưu Knowledge Base ra file text (Silent mode - không in log).
        :param output_path: Đường dẫn file output
        """
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        kb_text = self.get_ground_kb()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(kb_text)


# ============================================================================
# TEST & DEMO - Generate CNF from Input File
# ============================================================================

if __name__ == "__main__":
    import os
    from futoshiki_env import FutoshikiEnv
    
    # ===== LOAD INPUT FILE =====
    input_file = "Source/Inputs/input-01.txt"
    
    if not os.path.exists(input_file):
        print(f"✗ Error: File not found: {input_file}")
        exit(1)
    
    try:
        # Load KB from input file (quietly)
        kb_gen = KBGenerator.load_from_file(input_file)
        
        # Lấy tên file gốc (ví dụ: 'input-01')
        base_name = os.path.basename(input_file).replace('.txt', '')
        
        # Save FOL KB (full knowledge base with axioms)
        full_kb = kb_gen.get_full_kb()
        ground_output_path = os.path.join("Source", "Outputs", f"ground_kb_{base_name}.txt")
        os.makedirs(os.path.dirname(ground_output_path), exist_ok=True)
        with open(ground_output_path, 'w', encoding='utf-8') as f:
            f.write(full_kb)
            
        print("✓ Ground KB saved successfully")
        
        # Save CNF/Grounded KB (with CNF clauses)
        cnf_kb = kb_gen.get_ground_kb()
        output_path = os.path.join("Source", "Outputs", f"KB_ground_CNF_{base_name}.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cnf_kb)
        
        print("✓ Ground CNF KB saved successfully")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)