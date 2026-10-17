"""Sudoku game - Python 3 + tkinter (no extra packages needed).

Run:  python sudoku.py

Controls:
  Click a cell, then press 1-9 to fill it.
  Backspace / Delete / 0 clears a cell.
  Arrow keys move the selection.
"""

import random
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------- logic

def is_valid(board, r, c, n):
    for i in range(9):
        if board[r][i] == n or board[i][c] == n:
            return False
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if board[i][j] == n:
                return False
    return True


def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def fill_random(board):
    """Fill a full valid board using randomized backtracking."""
    pos = find_empty(board)
    if not pos:
        return True
    r, c = pos
    nums = list(range(1, 10))
    random.shuffle(nums)
    for n in nums:
        if is_valid(board, r, c, n):
            board[r][c] = n
            if fill_random(board):
                return True
            board[r][c] = 0
    return False


def count_solutions(board, limit=2):
    pos = find_empty(board)
    if not pos:
        return 1
    r, c = pos
    total = 0
    for n in range(1, 10):
        if is_valid(board, r, c, n):
            board[r][c] = n
            total += count_solutions(board, limit - total)
            board[r][c] = 0
            if total >= limit:
                break
    return total


def generate(clues):
    """Return (puzzle, solution) with a unique solution."""
    solution = [[0] * 9 for _ in range(9)]
    fill_random(solution)
    puzzle = [row[:] for row in solution]
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    remaining = 81
    for r, c in cells:
        if remaining <= clues:
            break
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        if count_solutions([row[:] for row in puzzle]) != 1:
            puzzle[r][c] = backup
        else:
            remaining -= 1
    return puzzle, solution


# ------------------------------------------------------------------ GUI

CELL = 60
MARGIN = 10
SIZE = CELL * 9 + MARGIN * 2
DIFFICULTY = {"Easy": 40, "Medium": 32, "Hard": 26}


