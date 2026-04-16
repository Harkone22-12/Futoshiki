import time
import traceback
import queue as std_queue
import multiprocessing as mp
import csv
import re
import tracemalloc
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from futoshiki_env import FutoshikiEnv

from Bruteforce import solve_bruteforce
from Backtracking import solve_backtracking
from Backtracking_Forward import (
    ForwardChaining as FCBacktracking,
    KnowledgeBase as KBBacktracking,
    solve_with_bfc,
)
from Backward_chaining import SLDResolutionEngine
from Forward_chaining import solve_pure_fc

from Astar_ac3 import solve_astar_ac3
from Astar_ac3_Forward import solve_astar_mac_ac3
from Astar_mbdt import solve_astar_mbdt
from Astar_mbdt_Forward import solve_astar_mac_mbdt
from Astar_mrc import solve_astar_mrc
from Astar_mrc_Forward import solve_astar_mac_mrc
from chart_report import ChartReportController

try:
    from satsolver import FutoshikiSATSolver
    SAT_AVAILABLE = True
except Exception:
    FutoshikiSATSolver = None
    SAT_AVAILABLE = False

BASE_DIR   = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "Inputs"
OUTPUTS_DIR = BASE_DIR / "Outputs"
RUN_LOG_FILE = OUTPUTS_DIR / "solve-log.csv"
SOLVER_TIMEOUT_SEC = 120
RUN_LOG_HEADER = [
    "timestamp",
    "input_file",
    "size",
    "algorithm",
    "heuristic",
    "fc_prune",
    "status",
    "elapsed_sec",
    "nodes",
    "peak_memory_mb",
    "output_file",
    "note",
]

# ── Palette ───────────────────────────────────────────────────────────────────
P = {
    "bg":        "#07090f",
    "surf0":     "#0d1117",
    "surf1":     "#131923",
    "surf2":     "#192230",
    "border":    "#1e2d3d",
    "border_hi": "#28405a",
    "fg":        "#dce8f5",
    "fg_mid":    "#7a96b4",
    "fg_dim":    "#3d556e",
    "teal":      "#00d9a6",
    "teal_dk":   "#00b389",
    "green":     "#29cc6e",
    "amber":     "#f5a623",
    "red":       "#e8445a",
    "cell_bg":   "#0f1720",
    "cell_bdr":  "#1a2a3a",
    "cell_pre":  "#141f2e",
    "cell_diff": "#1c1608",   # amber-tinted bg for changed cells
    "diff_bdr":  "#f5a623",   # amber border for changed cells
}

