"""Tkinter board, live statistics and a run results screen."""

import csv
import json
import time
from tkinter import filedialog, messagebox

from environment import ACTIONS, DIRECTIONS
from ui import (BG, BLUE, BOARD, GREEN, LINE, MUTED, PANEL, RED, TEXT,
                button, label, rounded, tk, trend, window)


class Display:
    def __init__(self, size, speed=8, step_by_step=False):
        self.root = window("Learn2Slither | Live run")
        self.root.resizable(False, False)
        available = max(240, min(600, self.root.winfo_screenheight() - 260))
        self.cell = max(6, min(52, available // size))
        self.margin = 14
        self.board_width = self.cell * size + 28
        self.speed = speed
        self.step_by_step = step_by_step
        self.paused = False
        self.advance = False
        self.save_requested = False
        self.closed = False
        self.show_vision = False
        self.return_to_menu = False
        self.history = []
        self.q_values = [0.0] * 4
        self.last_action = "-"
        self.last_board = None
        self.last_context = None
        self.message = ""
        self.container = tk.Frame(self.root, bg=BG, padx=20, pady=16)
        self.container.pack()
        top = tk.Frame(self.container, bg=BG)
        top.pack(fill="x", pady=(0, 14))
        label(top, "Learn2Slither", 23).pack(side="left")
        self.mode = label(top, "", 10, GREEN)
        self.mode.pack(side="right")
        body = tk.Frame(self.container, bg=BG)
        body.pack()
        self.canvas = tk.Canvas(
            body, width=self.board_width, height=self.board_width,
            bg=BOARD, highlightthickness=1, highlightbackground=LINE)
        self.canvas.pack(side="left", anchor="n")
        sidebar = tk.Frame(body, bg=BG, width=260)
        sidebar.pack(side="left", padx=(20, 0), fill="y")
        label(sidebar, "LIVE TELEMETRY", 10, GREEN).pack(anchor="w")
        self.score = label(sidebar, "03", 42, TEXT)
        self.score.pack(anchor="w", pady=(4, 0))
        label(sidebar, "CURRENT LENGTH", 9, MUTED).pack(anchor="w")
        self.stats = label(sidebar, "", 11, MUTED, justify="left")
        self.stats.pack(anchor="w", pady=12)
        self.goals = label(sidebar, "", 10, GREEN, justify="left")
        self.goals.pack(anchor="w", pady=(0, 12))
        label(sidebar, "Q-VALUES / CURRENT VISION", 9,
              MUTED).pack(anchor="w")
        self.q_canvas = tk.Canvas(sidebar, width=250, height=105, bg=BG,
                                  highlightthickness=0)
        self.q_canvas.pack(pady=(4, 12))
        label(sidebar, "FINAL LENGTH / LAST 100 GAMES", 9,
              MUTED).pack(anchor="w")
        self.chart = tk.Canvas(sidebar, width=250, height=100, bg=BG,
                               highlightthickness=0)
        self.chart.pack(pady=(4, 0))
        trend(self.chart, [], 250, 100)
        self.status = label(self.container, "", 10, MUTED, anchor="w")
        self.status.pack(fill="x", pady=(10, 8))
        controls = tk.Frame(self.container, bg=BG)
        controls.pack(fill="x")
        self.pause_button = button(controls, "Pause", self.toggle_pause)
        self.pause_button.pack(side="left", padx=(0, 6))
        button(controls, "Next", self.next_step).pack(side="left", padx=6)
        button(controls, "Save", self.request_save).pack(side="left", padx=6)
        self.vision_button = button(controls, "Vision: off",
                                    self.toggle_vision)
        self.vision_button.pack(side="left", padx=6)
        self.speed_value = tk.IntVar(value=speed)
        tk.Scale(controls, from_=1, to=120, orient="horizontal",
                 variable=self.speed_value, command=self.set_speed,
                 label="Moves / second", bg=BG, fg=MUTED, troughcolor=LINE,
                 highlightthickness=0, length=180).pack(side="right")
        label(self.container, "SPACE pause / step   ·   N next   ·   "
              "V vision   ·   S save   ·   +/- speed   ·   ESC quit",
              9, MUTED).pack(anchor="w", pady=(10, 0))
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Key>", self.key)
        self.refresh_controls()

    def next_step(self):
        self.advance = True

    def request_save(self):
        self.save_requested = True

    def set_speed(self, value):
        self.speed = int(float(value))

    def toggle_pause(self):
        if self.step_by_step:
            self.advance = True
        else:
            self.paused = not self.paused
        self.refresh_controls()

    def refresh_controls(self):
        text = "Step mode" if self.step_by_step else (
            "Resume" if self.paused else "Pause")
        self.pause_button.config(text=text)

    def toggle_vision(self):
        self.show_vision = not self.show_vision
        self.vision_button.config(
            text="Vision: on" if self.show_vision else "Vision: off")
        if self.last_board is not None:
            self.draw(self.last_board, *self.last_context)

    def key(self, event):
        key = event.keysym.lower()
        if key == "escape":
            self.close()
        elif key == "space":
            self.toggle_pause()
        elif key == "n":
            self.next_step()
        elif key in ("plus", "equal", "kp_add"):
            self.speed_value.set(min(120, self.speed + 2))
            self.speed = self.speed_value.get()
        elif key in ("minus", "kp_subtract"):
            self.speed_value.set(max(1, self.speed - 2))
            self.speed = self.speed_value.get()
        elif key == "s":
            self.request_save()
        elif key == "v":
            self.toggle_vision()

    def bounds(self, cell, inset=0):
        x, y = cell
        left = self.margin + x * self.cell
        top = self.margin + y * self.cell
        return (left + inset, top + inset,
                left + self.cell - inset, top + self.cell - inset)

    def apple(self, cell, color):
        inset = max(1, self.cell * 0.22)
        x1, y1, x2, y2 = self.bounds(cell, inset)
        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="")
        if self.cell >= 18:
            self.canvas.create_line((x1 + x2) / 2, y1 + 2,
                                    (x1 + x2) / 2 + 3, y1 - 4,
                                    fill=GREEN, width=2)
            self.canvas.create_oval(x1 + 3, y1 + 3, x1 + 6, y1 + 6,
                                    fill=TEXT, outline="")

    def snake(self, board):
        for index, cell in enumerate(reversed(board.snake)):
            color = BLUE if index == len(board.snake) - 1 else "#438b9f"
            rounded(self.canvas, *self.bounds(cell, max(1, self.cell * 0.08)),
                    max(2, self.cell * 0.22), color)
        if not board.snake or self.cell < 12:
            return
        head_x, head_y = board.snake[0]
        direction = (0, -1)
        if len(board.snake) > 1:
            neck_x, neck_y = board.snake[1]
            direction = (head_x - neck_x, head_y - neck_y)
        elif self.last_action in ACTIONS:
            direction = DIRECTIONS[ACTIONS.index(self.last_action)]
        dx, dy = direction
        cx = self.margin + (head_x + 0.5) * self.cell
        cy = self.margin + (head_y + 0.5) * self.cell
        radius = max(1.5, self.cell * 0.055)
        for side in (-1, 1):
            x = cx + (dx * 0.19 - dy * side * 0.2) * self.cell
            y = cy + (dy * 0.19 + dx * side * 0.2) * self.cell
            self.canvas.create_oval(x - radius, y - radius,
                                    x + radius, y + radius,
                                    fill=BG, outline="")

    def draw(self, board, episode, epsilon, learning, action=None):
        self.last_board = board
        self.last_context = (episode, epsilon, learning)
        if action is not None:
            self.last_action = action
        self.canvas.delete("all")
        head = board.snake[0] if board.snake else None
        for y in range(board.size):
            for x in range(board.size):
                visible = head and (x == head[0] or y == head[1])
                color = "#203a43" if self.show_vision and visible else (
                    "#192b36" if (x + y) % 2 == 0 else "#172731")
                rounded(self.canvas, *self.bounds((x, y), 1),
                        min(4, self.cell / 8), color)
        for cell in board.green:
            self.apple(cell, GREEN)
        for cell in board.red:
            self.apple(cell, RED)
        self.snake(board)
        self.mode.config(text=("LEARNING" if learning else "EVALUATION")
                         + f"  /  {board.size} × {board.size}")
        self.score.config(text=f"{len(board.snake):02d}")
        self.stats.config(text=(
            f"Game            {episode}\n"
            f"Steps           {board.steps}\n"
            f"Peak length     {board.max_length}\n"
            f"Apples          +{board.green_eaten} / -{board.red_eaten}\n"
            f"Epsilon         {epsilon:.3f}"
        ))
        completed = "  ".join(str(goal) for goal in (10, 15, 20, 25, 30, 35)
                              if len(board.snake) >= goal)
        self.goals.config(text="LENGTH GOALS  " + (completed or "Next: 10"))
        self.status.config(text=(
            f"{board.reason or 'Running'}   /   Action {self.last_action}"
            f"   /   {self.message}"
        ))
        self.draw_q()

    def draw_q(self):
        self.q_canvas.delete("all")
        scale = max(1, max(abs(value) for value in self.q_values))
        best = max(self.q_values)
        for index, (action, value) in enumerate(zip(ACTIONS, self.q_values)):
            y = index * 25 + 12
            color = GREEN if value == best else BLUE
            self.q_canvas.create_text(0, y, text=action, anchor="w",
                                      fill=MUTED, font=("DejaVu Sans", 9))
            self.q_canvas.create_line(120, y - 8, 120, y + 8, fill=LINE)
            end = 120 + value / scale * 66
            self.q_canvas.create_rectangle(min(120, end), y - 5,
                                           max(120, end), y + 5,
                                           fill=color, outline="")
            self.q_canvas.create_text(245, y, text=f"{value:.1f}", anchor="e",
                                      fill=TEXT, font=("DejaVu Sans", 9))

    def record(self, row):
        self.history.append(row)
        trend(self.chart, [r["length"] for r in self.history], 250, 100)

    def wait(self):
        start = time.monotonic()
        while not self.closed:
            self.root.update()
            if self.closed:
                return False
            if self.save_requested:
                return True
            if self.advance:
                self.advance = False
                return True
            if (not self.step_by_step and not self.paused
                    and time.monotonic() - start >= 1 / self.speed):
                return True
            time.sleep(0.01)
        return False

    def results(self, report, rows, allow_menu=False):
        self.root.unbind("<Key>")
        self.container.destroy()
        self.root.title("Learn2Slither | Results")
        panel = tk.Frame(self.root, bg=BG, padx=28, pady=24)
        panel.pack()
        label(panel, "RUN COMPLETE", 10, GREEN).pack(anchor="w")
        label(panel, "Every run is a lesson.", 26).pack(anchor="w", pady=8)
        label(panel, f"Games: {report['sessions']}  /  "
              f"{report['size']} × {report['size']} board  /  "
              f"seed {report['seed']}", 11, MUTED).pack(anchor="w")
        metrics = tk.Frame(panel, bg=BG)
        metrics.pack(fill="x", pady=20)
        for title, value in (
                ("MEAN FINAL LENGTH", f"{report['mean_length']:.2f}"),
                ("BEST FINAL LENGTH", str(report["best_final_length"])),
                ("MEAN LIFETIME", f"{report['mean_steps']:.0f}"),
                ("FINAL LENGTH ≥ 10", f"{report['final_10_rate']:.0%}")):
            card = tk.Frame(metrics, bg=PANEL, padx=14, pady=12)
            card.pack(side="left", padx=(0, 8), fill="both", expand=True)
            label(card, title, 8, MUTED, PANEL).pack(anchor="w")
            label(card, value, 26, TEXT, PANEL).pack(anchor="w", pady=(8, 0))
        label(panel, "FINAL LENGTH / LAST 100 GAMES", 9,
              MUTED).pack(anchor="w")
        chart = tk.Canvas(panel, width=660, height=150, bg=BG,
                          highlightthickness=0)
        chart.pack(pady=8)
        trend(chart, [row["length"] for row in rows], 660, 150)
        goals = tk.Frame(panel, bg=BG)
        goals.pack(fill="x", pady=12)
        for goal in (15, 20, 25, 30, 35):
            rate = report["bonus_final_rates"][str(goal)]
            color = GREEN if rate else MUTED
            label(goals, f"≥ {goal}\n{rate:.1%}", 12, color,
                  justify="center").pack(side="left", expand=True)
        label(panel, f"Peak length: {report['best_length']}   /   "
              f"Longest life: {report['longest_life']} moves   /   "
              f"Step-limit endings: {report['truncated']}",
              10, MUTED).pack(anchor="w", pady=8)
        controls = tk.Frame(panel, bg=BG)
        controls.pack(fill="x", pady=(12, 0))
        button(controls, "Export JSON", lambda: self.export(
            report, rows, "json")).pack(side="left", padx=(0, 8))
        button(controls, "Export CSV", lambda: self.export(
            report, rows, "csv")).pack(side="left")
        button(controls, "Close", self.close).pack(side="right")
        if allow_menu:
            button(controls, "Back to lobby", self.back_to_menu,
                   True).pack(side="right", padx=8)
        self.root.bind("<Escape>", lambda event: self.close())
        self.root.mainloop()

    def export(self, report, rows, kind):
        filename = filedialog.asksaveasfilename(
            parent=self.root, defaultextension="." + kind,
            initialfile="slither-results." + kind,
            filetypes=[(kind.upper(), "*." + kind)])
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8", newline="") as stream:
                if kind == "json":
                    json.dump(report, stream, indent=2)
                    stream.write("\n")
                else:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
        except OSError as error:
            messagebox.showerror("Cannot export", str(error), parent=self.root)

    def back_to_menu(self):
        self.return_to_menu = True
        self.close()

    def close(self):
        if not self.closed:
            self.closed = True
            self.root.destroy()
