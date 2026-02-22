import tkinter as tk
from editor_core import PDFEngine
from viewer_ui import PDFViewerUI

def main():
    root = tk.Tk()
    root.title("PDF Editor")
    root.geometry("1100x800")

    engine = PDFEngine()
    app = PDFViewerUI(root, engine)

    root.mainloop()

if __name__ == "__main__":
    main()