UI   = "Segoe UI"
MONO = "Consolas"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_env_from_file(fp):
    with open(fp, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    n = int(lines[0])
    env = FutoshikiEnv(n)
    for i in range(1, n + 1):
        vals = [int(x) for x in lines[i].split(",")]
        for j in range(n):
            if vals[j]: env.set_given_value(i - 1, j, vals[j])
    for i in range(n + 1, 2 * n + 1):
        vals = [int(x) for x in lines[i].split(",")]
        for j in range(n - 1):
            if vals[j]: env.add_horizontal_constraint(i - (n + 1), j, vals[j])
    for i in range(2 * n + 1, 3 * n):
        vals = [int(x) for x in lines[i].split(",")]
        for j in range(n):
            if vals[j]: env.add_vertical_constraint(i - (2 * n + 1), j, vals[j])
    return env

def clone_grid(g):  return [r[:] for r in g]
def complete(g):    return all(c != 0 for row in g for c in row)

def rrect(cv, x1, y1, x2, y2, r=8, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
           x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
           x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return cv.create_polygon(pts, smooth=True, **kw)


def board_to_output_text(grid, hc, vc):
    n = len(grid)
    lines = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(str(grid[i][j]) if grid[i][j] != 0 else ".")
            if j < n - 1:
                if hc[i][j] == 1:
                    row.append("<")
                elif hc[i][j] == -1:
                    row.append(">")
                else:
                    row.append(" ")
        lines.append(" ".join(row))

        if i < n - 1:
            vrow = []
            for j in range(n):
                if vc[i][j] == 1:
                    vrow.append("^")
                elif vc[i][j] == -1:
                    vrow.append("v")
                else:
                    vrow.append(" ")
                if j < n - 1:
                    vrow.append(" ")
            lines.append(" ".join(vrow))

    return "\n".join(lines)


def next_output_file_path():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(r"^output-(\d+)\.txt$")
    max_idx = 0

    for p in OUTPUTS_DIR.glob("output-*.txt"):
        m = pattern.match(p.name)
        if m:
            max_idx = max(max_idx, int(m.group(1)))

    return OUTPUTS_DIR / f"output-{max_idx + 1}.txt"


def solve_payload(path, algo, heur, fc):
    path = Path(path)
    env = load_env_from_file(path)
    t0 = time.perf_counter()
    solved = False
    sol = None
    nodes = "N/A"
    note = ""
    peak_bytes = 0

    tracemalloc.start()
    try:
        if algo == "A* Search":
            if fc:
                fns = {
                    "AC3": solve_astar_mac_ac3,
                    "MBDT": solve_astar_mac_mbdt,
                    "MRC": solve_astar_mac_mrc,
                }
                sol, nodes = fns[heur](env)
                solved = sol is not None
            else:
                g = clone_grid(env.grid)
                fns = {
                    "AC3": solve_astar_ac3,
                    "MBDT": solve_astar_mbdt,
                    "MRC": solve_astar_mrc,
                }
                res = fns[heur](g, env.n, env.horiz_constraints, env.vert_constraints)
                rep = bool(res[0]) if isinstance(res, tuple) else False
                nodes = res[1] if isinstance(res, tuple) else "N/A"
                solved = rep or complete(g)
                sol = g if solved else None

        elif algo == "Backtracking":
            g = clone_grid(env.grid)
            solved, nodes = solve_backtracking(g, env.n, env.horiz_constraints, env.vert_constraints)
            sol = g if solved else None

        elif algo == "Backtracking + Forward Chaining":
            kb = KBBacktracking(env.n)
            for r in range(env.n):
                for c in range(env.n):
                    v = env.grid[r][c]
                    if v:
                        kb.domains[r][c] = {v}
                        kb.facts.append((r, c, v))
            if FCBacktracking(kb, env).execute():
                res = solve_with_bfc(kb, env)
                if isinstance(res, tuple) and len(res) >= 2:
                    sol, nodes = res
                    solved = sol is not None
            else:
                note = "Forward chaining found a contradiction."

        elif algo == "Brute Force":
            g = clone_grid(env.grid)
            solved, nodes = solve_bruteforce(g, env.n, env.horiz_constraints, env.vert_constraints)
            sol = g if solved else None

        elif algo == "Pure Forward Chaining":
            sol, note = solve_pure_fc(env)
            solved = sol is not None

        elif algo == "Backward Chaining (SLD)":
            sld = SLDResolutionEngine(env)
            solved = sld.prove_board()
            nodes = sld.nodes_expanded
            sol = sld.grid if solved else None

        elif algo == "SAT Solver":
            if not SAT_AVAILABLE:
                raise RuntimeError("Install python-sat to enable SAT Solver.")
            s = FutoshikiSATSolver(env)
            sol, nodes = s.solve()
            solved = sol is not None
            note = f"CNF clauses: {len(s.cnf_strings)}"

        else:
            raise RuntimeError(f"Unknown: {algo}")
    finally:
        try:
            _, peak_bytes = tracemalloc.get_traced_memory()
        except Exception:
            peak_bytes = 0
        try:
            tracemalloc.stop()
        except Exception:
            pass

    elapsed = time.perf_counter() - t0
    peak_memory_mb = peak_bytes / (1024 * 1024)
    return {
        "file": path.name,
        "n": env.n,
        "algo": algo,
        "heur": heur,
        "fc": fc,
        "solved": solved,
        "nodes": nodes,
        "elapsed": elapsed,
        "peak_memory_mb": round(peak_memory_mb, 4),
        "note": note,
        "sol": clone_grid(sol if solved else env.grid),
        "hc": [r[:] for r in env.horiz_constraints],
        "vc": [r[:] for r in env.vert_constraints],
        "given": {(r, c) for r in range(env.n) for c in range(env.n) if env.grid[r][c] != 0},
    }


def solver_worker(payload, out_q):
    try:
        result = solve_payload(
            path=payload["path"],
            algo=payload["algo"],
            heur=payload["heur"],
            fc=payload["fc"],
        )
        out_q.put({"ok": True, "result": result})
    except Exception as ex:
        out_q.put({
            "ok": False,
            "error": str(ex),
            "trace": traceback.format_exc(),
        })


# ── Widgets ───────────────────────────────────────────────────────────────────

class RunButton(tk.Canvas):
    def __init__(self, master, text, command=None, **kw):
        kw.setdefault("height", 40)
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("bd", 0)
        super().__init__(master, bg=P["surf0"], **kw)
        self._text = text; self._cmd = command; self._hov = False; self._enabled = True
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>",    self._en)
        self.bind("<Leave>",    self._lv)
        self.bind("<Button-1>", self._cl)

    def _draw(self, _=None):
        self.delete("all")
        w = self.winfo_width()  or int(self.cget("width")  or 200)
        h = self.winfo_height() or int(self.cget("height") or 40)
        if self._enabled:
            fill = P["teal_dk"] if self._hov else P["teal"]
            text_col = "#051a10"
        else:
            fill = P["surf2"]
            text_col = P["fg_dim"]
        rrect(self, 3, 3, w-3, h-3, r=h//2-3, fill=fill, outline="")
        self.create_text(w//2, h//2, text=self._text,
                         fill=text_col, font=(UI, 10, "bold"))

    def _en(self, _):
        if not self._enabled: return
        self._hov = True; self._draw(); self.config(cursor="hand2")

    def _lv(self, _):
        self._hov = False; self._draw(); self.config(cursor="")

    def _cl(self, _):
        if self._enabled and self._cmd: self._cmd()

    def enable(self, on):
        self._enabled = bool(on)
        if not self._enabled:
            self._hov = False
            self.config(cursor="")
        self._draw()


class Dropdown(tk.Frame):
    def __init__(self, master, values, var, on_change=None, max_height=220, **kw):
        super().__init__(master, bg=P["surf1"], bd=0,
                         highlightthickness=1, highlightbackground=P["border"], **kw)
        self._var = var; self._values = values; self._cb = on_change
        self._open = False; self._popup = None; self._enabled = True
        self._max_height = max_height

        top = tk.Frame(self, bg=P["surf1"], cursor="hand2")
        top.pack(fill="x")
        self._lbl = tk.Label(top, textvariable=var, bg=P["surf1"], fg=P["fg"],
                             font=(UI, 9), anchor="w", padx=10, pady=9)
        self._lbl.pack(side="left", fill="x", expand=True)
        self._arr = tk.Label(top, text="▾", bg=P["surf1"], fg=P["teal"],
                             font=(UI, 9), padx=8)
        self._arr.pack(side="right")

        for w in (top, self._lbl, self._arr):
            w.bind("<Button-1>", self._toggle)
            w.bind("<Enter>", lambda e: self._en())
            w.bind("<Leave>", lambda e: self._lv())

    def _en(self):
        if self._enabled:
            self.config(highlightbackground=P["teal"])
    def _lv(self):
        self.config(highlightbackground=P["border"])

    def _toggle(self, _=None):
        if not self._enabled: return
        self._close() if self._open else self._show()

    def _show(self):
        self._open = True; self._arr.config(text="▴")
        p = tk.Toplevel(self, bg=P["surf2"])
        p.wm_overrideredirect(True); p.lift()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = self.winfo_width()
        full_h = len(self._values) * 32 + 4
        popup_h = min(full_h, self._max_height)
        p.geometry(f"{w}x{popup_h}+{x}+{y}")
        p.config(highlightthickness=1, highlightbackground=P["border_hi"])

        cv = tk.Canvas(p, bg=P["surf2"], highlightthickness=0)
        sb = tk.Scrollbar(p, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=sb.set)
        inner = tk.Frame(cv, bg=P["surf2"])
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=inner, anchor="nw", width=w)

        def _wheel(event):
            if event.delta:
                cv.yview_scroll(int(-event.delta / 120), "units")
            elif getattr(event, "num", None) == 4:
                cv.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                cv.yview_scroll(1, "units")
            return "break"

        for v in self._values:
            row = tk.Frame(inner, bg=P["surf2"], cursor="hand2")
            row.pack(fill="x")
            lbl = tk.Label(row, text=v, bg=P["surf2"], fg=P["fg"],
                           font=(UI, 9), anchor="w", padx=12, pady=7)
            lbl.pack(fill="x")
            for ww in (row, lbl):
                ww.bind("<Enter>",    lambda e, l=lbl: l.config(fg=P["teal"], bg=P["surf1"]))
                ww.bind("<Leave>",    lambda e, l=lbl: l.config(fg=P["fg"],   bg=P["surf2"]))
                ww.bind("<Button-1>", lambda e, val=v: self._pick(val))

        need_scroll = full_h > self._max_height
        if need_scroll:
            sb.pack(side="right", fill="y")
        cv.pack(fill="both", expand=True)
        cv.bind("<MouseWheel>", _wheel)
        inner.bind("<MouseWheel>", _wheel)
        cv.bind("<Button-4>", _wheel)
        cv.bind("<Button-5>", _wheel)
        inner.bind("<Button-4>", _wheel)
        inner.bind("<Button-5>", _wheel)
        p.bind("<FocusOut>", lambda e: self._close()); p.focus_set()
        self._popup = p

    def _pick(self, val):
        self._var.set(val); self._close()
        if self._cb: self._cb()

    def _close(self):
        self._open = False; self._arr.config(text="▾")
        if self._popup: self._popup.destroy(); self._popup = None

    def enable(self, on):
        self._enabled = on
        self._lbl.config(fg=P["fg"] if on else P["fg_dim"])
        self._arr.config(fg=P["teal"] if on else P["fg_dim"])
        self.config(highlightbackground=P["border"])


class Chip(tk.Frame):
    def __init__(self, master, label, var, color, **kw):
        super().__init__(master, bg=P["surf0"], **kw)
        tk.Label(self, text=label, bg=P["surf0"], fg=P["fg_mid"],
                 font=(UI, 7)).pack(anchor="w")
        tk.Label(self, textvariable=var, bg=P["surf0"], fg=color,
                 font=(UI, 12, "bold")).pack(anchor="w")


# ── App ───────────────────────────────────────────────────────────────────────

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Futoshiki Solver")
        self.root.minsize(980, 640)
        self.root.configure(bg=P["bg"])

        self.algo_list = [
            "A* Search", "Backtracking", "Backtracking + Forward Chaining",
            "Brute Force", "Pure Forward Chaining",
            "Backward Chaining (SLD)", "SAT Solver",
        ]
        if not SAT_AVAILABLE:
            self.algo_list = [a for a in self.algo_list if a != "SAT Solver"]

        self.v_input   = tk.StringVar()
        self.v_algo    = tk.StringVar(value=self.algo_list[0])
        self.v_heur    = tk.StringVar(value="AC3")
        self.v_fc      = tk.BooleanVar(value=False)
        self.v_status  = tk.StringVar(value="—")
        self.v_time    = tk.StringVar(value="—")
        self.v_nodes   = tk.StringVar(value="—")
        self.v_note    = tk.StringVar(value="Select a puzzle and press Run")
        self.v_caption = tk.StringVar(value="")
        self.v_solving = tk.StringVar(value="")
        self.chart_controller = ChartReportController(
            root=self.root,
            palette=P,
            ui_font=UI,
            outputs_dir=OUTPUTS_DIR,
            run_log_file=RUN_LOG_FILE,
            note_setter=self.v_note.set,
        )

        self._board_data  = None
        self._given_cells = set()
        self._diff_cells  = set()   # cells that differ vs previous solve
        self._prev_sol    = None    # last solution grid for diff comparison
        self._prev_file   = None    # which file produced _prev_sol
        self._fc_enabled  = False
        self._busy        = False
        self._proc        = None
        self._queue       = None
        self._started_at  = 0.0
        self._active_payload = None
        self._solve_anim_job = None
        self._solve_anim_step = 0

        self._build()
        self._load_files()
        self._sync_astar()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        outer = tk.Frame(self.root, bg=P["bg"])
        outer.grid(sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(outer, bg=P["surf0"])
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)
        tk.Label(hdr, text="◈", bg=P["surf0"], fg=P["teal"],
                 font=(UI, 15)).grid(row=0, column=0, padx=(18,8), pady=13)
        tk.Label(hdr, text="Futoshiki Solver", bg=P["surf0"], fg=P["fg"],
                 font=(UI, 13, "bold")).grid(row=0, column=1, sticky="w")
        tk.Label(hdr, textvariable=self.v_caption, bg=P["surf0"], fg=P["fg_mid"],
                 font=(UI, 8)).grid(row=0, column=2, padx=(0,18), sticky="e")
        tk.Frame(outer, bg=P["teal"], height=1).grid(row=0, column=0, sticky="sew")

        # Body
        body = tk.Frame(outer, bg=P["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=12)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, minsize=268)
        body.rowconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        self._build_board(body)
        self._build_sidebar(body)

    def _build_board(self, parent):
        pnl = tk.Frame(parent, bg=P["surf0"],
                       highlightthickness=1, highlightbackground=P["border"])
        pnl.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        pnl.columnconfigure(0, weight=1)
        # Three distinct rows — chips | note | canvas — no overlap possible
        pnl.rowconfigure(0, weight=0)
        pnl.rowconfigure(1, weight=0)
        pnl.rowconfigure(2, weight=1)

        # Row 0 — stat chips
        chips = tk.Frame(pnl, bg=P["surf0"])
        chips.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        Chip(chips, "Status",     self.v_status, P["green"]).pack(side="left", padx=(0,24))
        Chip(chips, "Solve time", self.v_time,   P["teal"]).pack(side="left", padx=(0,24))
        Chip(chips, "Nodes",      self.v_nodes,  P["amber"]).pack(side="left")

        # Row 1 — hint / note
        tk.Label(pnl, textvariable=self.v_note, bg=P["surf0"], fg=P["fg_dim"],
                 font=(UI, 8), anchor="w").grid(
            row=1, column=0, sticky="ew", padx=18, pady=(0, 8))

        # Row 2 — canvas
        self.cv = tk.Canvas(pnl, bg=P["bg"], bd=0, highlightthickness=0)
        self.cv.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.cv.bind("<Configure>", lambda _: self._redraw())

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=P["surf0"],
                      highlightthickness=1, highlightbackground=P["border"])
        sb.grid(row=0, column=1, sticky="nsew")
        sb.columnconfigure(0, weight=1)

        def gap(row, h=8):
            tk.Frame(sb, bg=P["surf0"], height=h).grid(row=row, column=0)

        def rule(row):
            tk.Frame(sb, bg=P["border"], height=1).grid(
                row=row, column=0, sticky="ew", padx=16)

        def field_lbl(row, txt):
            tk.Label(sb, text=txt, bg=P["surf0"], fg=P["fg_mid"],
                     font=(UI, 8)).grid(row=row, column=0,
                                        sticky="w", padx=16, pady=(12, 3))

        r = 0
        gap(r); r += 1
        tk.Label(sb, text="Settings", bg=P["surf0"], fg=P["fg"],
                 font=(UI, 11, "bold")).grid(row=r, column=0, sticky="w", padx=16)
        r += 1; gap(r, 4); r += 1
        rule(r); r += 1

        field_lbl(r, "Input file"); r += 1
        self.dd_input = Dropdown(
            sb,
            [],
            self.v_input,
            on_change=self._on_input,
            max_height=170,
        )
        self.dd_input.grid(row=r, column=0, sticky="ew", padx=16)
        r += 1

        field_lbl(r, "Search method"); r += 1
        self.dd_algo = Dropdown(sb, self.algo_list, self.v_algo,
                                on_change=self._on_algo)
        self.dd_algo.grid(row=r, column=0, sticky="ew", padx=16)
        r += 1

        rule(r); r += 1

        field_lbl(r, "A* heuristic"); r += 1
        self.dd_heur = Dropdown(sb, ["AC3", "MBDT", "MRC"], self.v_heur)
        self.dd_heur.grid(row=r, column=0, sticky="ew", padx=16)
        r += 1

        gap(r, 10); r += 1

        # Toggle row
        tog = tk.Frame(sb, bg=P["surf0"])
        tog.grid(row=r, column=0, sticky="ew", padx=16); r += 1
        self._tog = tk.Canvas(tog, width=36, height=20, bg=P["surf0"],
                              bd=0, highlightthickness=0, cursor="hand2")
        self._tog.pack(side="left")
        self._tog.bind("<Button-1>", self._toggle_fc)
        self._fc_lbl = tk.Label(tog, text="Forward Chaining (MAC)",
                                bg=P["surf0"], fg=P["fg_mid"],
                                font=(UI, 8), cursor="hand2")
        self._fc_lbl.pack(side="left", padx=(8, 0))
        self._fc_lbl.bind("<Button-1>", self._toggle_fc)
        self._draw_toggle()

        gap(r, 6); r += 1
        rule(r); r += 1
        sb.rowconfigure(r, weight=1); r += 1   # spacer

        self.run_btn = RunButton(sb, text="Run Solver", command=self.run_selected)
        self.run_btn.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 16))
        r += 1

        self.chart_btn = RunButton(sb, text="Show Charts", command=self.show_charts)
        self.chart_btn.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 12))
        r += 1

        self.clear_btn = RunButton(sb, text="Clear Log + Output", command=self.clear_logs_and_outputs)
        self.clear_btn.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 12))
        r += 1

        self.solve_anim_lbl = tk.Label(
            sb,
            textvariable=self.v_solving,
            bg=P["surf0"],
            fg=P["teal"],
            font=(UI, 9, "bold"),
            anchor="center",
        )
        self.solve_anim_lbl.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 14))

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _draw_toggle(self):
        cv = self._tog; cv.delete("all")
        on = self.v_fc.get()
        rrect(cv, 1, 3, 35, 17, r=7,
              fill=P["teal"] if on else P["surf2"],
              outline=P["teal"] if on else P["border_hi"], width=1)
        kx = 19 if on else 7
        cv.create_oval(kx-5, 4, kx+5, 16,
                       fill=P["fg"] if on else P["fg_mid"], outline="")

    def _toggle_fc(self, _=None):
        if not self._fc_enabled: return
        self.v_fc.set(not self.v_fc.get()); self._draw_toggle()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_files(self):
        INPUTS_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(p.name for p in INPUTS_DIR.glob("*.txt"))
        self.dd_input._values = files
        if files:
            self.v_input.set(files[0]); self._preview()
        else:
            self.v_input.set("(no files found)")

    def _ensure_run_log_schema(self):
        if not RUN_LOG_FILE.exists():
            return

        try:
            with open(RUN_LOG_FILE, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_header = reader.fieldnames or []
                if existing_header == RUN_LOG_HEADER:
                    return
                existing_rows = list(reader)
        except Exception:
            return

        with open(RUN_LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=RUN_LOG_HEADER)
            writer.writeheader()
            for old_row in existing_rows:
                migrated = {key: old_row.get(key, "") for key in RUN_LOG_HEADER}
                if not migrated["peak_memory_mb"]:
                    migrated["peak_memory_mb"] = old_row.get("memory_mb", "")
                writer.writerow(migrated)

    def _append_run_log(self, *, input_file, size, algo, heur, fc, status,
                        elapsed, nodes, peak_memory_mb, output_file, note):
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_run_log_schema()

        if isinstance(peak_memory_mb, (int, float)):
            peak_mem_text = f"{peak_memory_mb:.4f}"
        elif peak_memory_mb in (None, ""):
            peak_mem_text = ""
        else:
            peak_mem_text = str(peak_memory_mb)

        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "input_file": input_file,
            "size": size,
            "algorithm": algo,
            "heuristic": heur,
            "fc_prune": "yes" if fc else "no",
            "status": status,
            "elapsed_sec": f"{elapsed:.4f}" if isinstance(elapsed, (int, float)) else str(elapsed),
            "nodes": str(nodes),
            "peak_memory_mb": peak_mem_text,
            "output_file": output_file,
            "note": str(note).replace("\n", " ").strip(),
        }

        need_header = (not RUN_LOG_FILE.exists()) or (RUN_LOG_FILE.stat().st_size == 0)
        with open(RUN_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=RUN_LOG_HEADER)
            if need_header:
                writer.writeheader()
            writer.writerow(row)
        self.chart_controller.on_log_data_changed()

    def _log_from_payload(self, status, elapsed, note):
        payload = self._active_payload or {}
        input_path = payload.get("path", "")
        input_file = Path(input_path).name if input_path else ""
        size = ""
        if input_path:
            try:
                size = load_env_from_file(input_path).n
            except Exception:
                size = ""

        self._append_run_log(
            input_file=input_file,
            size=size,
            algo=payload.get("algo", ""),
            heur=payload.get("heur", ""),
            fc=bool(payload.get("fc", False)),
            status=status,
            elapsed=elapsed,
            nodes="N/A",
            peak_memory_mb="",
            output_file="",
            note=note,
        )

    # ── Events ────────────────────────────────────────────────────────────────

    def _on_input(self):
        self.v_status.set("—"); self.v_time.set("—"); self.v_nodes.set("—")
        self.v_note.set("Puzzle loaded — press Run to solve")
        # Reset diff state when switching puzzles
        self._prev_sol   = None
        self._prev_file  = None
        self._diff_cells = set()
        self._preview()

    def _on_algo(self): self._sync_astar()

    def show_charts(self):
        self.chart_controller.show_charts()

    def clear_logs_and_outputs(self):
        self.chart_controller.clear_log_and_outputs()

    def _close_chart_window(self):
        self.chart_controller.close_window()

    def _set_busy(self, busy):
        self._busy = bool(busy)
        if busy:
            self.dd_input._close()
            self.dd_algo._close()
            self.dd_heur._close()
        self.dd_input.enable(not busy)
        self.dd_algo.enable(not busy)
        self.run_btn.enable(not busy)
        self.chart_btn.enable(not busy)
        self.clear_btn.enable(not busy)
        self._sync_astar()
        if busy:
            self._start_solving_animation()
        else:
            self._stop_solving_animation()

    def _start_solving_animation(self):
        self._stop_solving_animation()
        self._solve_anim_step = 0
        self._tick_solving_animation()

    def _tick_solving_animation(self):
        if not self._busy:
            return
        dots = "." * (self._solve_anim_step % 4)
        self.v_solving.set(f"Solving{dots}")
        self._solve_anim_step += 1
        self._solve_anim_job = self.root.after(300, self._tick_solving_animation)

    def _stop_solving_animation(self):
        if self._solve_anim_job is not None:
            try:
                self.root.after_cancel(self._solve_anim_job)
            except Exception:
                pass
            self._solve_anim_job = None
        self.v_solving.set("")

    def _sync_astar(self):
        on = self.v_algo.get() == "A* Search"
        self._fc_enabled = on and (not self._busy)
        self.dd_heur.enable(on and (not self._busy))
        self._fc_lbl.config(
            fg=P["fg_mid"] if self._fc_enabled else P["fg_dim"]
        )
        if not on:
            self.v_fc.set(False)
        self._draw_toggle()

    # ── Board rendering ───────────────────────────────────────────────────────

    def _set_board(self, grid, hc, vc, caption, given=None, diff=None):
        self._board_data  = {"grid": clone_grid(grid),
                             "hc": [r[:] for r in hc],
                             "vc": [r[:] for r in vc]}
        self._given_cells = given or set()
        self._diff_cells  = diff  or set()
        self.v_caption.set(caption)
        self._redraw()

    def _redraw(self):
        cv = self.cv; cv.delete("all")
        d = self._board_data
        if not d: return
        grid = d["grid"]; hc = d["hc"]; vc = d["vc"]; n = len(grid)
        if n == 0: return

        W = max(cv.winfo_width(), 1)
        H = max(cv.winfo_height(), 1)
        PAD = 22; GR = 0.28
        cell = min((W - 2*PAD) / (n + GR*(n-1)),
                   (H - 2*PAD) / (n + GR*(n-1)))
        cell = max(24.0, min(cell, 90.0))
        gap  = cell * GR
        rad  = max(5, int(cell * 0.11))
        ox   = (W - (n*cell + (n-1)*gap)) / 2
        oy   = (H - (n*cell + (n-1)*gap)) / 2

        val_fs = max(11, int(cell * 0.36))
        # Constraint symbol: based on gap size, hard-capped so it never floods the gap
        con_fs = max(7, min(11, int(gap * 0.46)))

        vf = (MONO, val_fs, "bold")
        cf = (UI,   con_fs, "bold")

        for r in range(n):
            for c in range(n):
                x1 = ox + c*(cell+gap); y1 = oy + r*(cell+gap)
                x2 = x1+cell;           y2 = y1+cell
                pre  = (r, c) in self._given_cells
                diff = (r, c) in self._diff_cells

                if pre:
                    fill, bdr, lw = P["cell_pre"], P["teal"], 1.5
                elif diff:
                    fill, bdr, lw = P["cell_diff"], P["diff_bdr"], 2.0
                else:
                    fill, bdr, lw = P["cell_bg"], P["cell_bdr"], 1

                rrect(cv, x1, y1, x2, y2, r=rad,
                      fill=fill, outline=bdr, width=lw)

                # Small diff indicator dot in top-right corner
                if diff:
                    dot_x = x2 - 6; dot_y = y1 + 6
                    cv.create_oval(dot_x-3, dot_y-3, dot_x+3, dot_y+3,
                                   fill=P["amber"], outline="")

                val = grid[r][c]
                if val == 0:
                    cv.create_text((x1+x2)/2, (y1+y2)/2,
                                   text="·", fill=P["fg_dim"], font=vf)
                else:
                    if pre:   clr = P["teal"]
                    elif diff: clr = P["amber"]
                    else:     clr = P["fg"]
                    cv.create_text((x1+x2)/2, (y1+y2)/2,
                                   text=str(val), fill=clr, font=vf)

                if c < n-1 and hc[r][c]:
                    cv.create_text(x2+gap/2, (y1+y2)/2,
                                   text=("<" if hc[r][c]==1 else ">"),
                                   fill=P["teal"], font=cf)

                if r < n-1 and vc[r][c]:
                    cv.create_text((x1+x2)/2, y2+gap/2,
                                   text=("∧" if vc[r][c]==1 else "∨"),
                                   fill=P["teal"], font=cf)

    def _preview(self):
        name = self.v_input.get().strip()
        if not name or name.startswith("("): return
        fp = INPUTS_DIR / name
        if not fp.exists(): return
        try:
            env   = load_env_from_file(fp)
            given = {(r,c) for r in range(env.n) for c in range(env.n)
                     if env.grid[r][c] != 0}
            self._set_board(env.grid, env.horiz_constraints,
                            env.vert_constraints,
                            f"{name}  ·  {env.n}×{env.n}",
                            given=given, diff=set())
        except Exception as ex:
            self.v_caption.set(f"Error: {ex}")

    # ── Solver dispatch ───────────────────────────────────────────────────────

    def run_selected(self):
        if self._busy:
            return

        name = self.v_input.get().strip()
        if not name or name.startswith("("):
            messagebox.showerror("No file", "Select an input file."); return
        fp = INPUTS_DIR / name
        if not fp.exists():
            messagebox.showerror("Missing", str(fp)); return

        # ── Flash: reset board to bare puzzle, show "solving…" state ──────
        self.v_status.set("…")
        self.v_time.set("…")
        self.v_nodes.set("…")
        self.v_note.set("Solver is running...")
        self._diff_cells = set()   # clear diff highlight during solve
        self._preview()            # show clean input board
        self.root.update_idletasks()

        payload = {
            "path": str(fp),
            "algo": self.v_algo.get(),
            "heur": self.v_heur.get(),
            "fc": bool(self.v_fc.get()),
        }
        self._start_worker(payload)

    def _start_worker(self, payload):
        self._cleanup_worker()
        self._active_payload = dict(payload)
        ctx = mp.get_context("spawn")
        self._queue = ctx.Queue()
        self._proc = ctx.Process(
            target=solver_worker,
            args=(payload, self._queue),
            daemon=True,
        )
        self._proc.start()
        self._started_at = time.perf_counter()
        self._set_busy(True)
        self.root.after(120, self._poll_worker)

    def _poll_worker(self):
        if self._proc is None:
            return

        elapsed = time.perf_counter() - self._started_at
        try:
            msg = self._queue.get_nowait() if self._queue is not None else None
        except std_queue.Empty:
            msg = None

        if msg is not None:
            self._cleanup_worker(join_process=True)
            self._set_busy(False)
            if msg.get("ok"):
                self._show(msg["result"])
            else:
                self.v_status.set("Error")
                self.v_time.set(f"{elapsed:.4f} s")
                self.v_nodes.set("N/A")
                self.v_note.set("Solver failed. Check error message.")
                self._log_from_payload("error", elapsed, msg.get("error", "Unknown solver error."))
                messagebox.showerror("Solver error", msg.get("error", "Unknown solver error."))
            self._active_payload = None
            return

        if not self._proc.is_alive():
            self._cleanup_worker(join_process=True)
            self._set_busy(False)
            self.v_status.set("Error")
            self.v_time.set(f"{elapsed:.4f} s")
            self.v_nodes.set("N/A")
            self.v_note.set("Solver process stopped unexpectedly.")
            self._log_from_payload("error", elapsed, "Solver process stopped unexpectedly.")
            messagebox.showerror("Solver error", "Solver process stopped unexpectedly.")
            self._active_payload = None
            return

        if elapsed >= SOLVER_TIMEOUT_SEC:
            self._terminate_worker()
            self._set_busy(False)
            self.v_status.set("Timeout")
            self.v_time.set(f"{SOLVER_TIMEOUT_SEC:.1f} s")
            self.v_nodes.set("N/A")
            self.v_note.set(f"Stopped after {SOLVER_TIMEOUT_SEC}s timeout.")
            self._log_from_payload("timeout", SOLVER_TIMEOUT_SEC, f"Stopped after {SOLVER_TIMEOUT_SEC}s timeout.")
            messagebox.showwarning("Timeout", f"Solver exceeded {SOLVER_TIMEOUT_SEC} seconds and was stopped.")
            self._active_payload = None
            return

        self.root.after(120, self._poll_worker)

    def _cleanup_worker(self, join_process=False):
        proc = self._proc
        q = self._queue
        self._proc = None
        self._queue = None

        if proc is not None and join_process:
            try:
                proc.join(timeout=0.2)
            except Exception:
                pass

        if q is not None:
            try:
                q.close()
                q.join_thread()
            except Exception:
                pass

    def _terminate_worker(self):
        if self._proc is not None and self._proc.is_alive():
            try:
                self._proc.terminate()
                self._proc.join(timeout=0.4)
            except Exception:
                pass
        self._cleanup_worker(join_process=False)

    def _solve(self, path):
        return solve_payload(path, self.v_algo.get(), self.v_heur.get(), self.v_fc.get())

    def _show(self, res):
        self.v_status.set("Solved" if res["solved"] else "Failed")
        self.v_time.set(f"{res['elapsed']:.4f} s")
        self.v_nodes.set(str(res["nodes"]))

        # ── Compute diff vs previous solve on the same file ───────────────
        new_sol  = res["sol"]
        new_file = res["file"]
        diff_cells = set()

        if (self._prev_sol is not None
                and self._prev_file == new_file
                and len(self._prev_sol) == len(new_sol)):
            n = len(new_sol)
            for r in range(n):
                for c in range(n):
                    if ((r, c) not in res["given"]
                            and new_sol[r][c] != self._prev_sol[r][c]):
                        diff_cells.add((r, c))

        # Build note text
        base_note = res["note"] or "Done."
        if diff_cells:
            diff_note = f"{len(diff_cells)} cell{'s' if len(diff_cells)>1 else ''} differ from previous run"
            note_text = f"{base_note}  ·  {diff_note}"
        elif self._prev_sol is not None and self._prev_file == new_file:
            note_text = f"{base_note}  ·  Same result as previous run"
        else:
            note_text = base_note

        output_file_name = ""
        if res["solved"]:
            try:
                output_path = next_output_file_path()
                output_path.write_text(
                    board_to_output_text(res["sol"], res["hc"], res["vc"]),
                    encoding="utf-8",
                )
                output_file_name = output_path.name
                note_text = f"{note_text}  ·  Saved: {output_file_name}"
            except Exception as ex:
                note_text = f"{note_text}  ·  Save failed: {ex}"

        peak_memory_mb = res.get("peak_memory_mb")
        if isinstance(peak_memory_mb, (int, float)):
            note_text = f"{note_text}  ·  Peak memory: {peak_memory_mb:.2f} MB"

        note_text = f"{note_text}  ·  Log: {RUN_LOG_FILE.name}"

        self.v_note.set(note_text)

        self._append_run_log(
            input_file=res["file"],
            size=res["n"],
            algo=res["algo"],
            heur=res["heur"],
            fc=bool(res["fc"]),
            status="solved" if res["solved"] else "failed",
            elapsed=res["elapsed"],
            nodes=res["nodes"],
            peak_memory_mb=res.get("peak_memory_mb", ""),
            output_file=output_file_name,
            note=note_text,
        )

        if res["solved"]:
            self.chart_controller.record_success(res)

        # Store this solution as the new "previous"
        self._prev_sol  = clone_grid(new_sol)
        self._prev_file = new_file
        self._active_payload = None

        tag = res["algo"]
        if tag == "A* Search":
            tag = f"A*  {res['heur']}" + (" + MAC" if res["fc"] else "")
        self._set_board(new_sol, res["hc"], res["vc"],
                        f"{res['file']}  ·  {res['n']}×{res['n']}  ·  {tag}",
                        given=res["given"], diff=diff_cells)


def main():
    mp.freeze_support()
    root = tk.Tk()
    app = MainApp(root)

    def _on_close():
        try:
            app._terminate_worker()
            app._close_chart_window()
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()