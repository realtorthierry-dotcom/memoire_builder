from __future__ import annotations

import tkinter as tk

from app.gui import MemoireApp


def main() -> None:
    root = tk.Tk()
    MemoireApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
