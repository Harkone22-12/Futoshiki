class ForwardChaining:
    def __init__(self, kb, env):
        self.kb = kb
        self.env = env
        self.n = env.n

    def execute(self):
        """
        Thực thi thuật toán Forward Chaining.
        Trả về True nếu suy diễn thành công (không có mâu thuẫn).
        Trả về False nếu phát hiện mâu thuẫn logic (domain rỗng).
        """
        # Khởi tạo hàng đợi với các sự kiện ban đầu từ KB
        agenda = self.kb.facts.copy()
        
        while agenda:
            r, c, val = agenda.pop(0)
            
            # --- 1. Áp dụng luật All-Different (Hàng và Cột) ---
            for i in range(self.n):
                # Thu hẹp domain trên cùng Cột
                if i != r and val in self.kb.domains[i][c]:
                    self.kb.domains[i][c].remove(val)
                    # Nếu ô chỉ còn 1 giá trị khả dĩ -> Trở thành Fact mới
                    if len(self.kb.domains[i][c]) == 1:
                        agenda.append((i, c, list(self.kb.domains[i][c])[0]))
                    # Nếu ô không còn giá trị nào -> Mâu thuẫn
                    elif len(self.kb.domains[i][c]) == 0:
                        return False

                # Thu hẹp domain trên cùng Hàng
                if i != c and val in self.kb.domains[r][i]:
                    self.kb.domains[r][i].remove(val)
                    if len(self.kb.domains[r][i]) == 1:
                        agenda.append((r, i, list(self.kb.domains[r][i])[0]))
                    elif len(self.kb.domains[r][i]) == 0:
                        return False

            # --- 2. Áp dụng luật Bất đẳng thức ---
            # Sử dụng danh sách ràng buộc từ Environment
            for constraint in self.env.constraints_list:
                ctype, r1, c1, r2, c2 = constraint
                
                # TH1: Sự kiện hiện tại nằm ở Vế Trái của bất đẳng thức
                if r == r1 and c == c1:
                    to_remove = []
                    for v2 in self.kb.domains[r2][c2]:
                        if (ctype == '<' and not (val < v2)) or (ctype == '>' and not (val > v2)):
                            to_remove.append(v2)
                            
                    for v2 in to_remove:
                        self.kb.domains[r2][c2].remove(v2)
                        if len(self.kb.domains[r2][c2]) == 1:
                            agenda.append((r2, c2, list(self.kb.domains[r2][c2])[0]))
                        elif len(self.kb.domains[r2][c2]) == 0:
                            return False

                # TH2: Sự kiện hiện tại nằm ở Vế Phải của bất đẳng thức
                elif r == r2 and c == c2:
                    to_remove = []
                    for v1 in self.kb.domains[r1][c1]:
                        if (ctype == '<' and not (v1 < val)) or (ctype == '>' and not (v1 > val)):
                            to_remove.append(v1)
                            
                    for v1 in to_remove:
                        self.kb.domains[r1][c1].remove(v1)
                        if len(self.kb.domains[r1][c1]) == 1:
                            agenda.append((r1, c1, list(self.kb.domains[r1][c1])[0]))
                        elif len(self.kb.domains[r1][c1]) == 0:
                            return False
                            
        return True