class SudokuApp:
    def __init__(self, root):
        self.root = root
        root.title("Sudoku")
        root.resizable(False, False)

        top = tk.Frame(root)
        top.pack(pady=6)
        tk.Label(top, text="Difficulty:").pack(side="left")
        self.diff = tk.StringVar(value="Medium")
        tk.OptionMenu(top, self.diff, *DIFFICULTY).pack(side="left", padx=4)
        tk.Button(top, text="New Game", command=self.new_game).pack(side="left", padx=4)
        self.timer_label = tk.Label(top, text="00:00", width=6)
        self.timer_label.pack(side="left", padx=8)

        self.canvas = tk.Canvas(root, width=SIZE, height=SIZE, bg="white", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        root.bind("<Key>", self.on_key)

        bottom = tk.Frame(root)
        bottom.pack(pady=6)
        tk.Button(bottom, text="Check", command=self.check).pack(side="left", padx=4)
        tk.Button(bottom, text="Hint", command=self.hint).pack(side="left", padx=4)
        tk.Button(bottom, text="Reset", command=self.reset).pack(side="left", padx=4)
        tk.Button(bottom, text="Solve", command=self.solve).pack(side="left", padx=4)

        self.status = tk.Label(root, text="", fg="gray30")
        self.status.pack(pady=(0, 6))

        self.sel = None
        self.seconds = 0
        self.running = False
        self.new_game()
        self.tick()

    # ---- game state
    def new_game(self):
        self.status.config(text="Generating...")
        self.root.update_idletasks()
        self.puzzle, self.solution = generate(DIFFICULTY[self.diff.get()])
        self.board = [row[:] for row in self.puzzle]
        self.sel = None
        self.seconds = 0
        self.running = True
        self.status.config(text="")
        self.draw()

    def reset(self):
        self.board = [row[:] for row in self.puzzle]
        self.draw()

    def solve(self):
        self.board = [row[:] for row in self.solution]
        self.running = False
        self.draw()

    def hint(self):
        target = self.sel
        if not target or self.puzzle[target[0]][target[1]] != 0 \
                or self.board[target[0]][target[1]] == self.solution[target[0]][target[1]]:
            wrong_or_empty = [(r, c) for r in range(9) for c in range(9)
                              if self.puzzle[r][c] == 0 and self.board[r][c] != self.solution[r][c]]
            if not wrong_or_empty:
                return
            target = random.choice(wrong_or_empty)
        r, c = target
        self.board[r][c] = self.solution[r][c]
        self.sel = (r, c)
        self.draw()
        self.check_win()

    def conflicts(self):
        bad = set()
        for r in range(9):
            for c in range(9):
                n = self.board[r][c]
                if n and self.puzzle[r][c] == 0:
                    self.board[r][c] = 0
                    if not is_valid(self.board, r, c, n):
                        bad.add((r, c))
                    self.board[r][c] = n
        return bad

    def check(self):
        bad = self.conflicts()
        wrong = [(r, c) for r in range(9) for c in range(9)
                 if self.board[r][c] and self.board[r][c] != self.solution[r][c]]
        if wrong:
            self.status.config(text=f"{len(wrong)} cell(s) are incorrect.")
        elif find_empty(self.board):
            self.status.config(text="No mistakes so far.")
        self.draw(extra_bad=set(wrong) | bad)
        self.check_win()

    def check_win(self):
        if not find_empty(self.board) and self.board == self.solution and self.running:
            self.running = False
            self.status.config(text="Solved!")
            m, s = divmod(self.seconds, 60)
            messagebox.showinfo("Sudoku", f"You solved it in {m:02d}:{s:02d}!")

    # ---- input
    def on_click(self, e):
        c = (e.x - MARGIN) // CELL
        r = (e.y - MARGIN) // CELL
        self.sel = (r, c) if 0 <= r < 9 and 0 <= c < 9 else None
        self.draw()

    def on_key(self, e):
        if not self.sel:
            return
        r, c = self.sel
        if e.keysym in ("Up", "Down", "Left", "Right"):
            dr, dc = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}[e.keysym]
            self.sel = ((r + dr) % 9, (c + dc) % 9)
        elif self.puzzle[r][c] == 0:
            if e.char in "123456789" and e.char:
                self.board[r][c] = int(e.char)
            elif e.keysym in ("BackSpace", "Delete") or e.char == "0":
                self.board[r][c] = 0
            else:
                return
            self.status.config(text="")
        self.draw()
        self.check_win()

    # ---- drawing
    def draw(self, extra_bad=None):
        cv = self.canvas
        cv.delete("all")
        bad = self.conflicts() | (extra_bad or set())

        if self.sel:
            sr, sc = self.sel
            for i in range(9):
                for (r, c) in ((sr, i), (i, sc)):
                    self.fill_cell(r, c, "#eeeeee")
            for i in range(3):
                for j in range(3):
                    self.fill_cell(3 * (sr // 3) + i, 3 * (sc // 3) + j, "#eeeeee")
            self.fill_cell(sr, sc, "#cfd8e6")

        for r, c in bad:
            self.fill_cell(r, c, "#f4c7c3")

        for i in range(10):
            w = 3 if i % 3 == 0 else 1
            p = MARGIN + i * CELL
            cv.create_line(MARGIN, p, SIZE - MARGIN, p, width=w)
            cv.create_line(p, MARGIN, p, SIZE - MARGIN, width=w)

        for r in range(9):
            for c in range(9):
                n = self.board[r][c]
                if n:
                    given = self.puzzle[r][c] != 0
                    cv.create_text(
                        MARGIN + c * CELL + CELL // 2,
                        MARGIN + r * CELL + CELL // 2,
                        text=str(n),
                        font=("Helvetica", 24, "bold" if given else "normal"),
                        fill="black" if given else "#1a4fa0",
                    )

    def fill_cell(self, r, c, color):
        x, y = MARGIN + c * CELL, MARGIN + r * CELL
        self.canvas.create_rectangle(x, y, x + CELL, y + CELL, fill=color, outline="")

    def tick(self):
        if self.running:
            self.seconds += 1
        m, s = divmod(self.seconds, 60)
        self.timer_label.config(text=f"{m:02d}:{s:02d}")
        self.root.after(1000, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    SudokuApp(root)
    root.mainloop()
