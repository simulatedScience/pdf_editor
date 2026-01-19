
import tkinter as tk
from tkinter import filedialog
from PyPDF2 import PdfReader, PdfWriter
import os
import math
from pdf2image import convert_from_path
from PIL import Image, ImageTk

# --- Custom UI Components ---

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg="#4A90E2", hover_bg="#357ABD", 
                 fg="white", width=120, height=40, radius=8, font=("Segoe UI", 10, "bold"), **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=parent.cget('bg'), **kwargs)
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.text = text
        self.radius = radius
        self.font = font
        self.enabled = True
        
        self.draw_button(bg)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def draw_button(self, color):
        self.delete("all")
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        r = self.radius
        
        # Rounded rectangle
        points = [r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0]
        self.create_polygon(points, fill=color, smooth=True, outline="")
        self.create_text(w//2, h//2, text=self.text, fill=self.fg, font=self.font)
    
    def on_enter(self, e):
        if self.enabled: self.draw_button(self.hover_bg)
    
    def on_leave(self, e):
        self.draw_button(self.bg if self.enabled else "#cccccc")
    
    def on_click(self, e):
        if self.command and self.enabled: self.command()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.draw_button(self.bg if enabled else "#cccccc")

class MessageBanner(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=parent.cget('bg'), height=0) # Start hidden
        self.pack_propagate(False)
        self.message_frame = None
        self.after_id = None
    
    def show_message(self, message, msg_type="info"):
        if self.message_frame: self.message_frame.destroy()
        if self.after_id: self.after_cancel(self.after_id)
        
        self.config(height=50) # Expand
        
        colors = {
            "success": ("#d4edda", "#155724", "✓"),
            "error": ("#f8d7da", "#721c24", "✗"),
            "warning": ("#fff3cd", "#856404", "⚠"),
            "info": ("#d1ecf1", "#0c5460", "ℹ")
        }
        bg, fg, icon = colors.get(msg_type, colors["info"])
        
        self.message_frame = tk.Frame(self, bg=bg)
        self.message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        content = tk.Frame(self.message_frame, bg=bg)
        content.pack(expand=True, fill=tk.Y)
        
        tk.Label(content, text=icon, font=("Segoe UI", 14), fg=fg, bg=bg).pack(side=tk.LEFT, padx=5)
        tk.Label(content, text=message, font=("Segoe UI", 10), fg=fg, bg=bg).pack(side=tk.LEFT, padx=5)
        
        self.after_id = self.after(4000, self.hide_message)
    
    def hide_message(self):
        if self.message_frame: self.message_frame.destroy()
        self.config(height=0) # Collapse

# --- Core Data Class ---

class PageData:
    """Stores information about a specific page from a specific file."""
    def __init__(self, source_path, page_index, image, display_index_str):
        self.source_path = source_path
        self.page_index = page_index # 0-based index in original file
        self.image = image
        self.display_index_str = display_index_str # e.g. "Doc1 - Pg 1"
        self.id = f"{source_path}_{page_index}" # Unique ID

# --- Draggable Thumbnail Widget ---

class DraggableThumbnail(tk.Frame):
    def __init__(self, parent, page_data, selection_callback, drag_start_callback, drag_end_callback, **kwargs):
        super().__init__(parent, **kwargs)
        self.page_data = page_data
        self.selection_callback = selection_callback
        self.drag_start_callback = drag_start_callback
        self.drag_end_callback = drag_end_callback
        self.is_selected = False
        
        self.config(bg="white", relief=tk.FLAT, bd=1)
        
        # Inner container for visual padding
        self.inner = tk.Frame(self, bg="white", padx=5, pady=5)
        self.inner.pack(fill=tk.BOTH, expand=True)
        
        # Image Canvas
        self.canvas = tk.Canvas(self.inner, width=100, height=130, bg="#f0f0f0", 
                               highlightthickness=0, bd=0)
        self.canvas.pack()
        
        # Set Image
        self.photo = ImageTk.PhotoImage(page_data.image.resize((100, 130)))
        self.canvas.create_image(50, 65, image=self.photo)
        
        # Label
        self.lbl = tk.Label(self.inner, text=page_data.display_index_str, 
                           font=("Segoe UI", 8), bg="white", fg="#666")
        self.lbl.pack(pady=(4,0))
        
        # Bindings for selection and dragging
        for widget in [self, self.inner, self.canvas, self.lbl]:
            widget.bind("<Button-1>", self.on_click_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)
            widget.bind("<ButtonRelease-1>", self.on_drag_release)

        self._drag_started = False
        self._start_x = 0
        self._start_y = 0

    def set_selected(self, selected):
        self.is_selected = selected
        color = "#ffcccc" if selected else "white"
        border = "#e53935" if selected else "white"
        thickness = 2 if selected else 1
        
        self.config(bg=border, bd=thickness)
        self.inner.config(bg=color)
        self.lbl.config(bg=color, fg="#c62828" if selected else "#666")
        self.canvas.config(bg=color)

    def on_click_start(self, event):
        self._drag_started = False
        self._start_x = event.x
        self._start_y = event.y
        # Immediate visual feedback for selection
        self.selection_callback(self, event.state & 0x0004) # Check for Ctrl key

    def on_drag_motion(self, event):
        # Threshold to detect drag vs click
        if not self._drag_started and (abs(event.x - self._start_x) > 5 or abs(event.y - self._start_y) > 5):
            self._drag_started = True
            self.drag_start_callback(self, event)
        
        if self._drag_started:
            # We don't move self; the controller creates a 'ghost' window
            pass 

    def on_drag_release(self, event):
        if self._drag_started:
            self.drag_end_callback(event)
            self._drag_started = False

# --- Main Application ---

class PDFEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern PDF Editor")
        self.root.geometry("1100x800")
        self.root.config(bg="#f5f5f5")
        
        # State
        self.pages_data = [] # List of PageData objects (Ordered)
        self.page_widgets = [] # List of DraggableThumbnail widgets
        self.selected_indices = set()
        
        # Drag State
        self.drag_data = {"item_idx": None, "window": None}

        self.setup_ui()
    
    def setup_ui(self):
        # 1. Top Bar (File Ops & Output)
        top_bar = tk.Frame(self.root, bg="white", pady=15, padx=20)
        top_bar.pack(fill=tk.X)
        
        # Input/Add Buttons
        tk.Label(top_bar, text="Actions:", font=("Segoe UI", 10, "bold"), bg="white").pack(side=tk.LEFT)
        RoundedButton(top_bar, "Add PDF", self.add_pdf, width=100, height=30, bg="#4A90E2").pack(side=tk.LEFT, padx=10)
        RoundedButton(top_bar, "Insert After Selected", self.insert_pdf_at_selection, width=160, height=30, bg="#357ABD").pack(side=tk.LEFT, padx=0)

        # Output Path
        tk.Frame(top_bar, width=20, bg="white").pack(side=tk.LEFT) # Spacer
        tk.Label(top_bar, text="Output:", font=("Segoe UI", 10, "bold"), bg="white").pack(side=tk.LEFT)
        
        self.output_var = tk.StringVar()
        self.output_entry = tk.Entry(top_bar, textvariable=self.output_var, width=40, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.output_entry.pack(side=tk.LEFT, padx=10, ipady=4)
        
        RoundedButton(top_bar, "Browse", self.browse_output, width=80, height=30, bg="#95a5a6").pack(side=tk.LEFT)

        # 2. Message Banner
        self.banner = MessageBanner(self.root)
        self.banner.pack(fill=tk.X)

        # 3. Main Workspace (Scrollable)
        work_frame = tk.Frame(self.root, bg="#f5f5f5")
        work_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Toolbar above grid
        toolbar = tk.Frame(work_frame, bg="#f5f5f5")
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        self.info_label = tk.Label(toolbar, text="0 Pages loaded", bg="#f5f5f5", fg="#666", font=("Segoe UI", 11))
        self.info_label.pack(side=tk.LEFT)
        
        # Right aligned action buttons
        RoundedButton(toolbar, "Clear All", self.clear_all, bg="#7f8c8d", width=90, height=30).pack(side=tk.RIGHT, padx=5)
        RoundedButton(toolbar, "Remove Selected", self.remove_selected, bg="#e53935", hover_bg="#c62828", width=140, height=30).pack(side=tk.RIGHT, padx=5)

        # The Grid Area
        self.canvas = tk.Canvas(work_frame, bg="#e0e0e0", highlightthickness=0)
        scrollbar = tk.Scrollbar(work_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#e0e0e0")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mousewheel binding
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # 4. Bottom Save Bar
        bottom_bar = tk.Frame(self.root, bg="white", height=70)
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        bottom_bar.pack_propagate(False)
        
        RoundedButton(bottom_bar, "Save Final PDF", self.save_pdf, bg="#27ae60", hover_bg="#219150", width=200, height=45, radius=10, font=("Segoe UI", 12, "bold")).pack(pady=12)

    # --- Logic ---

    def add_pdf(self, insert_index=None):
        filenames = filedialog.askopenfilenames(title="Select PDF(s)", filetypes=[("PDF files", "*.pdf")])
        if not filenames: return
        
        self.process_files(filenames, insert_index)

    def insert_pdf_at_selection(self):
        # Insert after the last selected item, or at end if nothing selected
        if not self.selected_indices:
            self.add_pdf() # Just append
            return
            
        # Find the highest index selected to insert after
        insert_idx = max(self.selected_indices) + 1
        self.add_pdf(insert_index=insert_idx)

    def process_files(self, filenames, insert_index=None):
        # If this is the first file loaded, set default output path
        if not self.pages_data and len(filenames) > 0:
            first_file = filenames[0]
            folder = os.path.dirname(first_file)
            name = os.path.splitext(os.path.basename(first_file))[0]
            default_out = os.path.join(folder, f"{name}_merged.pdf")
            self.output_var.set(default_out)

        total_new = 0
        new_pages = []

        # Show loading indicator (cursor)
        self.root.config(cursor="watch")
        self.root.update()

        try:
            for fpath in filenames:
                try:
                    # Load PDF
                    reader = PdfReader(fpath)
                    count = len(reader.pages)
                    
                    # Generate thumbnails (Limit resolution for performance)
                    # Note: Requires Poppler installed
                    images = convert_from_path(fpath, dpi=40) 
                    
                    fname = os.path.basename(fpath)
                    short_name = (fname[:10] + '..') if len(fname) > 10 else fname
                    
                    for i in range(count):
                        # Create PageData object
                        img = images[i] if i < len(images) else Image.new('RGB', (100, 130), 'white')
                        p = PageData(fpath, i, img, f"{short_name}\nPg {i+1}")
                        new_pages.append(p)
                        
                    total_new += count
                except Exception as e:
                    self.banner.show_message(f"Error reading {os.path.basename(fpath)}: {e}", "error")
            
            # Insert into main list
            if insert_index is None:
                self.pages_data.extend(new_pages)
            else:
                self.pages_data[insert_index:insert_index] = new_pages
                
            self.refresh_grid()
            self.banner.show_message(f"Added {total_new} pages", "success")
            
        finally:
            self.root.config(cursor="")

    def browse_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if f: self.output_var.set(f)

    def clear_all(self):
        self.pages_data.clear()
        self.selected_indices.clear()
        self.output_var.set("")
        self.refresh_grid()
        self.banner.show_message("All pages cleared", "info")

    def remove_selected(self):
        if not self.selected_indices:
            self.banner.show_message("No pages selected to remove", "warning")
            return
            
        # Sort indices in descending order to delete correctly
        for idx in sorted(self.selected_indices, reverse=True):
            del self.pages_data[idx]
            
        self.selected_indices.clear()
        self.refresh_grid()
        self.banner.show_message("Selected pages removed", "info")

    def refresh_grid(self):
        # Clean UI
        for w in self.page_widgets: w.destroy()
        self.page_widgets.clear()
        
        # Re-render
        cols = 6
        for i, p_data in enumerate(self.pages_data):
            row, col = divmod(i, cols)
            
            thumb = DraggableThumbnail(self.scrollable_frame, p_data, 
                                     self.on_thumb_click,
                                     self.on_drag_start,
                                     self.on_drag_end)
            thumb.grid(row=row, column=col, padx=10, pady=10)
            
            # Restore selection state
            if i in self.selected_indices:
                thumb.set_selected(True)
                
            self.page_widgets.append(thumb)
            
        self.info_label.config(text=f"{len(self.pages_data)} Pages | Drag to reorder")

    # --- Interaction Logic ---

    def on_thumb_click(self, widget, is_ctrl_pressed):
        # Find index of widget
        try:
            idx = self.page_widgets.index(widget)
        except ValueError: return

        if is_ctrl_pressed:
            # Toggle
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
                widget.set_selected(False)
            else:
                self.selected_indices.add(idx)
                widget.set_selected(True)
        else:
            # Exclusive select
            for old_idx in self.selected_indices:
                if old_idx < len(self.page_widgets):
                    self.page_widgets[old_idx].set_selected(False)
            self.selected_indices.clear()
            
            self.selected_indices.add(idx)
            widget.set_selected(True)

    def on_drag_start(self, widget, event):
        try:
            idx = self.page_widgets.index(widget)
            self.drag_data["item_idx"] = idx
            
            # Create semi-transparent ghost window
            top = tk.Toplevel(self.root)
            top.overrideredirect(True)
            top.attributes('-alpha', 0.6)
            
            # Copy image to label
            lbl = tk.Label(top, image=widget.photo, bg="white", relief=tk.SOLID, bd=2)
            lbl.pack()
            
            self.drag_data["window"] = top
            self.update_drag_window(event)
            
        except ValueError: pass

    def on_drag_motion_global(self, event):
        # This would be needed if dragging outside the widget, 
        # but Toplevel follows mouse via bind on widget
        pass

    def update_drag_window(self, event):
        if self.drag_data["window"]:
            x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
            self.drag_data["window"].geometry(f"+{x+10}+{y+10}")

    def on_drag_end(self, event):
        if self.drag_data["window"]:
            self.drag_data["window"].destroy()
            self.drag_data["window"] = None
        
        start_idx = self.drag_data["item_idx"]
        if start_idx is None: return

        # Calculate where we dropped it
        # We need relative coordinates to the scrollable frame
        x_root, y_root = self.root.winfo_pointerx(), self.root.winfo_pointery()
        
        # Find the nearest widget
        nearest_idx = start_idx
        min_dist = float('inf')
        
        for i, widget in enumerate(self.page_widgets):
            wx = widget.winfo_rootx() + widget.winfo_width() // 2
            wy = widget.winfo_rooty() + widget.winfo_height() // 2
            dist = math.hypot(wx - x_root, wy - y_root)
            
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i

        if nearest_idx != start_idx:
            # Move item in data list
            item = self.pages_data.pop(start_idx)
            self.pages_data.insert(nearest_idx, item)
            
            # Clear selection to avoid confusion or remap it
            self.selected_indices.clear()
            self.selected_indices.add(nearest_idx)
            
            self.refresh_grid()
            self.banner.show_message("Page reordered", "info")

    # --- Save ---

    def save_pdf(self):
        if not self.pages_data:
            self.banner.show_message("No pages to save!", "error")
            return
            
        output_path = self.output_var.get()
        if not output_path:
            self.banner.show_message("Please select an output file path", "warning")
            self.browse_output()
            return

        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            writer = PdfWriter()
            
            # Cache open file handles to avoid opening/closing repeatedly
            open_files = {} 
            
            for page_data in self.pages_data:
                src = page_data.source_path
                if src not in open_files:
                    open_files[src] = open(src, 'rb')
                    
                # We need a fresh reader for the open file handle or PyPDF2 gets confused
                # efficient way: Read objects on demand
                # Simpler robust way for GUI: Re-read page
                r = PdfReader(open_files[src])
                writer.add_page(r.pages[page_data.page_index])
            
            with open(output_path, "wb") as f_out:
                writer.write(f_out)
                
            # Close handles
            for f in open_files.values():
                f.close()
                
            self.banner.show_message(f"Successfully saved to {os.path.basename(output_path)}", "success")
            
        except Exception as e:
            self.banner.show_message(f"Save failed: {e}", "error")
            print(e)
        finally:
            self.root.config(cursor="")

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) # Sharp text on Windows
    except: pass
    
    root = tk.Tk()
    app = PDFEditorApp(root)
    root.mainloop()
