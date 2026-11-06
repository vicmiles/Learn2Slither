"""Configuration lobby for graphical runs."""

import argparse
from pathlib import Path
from tkinter import filedialog

from agent import Agent
from ui import (BG, BLUE, GREEN, LINE, MUTED, PANEL, TEXT, button,
                label, rounded, tk, window)


class Lobby:
    def __init__(self, args):
        self.args = args
        self.result = None
        self.root = window("Learn2Slither | Lobby")
        self.root.resizable(False, False)
        outer = tk.Frame(self.root, bg=BG, padx=28, pady=24)
        outer.pack()
        label(outer, "L2S  /  REINFORCEMENT LEARNING", 10,
              GREEN).pack(anchor="w")
        label(outer, "Learn2Slither", 30).pack(anchor="w", pady=(8, 2))
        label(outer, "A small snake. A table of possibilities.", 12,
              MUTED).pack(anchor="w")
        content = tk.Frame(outer, bg=BG)
        content.pack(pady=22)
        self.art(content)
        form = tk.Frame(content, bg=PANEL, padx=22, pady=18)
        form.pack(side="left", fill="both", padx=(22, 0))
        label(form, "CONFIGURE A RUN", 11, GREEN,
              PANEL).grid(row=0, column=0, columnspan=3, sticky="w",
                          pady=(0, 14))
        models = sorted(str(path) for path in Path("models").glob("*.json"))
        default = "models/best.json" if "models/best.json" in models else (
            "New agent")
        selected = args.load or default
        self.model = tk.StringVar(value=selected)
        self.field(form, "Model", 1)
        choices = ["New agent"] + models
        if selected not in choices:
            choices.append(selected)
        dropdown = tk.OptionMenu(form, self.model, *choices)
        dropdown.config(bg=LINE, fg=TEXT, activebackground=LINE,
                        highlightthickness=0, width=23, anchor="w")
        dropdown["menu"].config(bg=PANEL, fg=TEXT)
        dropdown.grid(row=1, column=1, sticky="ew")
        button(form, "...", self.browse).grid(row=1, column=2, padx=(6, 0))
        self.size = self.input(form, "Board size", args.size, 2, 5, 40)
        self.sessions = self.input(form, "Games", args.sessions, 3, 1, 1000000)
        self.speed = self.input(form, "Moves / second", args.speed, 4, 1, 120)
        self.seed = self.input(form, "Random seed", args.seed, 5)
        self.limit = self.input(form, "Step limit", args.max_steps, 6, 1,
                                10000000)
        self.learning = tk.BooleanVar(value=False)
        self.step = tk.BooleanVar(value=args.step_by_step)
        for row, text, variable in (
                (7, "Enable learning", self.learning),
                (8, "Step-by-step mode", self.step)):
            tk.Checkbutton(
                form, text=text, variable=variable, bg=PANEL, fg=TEXT,
                selectcolor=BG, activebackground=PANEL,
                activeforeground=TEXT, highlightthickness=0
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=4)
        label(form, "Evaluation keeps Q-values unchanged.", 9, MUTED,
              PANEL).grid(row=9, column=0, columnspan=3, sticky="w",
                          pady=(8, 0))
        self.error = label(outer, "", 10, "#ef8983", wraplength=690)
        self.error.pack(anchor="w")
        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill="x", pady=(8, 0))
        label(footer, "Green: grow / Red: shrink / Blue: agent",
              10, MUTED).pack(side="left", padx=(0, 20))
        button(footer, "Start run  →", self.start, True).pack(side="right")
        self.root.bind("<Return>", lambda event: self.start())
        self.root.bind("<Escape>", lambda event: self.root.destroy())

    def field(self, parent, title, row):
        label(parent, title, 10, MUTED, PANEL).grid(
            row=row, column=0, sticky="w", padx=(0, 14), pady=8)

    def input(self, parent, title, value, row, low=None, high=None):
        self.field(parent, title, row)
        variable = tk.StringVar(value=str(value))
        options = dict(textvariable=variable, bg=BG, fg=TEXT, relief="flat",
                       insertbackground=GREEN, width=12)
        if low is None:
            widget = tk.Entry(parent, **options)
        else:
            widget = tk.Spinbox(parent, from_=low, to=high, **options)
        widget.grid(row=row, column=1, columnspan=2, sticky="ew", ipady=6)
        return variable

    def art(self, parent):
        panel = tk.Frame(parent, bg=BG)
        panel.pack(side="left", anchor="n")
        canvas = tk.Canvas(panel, width=240, height=240, bg=BG,
                           highlightthickness=0)
        canvas.pack()
        rounded(canvas, 0, 0, 240, 240, 18, PANEL)
        for y in range(6):
            for x in range(6):
                rounded(canvas, 15 + x * 35, 15 + y * 35,
                        45 + x * 35, 45 + y * 35, 5, "#233744")
        for x, y in ((1, 4), (1, 3), (2, 3), (3, 3), (3, 2)):
            rounded(canvas, 16 + x * 35, 16 + y * 35,
                    45 + x * 35, 45 + y * 35, 7, BLUE)
        canvas.create_oval(131, 91, 136, 96, fill=BG, outline="")
        canvas.create_oval(145, 91, 150, 96, fill=BG, outline="")
        canvas.create_oval(164, 58, 188, 82, fill=GREEN, outline="")
        label(panel, "LEARN · EXPLORE · GROW", 11, GREEN).pack(
            anchor="w", pady=(20, 8))
        label(panel, "Only four rays of vision.\nFour possible actions.\n"
              "No hidden map or pathfinder.", 11, MUTED,
              justify="left").pack(anchor="w")
        label(panel, "GOALS   10 / 15 / 20 / 25 / 30 / 35", 9,
              MUTED).pack(anchor="w", pady=(22, 0))

    def browse(self):
        filename = filedialog.askopenfilename(
            parent=self.root, title="Choose a Q-learning model",
            filetypes=[("JSON model", "*.json"), ("All files", "*")])
        if filename:
            self.model.set(filename)

    def start(self):
        try:
            args = argparse.Namespace(**vars(self.args))
            args.size = int(self.size.get())
            args.sessions = int(self.sessions.get())
            args.speed = int(self.speed.get())
            args.seed = int(self.seed.get())
            args.max_steps = int(self.limit.get())
            if not 5 <= args.size <= 40:
                raise ValueError("Board size must be between 5 and 40")
            if args.sessions < 1 or args.max_steps < 1:
                raise ValueError("Games and step limit must be positive")
            if not 1 <= args.speed <= 120:
                raise ValueError("Speed must be between 1 and 120")
            args.load = None if self.model.get() == "New agent" else (
                self.model.get())
            if args.load:
                Agent.load(args.load)
            args.dontlearn = not self.learning.get()
            args.step_by_step = self.step.get()
            args.visual = "on"
            if args.dontlearn and args.checkpoint_dir:
                raise ValueError("Checkpoint directory requires learning")
            if not args.dontlearn and not args.save:
                args.save = "models/menu-trained.json"
            self.result = args
            self.root.destroy()
        except (ValueError, OSError) as error:
            self.error.config(text=str(error))

    def show(self):
        self.root.mainloop()
        return self.result
