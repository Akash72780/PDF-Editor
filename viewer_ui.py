import tkinter as tk
from tkinter import ttk, filedialog, messagebox,simpledialog
from PIL import Image, ImageTk
import fitz

class PDFViewerUI:
    def __init__(self, root, engine):
        self.root = root
        self.engine = engine
        self.tk_images = []
        self.current_viewing_name = None # Track what is currently on screen
        self.active_viewer_doc = None
        self.setup_sidebar()
        self.setup_viewer()

    def setup_sidebar(self):
        sidebar = tk.Frame(self.root, width=200, padx=10, pady=10, bg="#eeeeee")
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="Edit PDF", font=("Arial", 12, "bold"), bg="#eeeeee").pack(pady=10)

        tk.Button(sidebar, text="Add PDFs", command=self.on_add, width=18).pack(pady=5)
        
        self.listbox = tk.Listbox(sidebar, height=10, width=22)
        self.listbox.pack(pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_item)

        # NEW: Remove Button
        tk.Button(sidebar, text="Remove Selected", command=self.on_remove, width=18, bg="#ffeb3b").pack(pady=5)

        tk.Button(sidebar, text="Merge All", command=self.on_merge_all, width=18, bg="#e1f5fe").pack(pady=5)
        tk.Button(sidebar, text="Rotate 90°", command=self.on_rotate, width=18).pack(pady=5)
        tk.Button(sidebar, text="Insert PDF At...", command=self.on_insert_at, width=18, bg="#b2dfdb").pack(pady=5)
        tk.Button(sidebar, text="Save", command=self.on_save, width=18, bg="#4CAF50", fg="white").pack(pady=5)
        tk.Button(sidebar, text="Delete Page", command=self.on_delete_page, width=18, bg="#ffab91").pack(pady=5)
        tk.Button(sidebar, text="Clear All", command=self.on_clear, width=18, bg="#ffebee").pack(side="bottom", pady=10)

    
    def on_insert_at(self):
        """Handles inserting one PDF into another at a specific page."""
        # 1. Ensure at least two files exist
        if len(self.engine.library) < 2:
            messagebox.showwarning("Warning", "You need at least two PDFs in the list to use this feature.")
            return

        # 2. Get names for selection
        names = list(self.engine.library.keys())
        
        # Create a small pop-up window for selection
        top = tk.Toplevel(self.root)
        top.title("Insert PDF Logic")
        top.geometry("300x250")

        tk.Label(top, text="Select Source (To move):").pack(pady=2)
        source_cb = ttk.Combobox(top, values=names, state="readonly")
        source_cb.pack(pady=5)

        tk.Label(top, text="Select Target (The base):").pack(pady=2)
        target_cb = ttk.Combobox(top, values=names, state="readonly")
        target_cb.pack(pady=5)

        tk.Label(top, text="Insert after page number:").pack(pady=2)
        pos_entry = tk.Entry(top)
        pos_entry.pack(pady=5)

        def execute_insertion():
            src = source_cb.get()
            tgt = target_cb.get()
            pos = pos_entry.get()

            if not src or not tgt or not pos or src == tgt:
                messagebox.showerror("Error", "Check your selections. Source and Target must be different.")
                return

            try:
                pos_int = int(pos)
                success = self.engine.insert_at(tgt, src, pos_int)
                if success:
                    messagebox.showinfo("Success", f"Inserted {src} into {tgt} after page {pos_int}")
                    # Update viewer to show the new combined target
                    self.render_document(self.engine.get_document(tgt), tgt)
                    top.destroy()
            except ValueError:
                messagebox.showerror("Error", "Position must be a number.")

        tk.Button(top, text="Confirm Insert", command=execute_insertion, bg="#4db6ac").pack(pady=10)

    def render_document(self, doc, name=None):
        """Renders pages and keeps a reference to the active document."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.tk_images = []
        self.current_viewing_name = name
        
        # This ensures the 'Save' button has something to point to
        self.active_viewer_doc = doc 

        if not doc: 
            return

        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            tk_img = ImageTk.PhotoImage(img)
            self.tk_images.append(tk_img)
            tk.Label(self.scroll_frame, image=tk_img, bg="gray", pady=10).pack()

    def on_delete_page(self):
        """Prompts for a page number, deletes it, and refreshes the view."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a PDF from the list.")
            return

        name = self.listbox.get(selection[0])
        doc = self.engine.get_document(name)
        
        # 1. Ask user for the page number
        total_pages = len(doc)
        page_num = simpledialog.askinteger(
            "Delete Page", 
            f"Enter page number to delete (1 to {total_pages}):",
            parent=self.root
        )
        
        if page_num is not None:
            # 2. Convert to 0-based index
            page_index = page_num - 1
            
            # 3. Call engine to delete
            success = self.engine.delete_page(name, page_index)
            
            if success:
                # 4. CRITICAL: Re-render the viewer to show the remaining pages
                self.render_document(doc, name)
                messagebox.showinfo("Success", f"Page {page_num} removed. {len(doc)} pages remaining.")
            else:
                messagebox.showerror("Error", f"Could not delete page {page_num}. Please check the page range.")
    def setup_viewer(self):
        self.canvas = tk.Canvas(self.root, bg="gray")
        self.scroll_y = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="gray")

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.canvas.pack(side="left", expand=True, fill="both")
        self.scroll_y.pack(side="right", fill="y")

    def on_add(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        for f in files:
            name = self.engine.load_file(f)
            self.listbox.insert(tk.END, name)

    def on_select_item(self, event):
        selection = self.listbox.curselection()
        if selection:
            name = self.listbox.get(selection[0])
            doc = self.engine.get_document(name)
            self.render_document(doc, name)

    def on_remove(self):
        """Handles the removal of a single PDF from list and viewer."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to remove.")
            return

        name = self.listbox.get(selection[0])
        
        # 1. Remove from Engine
        self.engine.remove_file(name)
        
        # 2. Remove from Listbox
        self.listbox.delete(selection[0])
        
        # 3. If we were viewing this file, clear the viewer
        if self.current_viewing_name == name:
            self.render_document(None)

    def on_merge_all(self):
        merged = self.engine.merge_all()
        if merged:
            self.render_document(merged, "Merged Result")

    def on_rotate(self):
        selection = self.listbox.curselection()
        if selection:
            name = self.listbox.get(selection[0])
            doc = self.engine.get_document(name)
            for page in doc:
                page.set_rotation((page.rotation + 90) % 360)
            self.render_document(doc, name)

    def on_save(self):
        """Saves only the document currently visible in the viewer."""
        # 1. Check if we have an active document in the viewer
        if not self.active_viewer_doc:
            messagebox.showwarning("Warning", "The viewer is empty. Nothing to save.")
            return

        # 2. Ask for file location
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Viewed PDF As"
        )

        if path:
            try:
                # 3. Save the specific document object currently in the viewer
                self.active_viewer_doc.save(path)
                messagebox.showinfo("Success", "PDF saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

    def on_clear(self):
        self.engine.clear()
        self.listbox.delete(0, tk.END)
        self.render_document(None)