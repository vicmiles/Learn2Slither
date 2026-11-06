"""Shared colors and small Tkinter drawing helpers."""

try:
    import tkinter as tk
except ImportError as error:
    raise ValueError(
        "Tkinter is missing. Run make setup or use -visual off"
    ) from error


BG = "#101923"
PANEL = "#192632"
BOARD = "#12212c"
TEXT = "#edf5ef"
MUTED = "#91a7af"
GREEN = "#b6e879"
BLUE = "#72c9dc"
RED = "#ef8983"
LINE = "#2b3d49"


def window(title):
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise ValueError(
            "Cannot open a window. Use -visual off on a headless machine"
        ) from error
    root.title(title)
    root.configure(bg=BG)
    root.option_add("*Font", "{DejaVu Sans} 11")
    return root


def label(parent, text, size=11, color=TEXT, bg=BG, **kwargs):
    return tk.Label(parent, text=text, bg=bg, fg=color,
                    font=("DejaVu Sans", size), **kwargs)


class ActionButton(tk.Label):
    """A keyboard-accessible button with the same colors on macOS and Linux."""

    def __init__(self, parent, text, command, accent=False):
        self.command = command
        self.normal_bg = GREEN if accent else LINE
        self.normal_fg = BG if accent else TEXT
        super().__init__(
            parent, text=text, bg=self.normal_bg, fg=self.normal_fg,
            padx=14, pady=10, cursor="hand2", takefocus=True,
            highlightthickness=1, highlightbackground=BG, highlightcolor=BLUE)
        for event in ("<Button-1>", "<Return>", "<space>"):
            self.bind(event, self.invoke)
        self.bind("<Enter>", lambda event: self.config(bg=BLUE, fg=BG))
        self.bind("<Leave>", lambda event: self.config(
            bg=self.normal_bg, fg=self.normal_fg))

    def invoke(self, event=None):
        self.command()
        return "break"


def button(parent, text, command, accent=False):
    return ActionButton(parent, text, command, accent)


def rounded(canvas, x1, y1, x2, y2, radius, color):
    points = [x1 + radius, y1, x2 - radius, y1, x2, y1,
              x2, y1 + radius, x2, y2 - radius, x2, y2,
              x2 - radius, y2, x1 + radius, y2, x1, y2,
              x1, y2 - radius, x1, y1 + radius, x1, y1]
    return canvas.create_polygon(points, smooth=True, fill=color, outline="")


def trend(canvas, values, width, height):
    """Plot actual final lengths from the most recent 100 games."""
    canvas.delete("all")
    values = values[-100:]
    if not values:
        canvas.create_text(width / 2, height / 2, text="No completed games",
                           fill=MUTED, font=("DejaVu Sans", 10))
        return
    ceiling = max(10, max(values))
    for value in sorted({0, 10, ceiling}):
        y = height - 16 - value / ceiling * (height - 32)
        canvas.create_line(26, y, width - 8, y, fill=LINE)
        canvas.create_text(12, y, text=str(value), fill=MUTED,
                           font=("DejaVu Sans", 8))
    points = []
    for index, value in enumerate(values):
        x = 28 + index / max(1, len(values) - 1) * (width - 40)
        y = height - 16 - value / ceiling * (height - 32)
        points.extend((x, y))
    if len(values) > 1:
        canvas.create_line(*points, fill=GREEN, width=2)
    else:
        x, y = points
        canvas.create_oval(x - 3, y - 3, x + 3, y + 3,
                           fill=GREEN, outline="")
