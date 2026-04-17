import csv
import importlib
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


class ChartReportController:
    def __init__(
        self,
        *,
        root,
        palette,
        ui_font,
        outputs_dir,
        run_log_file,
        note_setter=None,
    ):
        self.root = root
        self.P = palette
        self.UI = ui_font
        self.outputs_dir = Path(outputs_dir)
        self.run_log_file = Path(run_log_file)
        self.benchmark_file = self.outputs_dir / "benchmark-results.csv"
        self.C = {
            "fig_bg": "#ffffff",
            "ax_bg": "#ffffff",
            "text": "#0f172a",
            "muted": "#334155",
            "dim": "#64748b",
            "grid": "#dbe2ea",
            "spine": "#cbd5e1",
            "ui_bg": "#f8fafc",
            "control_bg": "#e2e8f0",
            "control_active": "#cbd5e1",
            "accent": "#0ea5e9",
            "accent_dark": "#0284c7",
            "danger": "#ef4444",
            "danger_dark": "#dc2626",
            "on_accent": "#ffffff",
        }
        self._set_note = note_setter or (lambda _: None)

        self._FigureCanvasTkAgg = None
        self._Figure = None
        self._mpl_ready = None

        self._chart_win = None
        self._chart_host = None
        self._chart_canvas = None
        self._chart_fig = None
        self._chart_source_var = None
        self._chart_subtitle_var = None

        self._latest_session_success = None

    # ---- public API ----

    def record_success(self, result):
        self._latest_session_success = {
            "file": result.get("file", ""),
            "algo": result.get("algo", ""),
            "heur": result.get("heur", ""),
            "fc": bool(result.get("fc", False)),
            "elapsed": result.get("elapsed", 0.0),
            "nodes": result.get("nodes", "N/A"),
            "memory_mb": result.get("peak_memory_mb", 0.0),
        }
        self.on_log_data_changed()

    def on_log_data_changed(self):
        if self._chart_win is not None and self._chart_win.winfo_exists():
            self._render_chart()

    def show_charts(self):
        if not self._ensure_matplotlib_ready():
            messagebox.showerror(
                "Missing dependency",
                "Chart feature requires matplotlib. Install it with: pip install matplotlib",
            )
            return

        if self._chart_win is None or not self._chart_win.winfo_exists():
            self._create_chart_window()
        else:
            self._chart_win.deiconify()
            self._chart_win.lift()
            try:
                self._chart_win.focus_force()
            except Exception:
                pass

        self._render_chart()

    def clear_log_and_outputs(self):
        if not messagebox.askyesno(
            "Clear data",
            "Delete solve-log.csv and all output-*.txt files?",
        ):
            return

        removed_log = False
        removed_outputs = 0
        errors = []

        try:
            if self.run_log_file.exists():
                self.run_log_file.unlink()
                removed_log = True
        except Exception as ex:
            errors.append(f"Could not delete {self.run_log_file.name}: {ex}")

        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        for fp in sorted(self.outputs_dir.glob("output-*.txt")):
            if not fp.is_file():
                continue
            try:
                fp.unlink()
                removed_outputs += 1
            except Exception as ex:
                errors.append(f"Could not delete {fp.name}: {ex}")

        self._latest_session_success = None

        if errors:
            messagebox.showerror("Clear failed", "\n".join(errors))
            return

        msg = f"Cleared log: {'yes' if removed_log else 'no'} | Output files removed: {removed_outputs}"
        self._set_note(msg)
        if self._chart_win is not None and self._chart_win.winfo_exists():
            self._render_chart()

    def close_window(self):
        if self._chart_canvas is not None:
            try:
                self._chart_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._chart_canvas = None

        if self._chart_fig is not None:
            try:
                self._chart_fig.clear()
            except Exception:
                pass
            self._chart_fig = None

        self._chart_host = None
        if self._chart_win is not None and self._chart_win.winfo_exists():
            try:
                self._chart_win.destroy()
            except Exception:
                pass
        self._chart_win = None

    # ---- internals ----

    def _ensure_matplotlib_ready(self):
        if self._mpl_ready is not None:
            return self._mpl_ready

        try:
            backend_tkagg = importlib.import_module("matplotlib.backends.backend_tkagg")
            figure_mod = importlib.import_module("matplotlib.figure")
            self._FigureCanvasTkAgg = backend_tkagg.FigureCanvasTkAgg
            self._Figure = figure_mod.Figure
            self._mpl_ready = True
        except Exception:
            self._FigureCanvasTkAgg = None
            self._Figure = None
            self._mpl_ready = False
        return self._mpl_ready

    @staticmethod
    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _short_label(label, max_len=18):
        text = str(label).strip()
        if not text:
            return "Unknown"

        compact_map = {
            "Backtracking + Forward Chaining": "BT + FC",
            "Pure Forward Chaining": "Pure FC",
            "Backward Chaining (SLD)": "SLD Backward",
        }
        text = compact_map.get(text, text)
        text = text.replace(" + ", "+")

        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _load_csv_rows(self, csv_path):
        if not csv_path.exists():
            return []

        rows = []
        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row:
                        rows.append(row)
        except Exception:
            return []
        return rows

    def _load_log_rows(self):
        return self._load_csv_rows(self.run_log_file)

    def _load_benchmark_rows(self):
        return self._load_csv_rows(self.benchmark_file)

    def _default_chart_source(self):
        benchmark_rows = self._load_benchmark_rows()
        if benchmark_rows:
            return "benchmark"
        return "solve-log"

    def _get_chart_source(self):
        if self._chart_source_var is None:
            return "solve-log"
        source = str(self._chart_source_var.get()).strip().lower()
        if source in {"solve-log", "benchmark"}:
            return source
        return "solve-log"

    def _set_chart_subtitle(self, text):
        if self._chart_subtitle_var is not None:
            self._chart_subtitle_var.set(str(text))

    def _metric_colors(self, count, *, base_color=None):
        if count <= 0:
            return []
        if base_color:
            return [base_color] * count

        palette = [
            "#2563eb",
            "#0f766e",
            "#d97706",
            "#dc2626",
            "#7c3aed",
            "#0891b2",
            "#4d7c0f",
            "#b45309",
        ]
        return [palette[idx % len(palette)] for idx in range(count)]

    def _plot_ranked_horizontal_bars(
        self,
        ax,
        *,
        series,
        title,
        x_label,
        empty_text,
        value_fmt,
        colors=None,
        min_x=1.0,
        fixed_xmax=None,
        label_max_len=24,
    ):
        ax.set_title(
            title,
            color=self.C["text"],
            fontsize=10,
            pad=8,
        )

        if not series:
            ax.text(
                0.5,
                0.5,
                empty_text,
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=self.C["dim"],
                fontsize=9,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            return

        labels = [self._short_label(name, max_len=label_max_len) for name, _ in series]
        values = [float(value) for _, value in series]
        y_positions = list(range(len(series)))
        bar_colors = colors if colors is not None else self._metric_colors(len(series))
        bar_height = 0.62 if len(series) <= 10 else 0.52
        label_font_size = 8 if len(series) <= 10 else 7

        bars = ax.barh(y_positions, values, color=bar_colors, height=bar_height)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, color=self.C["text"], fontsize=label_font_size)
        ax.invert_yaxis()
        ax.set_xlabel(x_label, color=self.C["muted"], fontsize=8)
        ax.tick_params(axis="y", pad=10, colors=self.C["muted"])
        ax.set_axisbelow(True)

        max_value = max(values) if values else 0.0
        if fixed_xmax is not None:
            base_x_max = max(float(fixed_xmax), 1e-9)
        else:
            base_x_max = max(float(min_x), max_value * 1.08)
        label_pad = max(base_x_max * 0.03, 0.02)
        x_max = base_x_max + (label_pad * 7.0)
        ax.set_xlim(0, x_max)
        ax.margins(y=0.08)

        for idx, (bar, value) in enumerate(zip(bars, values)):
            x_text = min(x_max * 0.992, bar.get_width() + label_pad)
            ax.text(
                x_text,
                bar.get_y() + (bar.get_height() / 2),
                value_fmt(value, idx),
                ha="left",
                va="center",
                color=self.C["text"],
                fontsize=8,
                clip_on=False,
            )

    def _format_algo_tag(self, latest):
        algo = str(latest.get("algo", ""))
        if algo == "A* Search":
            suffix = " + MAC" if latest.get("fc") else ""
            return f"A* {latest.get('heur', '')}{suffix}".strip()
        return algo or "N/A"

    def _format_algo_from_log_row(self, row):
        algo = str(row.get("algorithm", "")).strip() or "Unknown"
        if algo != "A* Search":
            return algo

        heur = str(row.get("heuristic", "")).strip()
        fc_flag = str(row.get("fc_prune", "")).strip().lower()
        has_mac = fc_flag in {"yes", "true", "1"}
        suffix = " + MAC" if has_mac else ""
        if heur:
            return f"A* {heur}{suffix}".strip()
        return f"A*{suffix}".strip()

    def _create_report_figure(self, log_rows):
        fig = self._Figure(figsize=(15.2, 7.0), dpi=100, facecolor=self.C["fig_bg"])
        ax_latest, ax_outputs, ax_memory = fig.subplots(1, 3)

        for ax in (ax_latest, ax_outputs, ax_memory):
            ax.set_facecolor(self.C["ax_bg"])
            ax.tick_params(colors=self.C["muted"], labelsize=8)
            for side in ("bottom", "top", "left", "right"):
                ax.spines[side].set_color(self.C["spine"])
            ax.grid(color=self.C["grid"], alpha=0.65, linewidth=0.7)

        # Left chart: latest successful solve in this app session
        ax_latest.set_title(
            "Latest Successful Run (This Session)",
            color=self.C["text"],
            fontsize=10,
            pad=8,
        )

        latest = self._latest_session_success
        if latest is not None:
            elapsed = self._to_float(latest.get("elapsed")) or 0.0
            mem_mb = self._to_float(latest.get("memory_mb")) or 0.0
            labels = ["Elapsed (s)", "Peak Mem (MB)"]
            values = [elapsed, mem_mb]
            bars = ax_latest.bar(labels, values, color=[self.C["accent"], "#f59e0b"], width=0.56)
            max_y = max(1.0, max(values) * 1.35)
            ax_latest.set_ylim(0, max_y)
            ax_latest.set_ylabel("Value", color=self.C["muted"], fontsize=8)

            for index, bar in enumerate(bars):
                value_text = f"{values[index]:.4f}" if index == 0 else f"{values[index]:.2f}"
                ax_latest.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + (max_y * 0.02),
                    value_text,
                    ha="center",
                    va="bottom",
                    color=self.C["text"],
                    fontsize=8,
                )

            info = [
                f"Algorithm: {self._format_algo_tag(latest)}",
                f"Input: {latest.get('file', '')}",
                f"Nodes: {latest.get('nodes', 'N/A')}",
            ]
            ax_latest.text(
                0.03,
                0.97,
                "\n".join(info),
                transform=ax_latest.transAxes,
                ha="left",
                va="top",
                color=self.C["text"],
                fontsize=8,
                bbox={"facecolor": self.C["ax_bg"], "edgecolor": self.C["spine"], "boxstyle": "round,pad=0.25"},
            )
        else:
            ax_latest.text(
                0.5,
                0.5,
                "No successful run yet in this session",
                transform=ax_latest.transAxes,
                ha="center",
                va="center",
                color=self.C["dim"],
                fontsize=9,
            )
            ax_latest.set_xticks([])
            ax_latest.set_yticks([])

        # Middle chart: output files grouped by algorithm variant
        output_counts = {}
        for row in log_rows:
            output_file = str(row.get("output_file", "")).strip()
            if not output_file:
                continue
            algo = self._format_algo_from_log_row(row)
            output_counts[algo] = output_counts.get(algo, 0) + 1

        output_series = [
            (name, float(count))
            for name, count in sorted(output_counts.items(), key=lambda item: item[1], reverse=True)
        ]
        self._plot_ranked_horizontal_bars(
            ax_outputs,
            series=output_series,
            title="Output Files In Log",
            x_label="Output files",
            empty_text="No output_file entries in solve-log.csv",
            value_fmt=lambda value, _idx: str(int(round(value))),
            colors=self._metric_colors(len(output_series)),
            min_x=1.0,
            label_max_len=14,
        )

        # Third chart: average peak memory from solve-log.csv grouped by algorithm
        memory_by_algo = {}
        for row in log_rows:
            mem_value = self._to_float(row.get("peak_memory_mb"))
            if mem_value is None:
                continue
            algo_name = self._format_algo_from_log_row(row)
            memory_by_algo.setdefault(algo_name, []).append(mem_value)

        memory_series = [
            (name, (sum(values) / len(values)))
            for name, values in sorted(
                memory_by_algo.items(),
                key=lambda item: (sum(item[1]) / len(item[1])) if item[1] else 0.0,
                reverse=True,
            )
            if values
        ]
        self._plot_ranked_horizontal_bars(
            ax_memory,
            series=memory_series,
            title="Average Peak Memory In Log",
            x_label="MB",
            empty_text="No peak_memory_mb entries in solve-log.csv",
            value_fmt=lambda value, _idx: f"{value:.2f}",
            colors=self._metric_colors(len(memory_series)),
            min_x=1.0,
            label_max_len=14,
        )

        memory_rows = sum(1 for row in log_rows if self._to_float(row.get("peak_memory_mb")) is not None)

        fig.suptitle(
            f"Futoshiki Chart Report | Log rows: {len(log_rows)} | Memory rows: {memory_rows}",
            color=self.C["text"],
            fontsize=12,
            fontweight="bold",
            y=0.985,
        )
        fig.tight_layout(rect=[0.01, 0.05, 0.99, 0.94], w_pad=3.0)
        return fig

    def _create_benchmark_figure(self, bench_rows):
        fig = self._Figure(figsize=(15.2, 7.0), dpi=100, facecolor=self.C["fig_bg"])
        (ax_elapsed, ax_success), (ax_memory, ax_nodes) = fig.subplots(2, 2)

        for ax in (ax_elapsed, ax_success, ax_memory, ax_nodes):
            ax.set_facecolor(self.C["ax_bg"])
            ax.tick_params(colors=self.C["muted"], labelsize=8)
            for side in ("bottom", "top", "left", "right"):
                ax.spines[side].set_color(self.C["spine"])
            ax.grid(color=self.C["grid"], alpha=0.65, linewidth=0.7)

        by_variant = {}
        status_totals = {}

        for row in bench_rows:
            variant = str(row.get("algorithm_variant", "")).strip()
            if not variant:
                variant = self._format_algo_from_log_row(row)
            by_variant.setdefault(variant, []).append(row)

            status = str(row.get("status", "unknown")).strip().lower() or "unknown"
            status_totals[status] = status_totals.get(status, 0) + 1

        # Left chart: average elapsed time by algorithm variant
        ax_elapsed.set_title(
            "Benchmark: Avg Elapsed Time",
            color=self.C["text"],
            fontsize=10,
            pad=8,
        )

        elapsed_items = []
        for variant, rows in by_variant.items():
            elapsed_values = [
                self._to_float(row.get("elapsed_sec"))
                for row in rows
            ]
            elapsed_values = [value for value in elapsed_values if value is not None]
            if elapsed_values:
                elapsed_items.append((variant, sum(elapsed_values) / len(elapsed_values), len(elapsed_values)))

        elapsed_series = [
            (name, avg)
            for name, avg, _count in sorted(elapsed_items, key=lambda item: item[1])
        ]
        self._plot_ranked_horizontal_bars(
            ax_elapsed,
            series=elapsed_series,
            title="Benchmark: Avg Elapsed Time",
            x_label="Seconds",
            empty_text="No elapsed_sec values in benchmark-results.csv",
            value_fmt=lambda value, _idx: f"{value:.4f}",
            colors=self._metric_colors(len(elapsed_series), base_color=self.C["accent"]),
            min_x=0.01,
            label_max_len=14,
        )

        # Middle chart: solved rate by algorithm variant
        ax_success.set_title(
            "Benchmark: Solved Rate",
            color=self.C["text"],
            fontsize=10,
            pad=8,
        )

        success_items = []
        for variant, rows in by_variant.items():
            total = len(rows)
            solved = sum(1 for row in rows if str(row.get("status", "")).strip().lower() == "solved")
            if total > 0:
                rate = (solved * 100.0) / total
                success_items.append((variant, rate, solved, total))

        success_items.sort(key=lambda item: item[1], reverse=True)
        success_series = [(name, rate) for name, rate, _solved, _total in success_items]
        success_colors = [
            "#16a34a" if rate >= 99.999 else ("#d97706" if rate >= 50.0 else "#dc2626")
            for _name, rate, _solved, _total in success_items
        ]
        self._plot_ranked_horizontal_bars(
            ax_success,
            series=success_series,
            title="Benchmark: Solved Rate",
            x_label="Solved %",
            empty_text="No rows in benchmark-results.csv",
            value_fmt=lambda value, idx: (
                f"{value:.1f}% ({success_items[idx][2]}/{success_items[idx][3]})"
            ),
            colors=success_colors,
            min_x=100.0,
            fixed_xmax=105.0,
            label_max_len=14,
        )

        # Right chart: average peak memory by algorithm variant
        ax_memory.set_title(
            "Benchmark: Avg Peak Memory",
            color=self.C["text"],
            fontsize=10,
            pad=8,
        )

        memory_items = []
        for variant, rows in by_variant.items():
            mem_values = [
                self._to_float(row.get("peak_memory_mb"))
                for row in rows
            ]
            mem_values = [value for value in mem_values if value is not None]
            if mem_values:
                memory_items.append((variant, sum(mem_values) / len(mem_values), len(mem_values)))

        memory_series = [
            (name, avg)
            for name, avg, _count in sorted(memory_items, key=lambda item: item[1])
        ]
        self._plot_ranked_horizontal_bars(
            ax_memory,
            series=memory_series,
            title="Benchmark: Avg Peak Memory",
            x_label="MB",
            empty_text="No peak_memory_mb values in benchmark-results.csv",
            value_fmt=lambda value, _idx: f"{value:.2f}",
            colors=self._metric_colors(len(memory_series), base_color="#16a34a"),
            min_x=0.1,
            label_max_len=14,
        )

        # Fourth chart: average nodes expanded by algorithm variant
        nodes_items = []
        for variant, rows in by_variant.items():
            node_values = [
                self._to_float(row.get("nodes"))
                for row in rows
            ]
            node_values = [value for value in node_values if value is not None]
            if node_values:
                nodes_items.append((variant, sum(node_values) / len(node_values), len(node_values)))

        nodes_series = [
            (name, avg)
            for name, avg, _count in sorted(nodes_items, key=lambda item: item[1])
        ]
        self._plot_ranked_horizontal_bars(
            ax_nodes,
            series=nodes_series,
            title="Benchmark: Avg Nodes Expanded",
            x_label="Nodes",
            empty_text="No 'nodes' values in benchmark-results.csv",
            value_fmt=lambda value, _idx: f"{int(round(value)):,}",
            colors=self._metric_colors(len(nodes_series), base_color="#7c3aed"),
            min_x=1.0,
            label_max_len=14,
        )

        status_order = ["solved", "failed", "timeout", "error", "unknown"]
        status_parts = []
        for key in status_order:
            count = status_totals.get(key, 0)
            if count:
                status_parts.append(f"{key}: {count}")
        if not status_parts:
            status_parts.append("No status data")

        fig.suptitle(
            f"Futoshiki Benchmark Report | Rows: {len(bench_rows)} | " + " | ".join(status_parts),
            color=self.C["text"],
            fontsize=12,
            fontweight="bold",
            y=0.985,
        )
        fig.tight_layout(rect=[0.01, 0.05, 0.99, 0.94], w_pad=3.0, h_pad=4.0)
        return fig

    def _render_chart(self):
        if self._chart_host is None or not self._chart_host.winfo_exists():
            return

        source = self._get_chart_source()

        if self._chart_canvas is not None:
            try:
                self._chart_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._chart_canvas = None

        if self._chart_fig is not None:
            try:
                self._chart_fig.clear()
            except Exception:
                pass
            self._chart_fig = None

        if source == "benchmark":
            bench_rows = self._load_benchmark_rows()
            self._set_chart_subtitle(
                f"Source: {self.benchmark_file.name} | Rows: {len(bench_rows)}"
            )
            self._chart_fig = self._create_benchmark_figure(bench_rows)
        else:
            log_rows = self._load_log_rows()
            self._set_chart_subtitle(
                f"Source: {self.run_log_file.name} | Rows: {len(log_rows)}"
            )
            self._chart_fig = self._create_report_figure(log_rows)

        self._chart_canvas = self._FigureCanvasTkAgg(self._chart_fig, master=self._chart_host)
        self._chart_canvas.draw()
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _download_chart_image(self):
        if self._chart_fig is None:
            messagebox.showinfo("No chart", "Open chart view first.")
            return

        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        source = self._get_chart_source()
        prefix = "benchmark-report" if source == "benchmark" else "report"
        default_name = f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        save_path = filedialog.asksaveasfilename(
            title="Save chart image",
            initialdir=str(self.outputs_dir),
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
        )
        if not save_path:
            return

        try:
            self._chart_fig.savefig(
                save_path,
                dpi=220,
                bbox_inches="tight",
                facecolor=self._chart_fig.get_facecolor(),
            )
            self._set_note(f"Chart image saved: {Path(save_path).name}")
        except Exception as ex:
            messagebox.showerror("Save failed", f"Could not save image.\n{ex}")

    def _export_chart_data(self):
        """Dispatches to the correct summary export method based on the current data source."""
        source = self._get_chart_source()
        if source == "benchmark":
            self._export_benchmark_summary()
        elif source == "solve-log":
            self._export_log_summary()
        else:
            messagebox.showinfo("No Data Source", "Please select a data source first.")

    def _export_benchmark_summary(self):
        """Aggregates and exports benchmark chart data to a CSV file."""
        bench_rows = self._load_benchmark_rows()
        if not bench_rows:
            messagebox.showinfo("No Data", f"'{self.benchmark_file.name}' is empty.")
            return

        by_variant = {}
        for row in bench_rows:
            variant = str(row.get("algorithm_variant", "")).strip() or self._format_algo_from_log_row(row)
            by_variant.setdefault(variant, []).append(row)

        elapsed_map, memory_map, nodes_map, success_map = {}, {}, {}, {}
        for variant, rows in by_variant.items():
            elapsed_vals = [v for r in rows if (v := self._to_float(r.get("elapsed_sec"))) is not None]
            if elapsed_vals: elapsed_map[variant] = sum(elapsed_vals) / len(elapsed_vals)

            mem_vals = [v for r in rows if (v := self._to_float(r.get("peak_memory_mb"))) is not None]
            if mem_vals: memory_map[variant] = sum(mem_vals) / len(mem_vals)

            node_vals = [v for r in rows if (v := self._to_float(r.get("nodes"))) is not None]
            if node_vals: nodes_map[variant] = sum(node_vals) / len(node_vals)

            total = len(rows)
            if total > 0:
                solved = sum(1 for r in rows if str(r.get("status", "")).strip().lower() == "solved")
                success_map[variant] = {"rate": (solved * 100.0) / total, "solved": solved, "total": total}

        header = ["algorithm_variant", "avg_elapsed_sec", "solved_rate_percent", "solved_count", "total_count", "avg_peak_memory_mb", "avg_nodes_expanded"]
        output_rows = []
        for variant in sorted(by_variant.keys()):
            s_info = success_map.get(variant, {})
            output_rows.append({
                "algorithm_variant": variant,
                "avg_elapsed_sec": f"{elapsed_map.get(variant, 0.0):.6f}",
                "solved_rate_percent": f"{s_info.get('rate', 0.0):.2f}",
                "solved_count": s_info.get('solved', 0),
                "total_count": s_info.get('total', 0),
                "avg_peak_memory_mb": f"{memory_map.get(variant, 0.0):.4f}",
                "avg_nodes_expanded": f"{nodes_map.get(variant, 0.0):.1f}",
            })

        default_name = f"benchmark-chart-summary-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        self._save_summary_csv("Save Benchmark Chart Summary", default_name, header, output_rows)

    def _export_log_summary(self):
        """Aggregates and exports solve-log chart data to a CSV file."""
        log_rows = self._load_log_rows()
        if not log_rows:
            messagebox.showinfo("No Data", f"'{self.run_log_file.name}' is empty.")
            return

        output_counts = {}
        memory_by_algo = {}
        for row in log_rows:
            algo = self._format_algo_from_log_row(row)
            if str(row.get("output_file", "")).strip():
                output_counts[algo] = output_counts.get(algo, 0) + 1
            if (mem_value := self._to_float(row.get("peak_memory_mb"))) is not None:
                memory_by_algo.setdefault(algo, []).append(mem_value)
        
        avg_memory_map = {name: sum(values) / len(values) for name, values in memory_by_algo.items() if values}

        header = ["algorithm", "output_file_count", "avg_peak_memory_mb"]
        all_algos = sorted(set(output_counts.keys()) | set(avg_memory_map.keys()))
        output_rows = [{"algorithm": algo, "output_file_count": output_counts.get(algo, 0), "avg_peak_memory_mb": f"{avg_memory_map.get(algo, 0.0):.4f}"} for algo in all_algos]

        default_name = f"log-chart-summary-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        self._save_summary_csv("Save Solve Log Chart Summary", default_name, header, output_rows)

    def _save_summary_csv(self, title, default_name, header, rows):
        """Handles the file dialog and writing of summary data to a CSV."""
        save_path = filedialog.asksaveasfilename(title=title, initialdir=str(self.outputs_dir), initialfile=default_name, defaultextension=".csv", filetypes=[("CSV file", "*.csv"), ("All files", "*.*")])
        if not save_path:
            return
        try:
            with open(save_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                writer.writerows(rows)
            self._set_note(f"Chart data saved: {Path(save_path).name}")
        except Exception as ex:
            messagebox.showerror("Save failed", f"Could not save CSV file.\n{ex}")

    def _create_chart_window(self):
        win = tk.Toplevel(self.root, bg=self.C["ui_bg"])
        win.title("Futoshiki Charts")
        win.minsize(900, 620)
        win.geometry("1060x700")
        win.columnconfigure(0, weight=1)
        win.rowconfigure(1, weight=1)

        top = tk.Frame(win, bg=self.C["ui_bg"])
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=0)

        self._chart_subtitle_var = tk.StringVar(
            value="Latest success + output counts + memory profile"
        )

        tk.Label(
            top,
            textvariable=self._chart_subtitle_var,
            bg=self.C["ui_bg"],
            fg=self.C["text"],
            font=(self.UI, 10, "bold"),
        ).grid(row=0, column=0, sticky="w")

        source_wrap = tk.Frame(top, bg=self.C["ui_bg"])
        source_wrap.grid(row=1, column=0, sticky="w", pady=(8, 0))

        tk.Label(
            source_wrap,
            text="Data source:",
            bg=self.C["ui_bg"],
            fg=self.C["muted"],
            font=(self.UI, 8),
        ).pack(side="left", padx=(0, 8))

        self._chart_source_var = tk.StringVar(value=self._default_chart_source())

        for text, value in (("Solve Log", "solve-log"), ("Benchmark Results", "benchmark")):
            tk.Radiobutton(
                source_wrap,
                text=text,
                variable=self._chart_source_var,
                value=value,
                command=self._render_chart,
                indicatoron=False,
                bg=self.C["control_bg"],
                fg=self.C["text"],
                selectcolor=self.C["ui_bg"],
                activebackground=self.C["control_active"],
                activeforeground=self.C["text"],
                bd=0,
                padx=10,
                pady=4,
                font=(self.UI, 8),
                cursor="hand2",
            ).pack(side="left", padx=(0, 6))

        buttons = tk.Frame(top, bg=self.C["ui_bg"])
        buttons.grid(row=0, column=1, rowspan=2, sticky="e")

        tk.Button(
            buttons,
            text="Refresh",
            command=self._render_chart,
            bg=self.C["control_bg"],
            fg=self.C["text"],
            activebackground=self.C["control_active"],
            activeforeground=self.C["text"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons,
            text="Download PNG",
            command=self._download_chart_image,
            bg=self.C["accent"],
            fg=self.C["on_accent"],
            activebackground=self.C["accent_dark"],
            activeforeground=self.C["on_accent"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons,
            text="Export CSV",
            command=self._export_chart_data,
            bg=self.C["control_bg"],
            fg=self.C["text"],
            activebackground=self.C["control_active"],
            activeforeground=self.C["text"],
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons,
            text="Clear Log + Output",
            command=self.clear_log_and_outputs,
            bg=self.C["danger"],
            fg="#ffffff",
            activebackground=self.C["danger_dark"],
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
        ).pack(side="left")

        host = tk.Frame(
            win,
            bg=self.C["ui_bg"],
            highlightthickness=1,
            highlightbackground=self.C["spine"],
        )
        host.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        host.columnconfigure(0, weight=1)
        host.rowconfigure(0, weight=1)

        self._chart_win = win
        self._chart_host = host
        self._chart_canvas = None
        self._chart_fig = None
        win.protocol("WM_DELETE_WINDOW", self.close_window)
