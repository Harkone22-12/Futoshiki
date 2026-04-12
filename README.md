# 🧩 Futoshiki Puzzle Solver

Giải Futoshiki puzzle sử dụng Forward/Backward Chaining, A\*, Backtracking, Brute Force.

---

## 📋 Mục lục

1. [Giới thiệu](#giới-thiệu)
2. [Cấu trúc dự án](#cấu-trúc-dự-án)
3. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
4. [Cách cài đặt](#cách-cài-đặt)
5. [Hướng dẫn chạy](#hướng-dẫn-chạy)
6. [Các thuật toán](#các-thuật-toán)
7. [Thư viện sử dụng](#thư-viện-sử-dụng)
8. [Lưu ý khi sử dụng](#lưu-ý-khi-sử-dụng)

---

## Giới thiệu

**Futoshiki** là trò chơi logic giống Sudoku với ràng buộc bất đẳng thức giữa các ô liền kề.

**Luật chơi:**

- Mỗi ô: số 1 đến N
- Mỗi dòng: 1 đến N (không trùng)
- Mỗi cột: 1 đến N (không trùng)
- Tuân theo `<` `>` giữa các ô liền kề

**Ví dụ 4×4:**

```
3 > 1 < 4 2
2 < 3 > 1 4
4 > 2 < 3 1
1 < 4 > 2 3
```

---

## Cấu trúc dự án

```
Futoshiki/
├── README.md
├── requirements.txt
│
└── Source/
    ├── main.py                         # Chương trình chính
    ├── futoshiki_env.py                # Môi trường puzzle
    ├── KB_generator.py                 # Tạo KB từ FOL
    │
    ├── Forward_chaining.py             # Forward Chaining
    ├── Backward_chaining.py            # Backward Chaining
    ├── Astar_ac3.py                    # A* với AC3
    ├── Astar_mbdt.py                   # A* với MBDT
    ├── Astar_mrc.py                    # A* với MRC
    ├── Backtracking.py                 # Backtracking
    ├── Bruteforce.py                   # Brute Force
    │
    ├── benchmark.py                    # Chạy benchmark
    ├── Inputs/                         # File input (input-01.txt - input-10.txt)
    ├── Outputs/                        # Kết quả output
    └── Benchmarks/                     # Kết quả benchmark
```

---

## Yêu cầu hệ thống

- **Python 3.12+**
- **pip** (package manager)
- **Windows / macOS / Linux**

---

## Cách cài đặt

### 1. Clone repository

```bash
git clone https://github.com/yourusername/Futoshiki.git
cd Futoshiki
```

### 2. Tạo virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

---

## Hướng dẫn chạy

### Chạy một thuật toán

```bash
python Source/main.py
```

### Chạy benchmark (tất cả thuật toán)

```bash
python Source/benchmark.py
```

### Phân tích kết quả

```bash
python Source/benchmark_report.py
python Source/memory_analysis.py
```

### Ví dụ mã

```python
from futoshiki_env import FutoshikiEnv
from Forward_chaining import solve_forward_chaining

env = FutoshikiEnv(4)
solution = solve_forward_chaining(env)
print(solution)
```

---

## Các thuật toán

| Thuật toán        | Loại      | Mô tả                       |
| ----------------- | --------- | --------------------------- |
| Forward Chaining  | Inference | Suy luận từ trên xuống      |
| Backward Chaining | Inference | Suy luận từ dưới lên (SLD)  |
| A\* AC3           | Search    | Tìm kiếm với AC3 heuristic  |
| A\* MBDT          | Search    | Tìm kiếm với MBDT heuristic |
| A\* MRC           | Search    | Tìm kiếm với MRC heuristic  |
| Backtracking      | Search    | Tìm kiếm Depth-First        |
| Brute Force       | Search    | Liệt kê toàn bộ             |

---

## Thư viện sử dụng

```
python-sat==1.9.dev2     # SAT solver (Glucose3)
six==1.17.0              # Python 2/3 compatibility
psutil>=5.9.0            # Đo bộ nhớ sử dụng
pandas>=2.0.0            # Xử lý dữ liệu CSV
```

---

## Lưu ý khi sử dụng

### Định dạng file input

```
N                        # Kích thước lưới
v11 v12 ... v1n         # Lưới (0 = trống)
...
h11 h12 ... h1(n-1)     # Ràng buộc ngang (0/1/-1)
...
v11 v12 ... v1n         # Ràng buộc dọc (0/1/-1)
```

- `0` = không có ràng buộc
- `1` = `<` (trái < phải / trên < dưới)
- `-1` = `>` (trái > phải / trên > dưới)

### Hiệu suất

- 4×4 - 5×5: Mọi thuật toán OK
- 6×6 - 7×7: A\* nhanh hơn
- 9×9+: Có thể timeout với brute force

### Memory

- Benchmark: ~50-100MB
- Lưới 9×9: Có thể >100MB

### Timeout

- FC/BC: Có thể fail nếu puzzle khó
- A\*: Thường nhanh nhất
- Brute Force: Tốt cho lưới nhỏ

---

## FOL Formalization

Dự án sử dụng First-Order Logic để mô hình hóa Futoshiki puzzle.

### Predicates

- `Val(i, j, v)` - Ô (i,j) có giá trị v
- `Given(i, j, v)` - Ô (i,j) là clue có giá trị v
- `LessH(i, j)` - Ràng buộc ngang: (i,j) < (i,j+1)
- `GreaterH(i, j)` - Ràng buộc ngang: (i,j) > (i,j+1)
- `LessV(i, j)` - Ràng buộc dọc: (i,j) < (i+1,j)
- `GreaterV(i, j)` - Ràng buộc dọc: (i,j) > (i+1,j)
- `Less(v1, v2)` - Quan hệ: v1 < v2

### Axioms

- **A1**: Mỗi ô có ít nhất một giá trị: ∀i∀j∃v Val(i,j,v)
- **A2**: Mỗi ô có tối đa một giá trị: ∀i∀j∀v1∀v2 (Val(i,j,v1) ∧ Val(i,j,v2)) → v1 = v2
- **A3**: Duy nhất theo hàng (Row Uniqueness): ∀i∀j1∀j2∀v (Val(i,j1,v) ∧ Val(i,j2,v) ∧ j1≠j2) → ⊥
- **A4**: Duy nhất theo cột (Column Uniqueness): ∀j∀i1∀i2∀v (Val(i1,j,v) ∧ Val(i2,j,v) ∧ i1≠i2) → ⊥
- **A5**: Ràng buộc < theo hàng: ∀i∀j∀v1∀v2 (LessH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2)) → Less(v1,v2)
- **A6**: Ràng buộc < theo cột: ∀i∀j∀v1∀v2 (LessV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2)) → Less(v1,v2)
- **A7**: Ràng buộc > theo hàng: ∀i∀j∀v1∀v2 (GreaterH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2)) → Greater(v1,v2)
- **A8**: Ràng buộc > theo cột: ∀i∀j∀v1∀v2 (GreaterV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2)) → Greater(v1,v2)
- **A9**: Tôn trọng clues cho trước: ∀i∀j∀v (Given(i,j,v) → Val(i,j,v))
- **A10**: Giá trị trong miền [1..N]: ∀i∀j∀v (Val(i,j,v) → (v ≥ 1 ∧ v ≤ N))

---

## Format Input/Output

### Input Format

```
N                        # Kích thước lưới
v11 v12 ... v1n         # Lưới ban đầu (0 = trống, 1..N = clue)
...
h11 h12 ... h1(n-1)     # Ràng buộc ngang
...
v11 v12 ... v1n         # Ràng buộc dọc
```

### Output Format

```
Lưới đã giải với dấu: <, > giữa các ô
Ví dụ:
3 > 1 < 4 2
2 ^ 3 > 1 4
4 > 2 v 3 1
1 < 4 > 2 ^ 3
```

---

## Cách Thực Hiện

### Forward Chaining

- Sử dụng rule-based inference
- Suy luận facts từ Known facts
- Kiểm tra contradiction

### Backward Chaining (SLD Resolution)

- Prolog-style depth-first search
- Query từng ô: Val(i, j, ?)
- Backtrack nếu fail

### A\* Search

- Tìm kiếm với heuristic
- AC3, MBDT, hoặc MRC
- Expand nodes theo f(n) = g(n) + h(n)

### Backtracking

- Depth-first search
- Constraint checking tại mỗi bước
- Backtrack nếu vi phạm

### Brute Force

- Liệt kê tất cả permutations
- Check constraints
- Nhậu khi tìm được solution

---

## Knowledge Base

Dự án tạo Knowledge Base từ FOL axioms:

- `ground_kb_inputXX.txt` - FOL facts
- `KB_ground_CNF_inputXX.txt` - CNF clauses

---

**Project**: CSC14003 - AI Fundamentals
**Nhóm**: 4 members | **Thời gian**: ~3 weeks

# 🧩 Futoshiki Puzzle Solver

Giải Futoshiki puzzle sử dụng Forward/Backward Chaining, A\*, Backtracking, Brute Force.

---

## 📋 Mục lục

1. [Giới thiệu](#giới-thiệu)
2. [Cấu trúc dự án](#cấu-trúc-dự-án)
3. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
4. [Cách cài đặt](#cách-cài-đặt)
5. [Hướng dẫn chạy](#hướng-dẫn-chạy)
6. [Các thuật toán](#các-thuật-toán)
7. [Thư viện sử dụng](#thư-viện-sử-dụng)
8. [Lưu ý khi sử dụng](#lưu-ý-khi-sử-dụng)

---

## Giới thiệu

**Futoshiki** là trò chơi logic giống Sudoku với ràng buộc bất đẳng thức giữa các ô liền kề.

**Luật chơi:**

- Mỗi ô: số 1 đến N
- Mỗi dòng: 1 đến N (không trùng)
- Mỗi cột: 1 đến N (không trùng)
- Tuân theo `<` `>` giữa các ô liền kề

**Ví dụ 4×4:**

```
3 > 1 < 4 2
2 < 3 > 1 4
4 > 2 < 3 1
1 < 4 > 2 3
```

---

## 🎯 Core Requirements

This project must implement:

### 1. **FOL Formalization (Report)**

- Write all First-Order Logic axioms for Futoshiki
- Derive Skolemized and CNF forms for at least 3 axioms step-by-step
- Handle predicates: `Val(i,j,v)`, `Given(i,j,v)`, `LessH(i,j)`, `GreaterH(i,j)`, `LessV(i,j)`, `GreaterV(i,j)`, `Less(v1,v2)`

### 2. **Inference & Search Algorithms**

- **Automatic KB Generation**: Convert FOL axioms to ground knowledge base for any N
- **Forward Chaining**: Implement from scratch to propagate facts and detect contradictions
- **Backward Chaining**: Implement SLD resolution (Prolog-style) to query individual cell values
- **A\* Search**: Implement with justified admissible heuristic for partial assignments
- **Comparison Algorithms**: Brute-force and backtracking for baseline comparison

### 3. **A\* Heuristic Requirements**

- Design an **admissible heuristic** h(s) for partial assignments
- Possible approaches:
  - Count remaining unassigned cells (trivially admissible but weak)
  - Estimate unfulfilled inequality chains
  - Use arc-consistency (AC-3) as informed lower bound
- Justify admissibility in report

---

## 🤖 Algorithms Required

### **Mandatory Implementations (from scratch)**

1. **Forward Chaining**
   - Rule-based inference using Modus Ponens
   - Propagate facts exhaustively until fixpoint
   - Detect contradictions

2. **Backward Chaining (SLD Resolution)**
   - Prolog-style depth-first search
   - Query individual cell values: `Val(i, j, ?)`
   - Use Horn clause encoding

3. **A\* Search**
   - Admissible heuristic function h(s)
   - Search over partial assignments
   - Prune branches violating FOL constraints

### **Comparison Algorithms**

4. **Brute Force** - Exhaustive enumeration
5. **Backtracking** - Depth-first with constraint checking

### **Optional Supplements**

- External libraries (pysat, clingo, z3) may be used for **verification only**
- Main algorithms must be fully implemented by the team

---

## � FOL Formalization

The project requires formal specification using First-Order Logic:

### Core Predicates

- `Val(i, j, v)` - Cell (i,j) is assigned value v
- `Given(i, j, v)` - Cell (i,j) has pre-filled clue value v
- `LessH(i, j)` - Horizontal constraint: (i,j) < (i,j+1)
- `GreaterH(i, j)` - Horizontal constraint: (i,j) > (i,j+1)
- `LessV(i, j)` - Vertical constraint: (i,j) < (i+1,j)
- `GreaterV(i, j)` - Vertical constraint: (i,j) > (i+1,j)
- `Less(v1, v2)` - Background relation: v1 < v2

### Required Axioms

**Students must derive:**

- A1: Every cell has at least one value
- A2: Every cell has at most one value
- A3: Row uniqueness
- A4: Horizontal inequality constraints
- A5: Given clues are enforced
- A6: Column uniqueness
- A7: Vertical inequality constraints
- A8: Value range constraints (1 to N)

**Report must include:**

- Full FOL axiom derivations
- CNF conversions (Skolemization + distribution)
- Step-by-step examples on 4×4 puzzles

---

## �📁 Project Structure

```
Futoshiki/
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
│
└── Source/
    ├── main.py                        # Entry point for solving
    ├── benchmark.py                   # Performance testing framework
    ├── benchmark_report.py            # Analysis & report generation
    ├── memory_analysis.py             # Memory usage analysis
    │
    ├── futoshiki_env.py               # Puzzle environment & constraints
    ├── input_generator.py             # Generate random puzzles
    ├── KB_generator.py                # FOL → CNF conversion
    │
    ├── satsolver.py                   # SAT solver implementation
    │
    ├── Forward_chaining.py            # Pure forward chaining
    ├── Backward_chaining.py           # SLD resolution
    │
    ├── Astar_ac3.py                   # A* with AC3 heuristic
    ├── Astar_mbdt.py                  # A* with MBDT heuristic
    ├── Astar_mrc.py                   # A* with MRC heuristic
    │
    ├── Astar_ac3_Forward.py           # A* AC3 + Forward Chaining
    ├── Astar_mbdt_Forward.py          # A* MBDT + Forward Chaining
    ├── Astar_mrc_Forward.py           # A* MRC + Forward Chaining
    │
    ├── Backtracking.py                # Pure backtracking search
    ├── Backtracking_Forward.py        # Backtracking + Forward Chaining
    ├── Bruteforce.py                  # Brute force enumeration
    │
    ├── Inputs/                        # Test cases (4×4 to 9×9)
    │   ├── input-01.txt to input-10.txt
    │
    ├── Outputs/                       # Generated knowledge bases
    │   ├── ground_kb_input01.txt
    │   └── KB_ground_CNF_input01.txt
    │
    └── Benchmarks/                    # Performance results
        └── benchmark_results_full.csv
```

---

## ⚙️ Installation & Setup

### Prerequisites

- **Python 3.12+** (tested with Python 3.12.4)
- **pip** package manager

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/Futoshiki.git
cd Futoshiki
```

### Step 2: Create Virtual Environment

```bash
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required Packages:**

- `python-sat==1.9.dev2` - SAT solver (Glucose3)
- `six==1.17.0` - Python 2/3 compatibility
- `psutil>=5.9.0` - Memory measurement
- `pandas>=2.0.0` - Data analysis

### Step 4: Verify Installation

```bash
python Source/benchmark.py
```

---

## 🚀 Quick Start

### Run a Single Algorithm

```python
from futoshiki_env import FutoshikiEnv
from Astar_mbdt_Forward import solve_astar_mac_mbdt

# Create 4×4 puzzle environment
env = FutoshikiEnv(4)

# Load puzzle from file
# (Add your puzzle loading logic here)

# Solve puzzle
solution, nodes_expanded = solve_astar_mac_mbdt(env)
print(f"Solution:\n{solution}")
print(f"Nodes explored: {nodes_expanded}")
```

### Run Benchmarks

```bash
# Full benchmark on all test cases
python Source/benchmark.py

# Generate analysis report
python Source/benchmark_report.py

# Analyze memory usage
python Source/memory_analysis.py
```

---

## 📝 Input & Output Format

### Input Specifications

- **Minimum 10 test files**: `input-01.txt` to `input-10.txt`
- **Coverage**: 4×4, 5×5, 6×6, 7×7, 9×9 grids (at least 2 cases each size)

### Input File Format

```
N                           # Grid size
# Grid (N lines of N values)
v11, v12, ..., v1n          # Row 1 (0 = empty, 1..N = pre-filled)
...
vN1, vN2, ..., vNN          # Row N

# Horizontal constraints (N lines of N-1 values)
h11, h12, ..., h1(n-1)      # Row 1
...
# 0 = no constraint
# 1 = '<' (left < right)
# -1 = '>' (left > right)

# Vertical constraints (N-1 lines of N values)
v11, v12, ..., v1n          # Between rows 1-2
...
# 0 = no constraint
# 1 = '<' (top < bottom)
# -1 = '>' (top > bottom)
```

### Output Format

- **Output file**: `output-XX.txt` (matching input filename)
- **Format**: Solved grid with inequality signs between cells
- **Example for 4×4**:

```
2 < 3 4 1
v
1 2 > 3 4
^
4 1 2 3
^
3 4 1 < 2
```

### Example Input File (4×4)

```
4
0 0 0 0
0 0 0 0
0 0 0 0
0 0 0 0
0 0 0 0
1 0 2 0
0 0 0 0
0 1 0 0
0 0 0 0
1 0 2 0
0 0 0 0
```

---

## 📊 Assessment Rubric

| Criterion | Score | Requirements |
|-----------|-------|──────────────|
| FOL Formalization | 25% | Complete FOL axioms, Skolemized/CNF forms, step-by-step derivations |
| Automatic KB Generation | 10% | Function generates ground KB for any N |
| Forward Chaining | 15% | Correct implementation, valid solutions on all test cases |
| Backward Chaining (SLD) | 10% | Prolog-style interpreter, query individual cells |
| A\* Search | 10% | Admissible heuristic, expansion count comparison |
| Comparison Algorithms | 5% | Brute-force and backtracking, performance comparison |
| Report & Experiments | 25% | 10 test cases, performance tables, comparative analysis |

### Evaluation Criteria

- **Correctness**: All algorithms produce valid solutions
- **Implementation Quality**: Code is clean and well-documented
- **FOL Rigor**: Axioms properly formalized and justified
- **Heuristic Admissibility**: Proven or argued in report
- **Comprehensive Testing**: Results across all grid sizes
- **Performance Analysis**: Charts and performance discussion

---

## 📚 Knowledge Base Generation

The project includes FOL (First-Order Logic) to CNF (Conjunctive Normal Form) conversion:

**FOL Axioms:**

```
Uniqueness: ∀i∀j¬(Val(i,j,v1) ∧ Val(i,j,v2))
Existence: ∀i∀j⋁ᵥ Val(i,j,v)
Row uniqueness: ∀i∀v¬(Val(i,j,v) ∧ Val(i,k,v))
Col uniqueness: ∀j∀v¬(Val(i,j,v) ∧ Val(k,j,v))
Inequality constraints: Given >, < between cells
```

**Output Files:**

- `ground_kb_input01.txt` - FOL facts (given values, constraints)
- `KB_ground_CNF_input01.txt` - CNF clauses for SAT solver

---

## � Report Requirements

Your project report must include:

### 1. **FOL Formalization** (25%)

- Complete vocabulary definition
- All axioms in FOL with detailed explanations
- Conversion to Prenex Normal Form
- Skolemization with examples
- Full CNF derivation for ≥3 axioms
- Step-by-step resolution proofs

### 2. **Knowledge Base Generation** (10%)

- Ground KB construction algorithm
- FOL to CNF conversion process
- Clauses generated for different grid sizes
- Propagation rules implementation

### 3. **Forward Chaining Implementation** (15%)

- Algorithm description with pseudocode
- Rule firing mechanism
- Contradiction detection
- Fixpoint computation
- Performance on each test case

### 4. **Backward Chaining (SLD Resolution)** (10%)

- SLD resolution algorithm
- Query engine implementation
- Proof trees and substitutions
- Results on test cases

### 5. **A\* Search with Heuristic** (10%)

- Heuristic function definition
- Admissibility proof or justification
- State representation
- Expansion count comparison
- Performance analysis

### 6. **Comparison Analysis** (5%)

- Brute-force vs Backtracking results
- Node expansion counts
- Solution quality comparison
- Scalability discussion

### 7. **Experiments & Results** (25%)

- Test results table for all 10 cases
- Runtime and node expansion comparisons
- Memory usage analysis
- Visualization (charts/graphs)
- Conclusions and observations

---

## 📦 Dependencies

**Core Dependencies:**

```
python-sat==1.9.dev2        # Glucose3 SAT solver
six==1.17.0                 # Python 2/3 compatibility
psutil>=5.9.0               # System resource monitoring
pandas>=2.0.0               # Data analysis and CSV handling
```

**Installation:**

```bash
pip install -r requirements.txt
```

---

## � Knowledge Base Generation

The project includes automatic conversion from FOL axioms to CNF:

### Core Axioms (Examples)

```
A1: ∀i∀j∃v Val(i,j,v)              # Every cell has a value
A2: ∀i∀j∀v1∀v2 (Val(i,j,v1) ∧ Val(i,j,v2)) → v1=v2  # Unique value per cell
A3: ∀i∀v¬(Val(i,j1,v) ∧ Val(i,j2,v)) where j1≠j2    # Row uniqueness
A4: ∀j∀v¬(Val(i1,j,v) ∧ Val(i2,j,v)) where i1≠i2    # Column uniqueness
A5: ∀i∀j Given(i,j,v) → Val(i,j,v)  # Enforce given clues
A6: ∀i∀j LessH(i,j) → Val(i,j) < Val(i,j+1)  # Horizontal constraints
A7: ∀i∀j LessV(i,j) → Val(i,j) < Val(i+1,j)  # Vertical constraints
```

### Output Files Generated

- `ground_kb_input01.txt` - Grounded FOL facts
- `KB_ground_CNF_input01.txt` - CNF clauses ready for SAT/Resolution

## 📞 Support

For questions about implementation:

- Review the FOL axioms section for knowledge representation
- Check algorithm pseudocode in the source files
- Consult the project PDF specification for requirements
- Run `python Source/benchmark.py` to verify all algorithms work

---

**Project**: CSC14003 - Fundamentals of Artificial Intelligence (Futoshiki Puzzle Solver)  
**Duration**: ~3 weeks  
**Group Assignment**: 4 members

_This is an educational project demonstrating AI problem-solving techniques through First-Order Logic reasoning and multiple search algorithms._
