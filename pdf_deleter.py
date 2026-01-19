import tkinter as tk
from tkinter import filedialog
from PyPDF2 import PdfReader, PdfWriter
import os
from pdf2image import convert_from_path
from PIL import Image, ImageTk, ImageDraw

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg="#4A90E2", hover_bg="#357ABD", 
                 fg="white", width=120, height=40, radius=8, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=parent.cget('bg'), **kwargs)
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.text = text
        self.radius = radius
        self.enabled = True
        
        self.draw_button(bg)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def draw_button(self, color):
        self.delete("all")
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        r = self.radius
        
        # Create rounded rectangle using polygons
        points = [
            r, 0,
            w-r, 0,
            w, 0,
            w, r,
            w, h-r,
            w, h,
            w-r, h,
            r, h,
            0, h,
            0, h-r,
            0, r,
            0, 0
        ]
        
        self.create_polygon(points, fill=color, smooth=True, outline="")
        self.create_text(w//2, h//2, text=self.text, fill=self.fg, 
                        font=("Segoe UI", 10, "bold"))
    
    def on_enter(self, e):
        if self.enabled:
            self.draw_button(self.hover_bg)
    
    def on_leave(self, e):
        self.draw_button(self.bg if self.enabled else "#cccccc")
    
    def on_click(self, e):
        if self.command and self.enabled:
            self.command()
    
    def set_enabled(self, enabled):
        self.enabled = enabled
        self.draw_button(self.bg if enabled else "#cccccc")

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg="#ffffff", radius=12, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.bg = bg
        self.radius = radius
        self.configure(bg=parent.cget('bg'))
        self.bind("<Configure>", self.draw_rounded_rect)
    
    def draw_rounded_rect(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self.radius
        
        points = [
            r, 0,
            w-r, 0,
            w, 0,
            w, r,
            w, h-r,
            w, h,
            w-r, h,
            r, h,
            0, h,
            0, h-r,
            0, r,
            0, 0
        ]
        
        self.create_polygon(points, fill=self.bg, smooth=True, outline="")

class MessageBanner(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=parent.cget('bg'), height=60)
        self.pack_propagate(False)
        
        self.message_frame = None
        self.after_id = None
    
    def show_message(self, message, msg_type="info"):
        # Clear existing message
        if self.message_frame:
            self.message_frame.destroy()
        if self.after_id:
            self.after_cancel(self.after_id)
        
        # Color scheme based on type
        colors = {
            "success": ("#d4edda", "#155724", "✓"),
            "error": ("#f8d7da", "#721c24", "✗"),
            "warning": ("#fff3cd", "#856404", "⚠"),
            "info": ("#d1ecf1", "#0c5460", "ℹ")
        }
        
        bg, fg, icon = colors.get(msg_type, colors["info"])
        
        self.message_frame = tk.Frame(self, bg=bg, relief=tk.FLAT, bd=1)
        self.message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        content = tk.Frame(self.message_frame, bg=bg)
        content.pack(expand=True)
        
        tk.Label(content, text=icon, font=("Segoe UI", 16), 
                fg=fg, bg=bg).pack(side=tk.LEFT, padx=(10, 5))
        tk.Label(content, text=message, font=("Segoe UI", 10), 
                fg=fg, bg=bg).pack(side=tk.LEFT, padx=5)
        
        # Auto-hide after 5 seconds
        self.after_id = self.after(5000, self.hide_message)
    
    def hide_message(self):
        if self.message_frame:
            self.message_frame.destroy()
            self.message_frame = None

class PageThumbnail(tk.Frame):
    def __init__(self, parent, page_num, is_selected, click_callback, **kwargs):
        super().__init__(parent, **kwargs)
        self.page_num = page_num
        self.is_selected = is_selected
        self.click_callback = click_callback
        
        self.config(relief=tk.FLAT, bd=0, bg="#ffffff")
        
        # Container with rounded corners effect
        self.container = tk.Frame(self, bg="#ffffff")
        self.container.pack(padx=3, pady=3)
        
        # Thumbnail placeholder
        self.canvas = tk.Canvas(self.container, width=100, height=130, bg="#f0f0f0", 
                               highlightthickness=0, bd=0)
        self.canvas.pack(padx=5, pady=5)
        
        # Page number label
        self.label = tk.Label(self.container, text=f"Page {page_num}", 
                             font=("Segoe UI", 9), bg="#ffffff")
        self.label.pack(pady=(0, 5))
        
        # Bind click events
        self.bind("<Button-1>", self.on_click)
        self.container.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-1>", self.on_click)
        self.label.bind("<Button-1>", self.on_click)
        
        self.update_appearance()
    
    def on_click(self, e):
        self.click_callback(self.page_num)
    
    def set_selected(self, selected):
        self.is_selected = selected
        self.update_appearance()
    
    def update_appearance(self):
        if self.is_selected:
            self.config(bg="#ffebee", relief=tk.SOLID, bd=3, 
                       highlightbackground="#e53935", highlightthickness=0)
            self.container.config(bg="#ffebee")
            self.label.config(bg="#ffebee", fg="#c62828", font=("Segoe UI", 9, "bold"))
            self.canvas.config(bg="#ffe0e0")
        else:
            self.config(bg="#ffffff", relief=tk.FLAT, bd=1,
                       highlightthickness=0)
            self.container.config(bg="#ffffff")
            self.label.config(bg="#ffffff", fg="#333333", font=("Segoe UI", 9))
            self.canvas.config(bg="#f0f0f0")
    
    def set_preview(self, image):
        """Set thumbnail preview image"""
        try:
            image.thumbnail((90, 120), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.canvas.delete("all")
            self.canvas.create_image(50, 65, image=photo)
            self.canvas.image = photo
        except Exception as e:
            print(f"Error setting preview: {e}")

class PDFPageDeleter:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Page Deleter")
        self.root.geometry("950x750")
        self.root.config(bg="#f5f5f5")
        
        self.pdf_path = None
        self.output_path = None
        self.total_pages = 0
        self.selected_pages = set()
        self.thumbnails = []
        self.preview_images = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="PDF Page Deleter", 
                        font=("Segoe UI", 24, "bold"), 
                        fg="white", bg="#2c3e50")
        title.pack(pady=20)
        
        # Message banner
        self.message_banner = MessageBanner(self.root)
        self.message_banner.pack(fill=tk.X)
        
        # Control panel
        control_frame = tk.Frame(self.root, bg="#ffffff", height=140)
        control_frame.pack(fill=tk.X, padx=20, pady=20)
        control_frame.pack_propagate(False)
        
        # Left side - file info
        left_controls = tk.Frame(control_frame, bg="#ffffff")
        left_controls.pack(side=tk.LEFT, padx=20, pady=20, anchor=tk.W)
        
        tk.Label(left_controls, text="Input PDF:", 
                font=("Segoe UI", 9), fg="#999999", bg="#ffffff").pack(anchor=tk.W)
        
        self.file_label = tk.Label(left_controls, text="No file selected", 
                                   font=("Segoe UI", 11), 
                                   fg="#666666", bg="#ffffff")
        self.file_label.pack(anchor=tk.W, pady=(2, 8))
        
        tk.Label(left_controls, text="Output PDF:", 
                font=("Segoe UI", 9), fg="#999999", bg="#ffffff").pack(anchor=tk.W)
        
        self.output_label = tk.Label(left_controls, text="Not set", 
                                     font=("Segoe UI", 11), 
                                     fg="#666666", bg="#ffffff")
        self.output_label.pack(anchor=tk.W, pady=(2, 8))
        
        info_frame = tk.Frame(left_controls, bg="#ffffff")
        info_frame.pack(anchor=tk.W)
        
        self.pages_label = tk.Label(info_frame, text="", 
                                    font=("Segoe UI", 9), 
                                    fg="#999999", bg="#ffffff")
        self.pages_label.pack(side=tk.LEFT)
        
        self.selected_label = tk.Label(info_frame, text="", 
                                       font=("Segoe UI", 9, "bold"), 
                                       fg="#e53935", bg="#ffffff")
        self.selected_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # Right side - buttons
        right_controls = tk.Frame(control_frame, bg="#ffffff")
        right_controls.pack(side=tk.RIGHT, padx=20, pady=20)
        
        btn_row1 = tk.Frame(right_controls, bg="#ffffff")
        btn_row1.pack(pady=(0, 8))
        
        RoundedButton(btn_row1, "Open PDF", self.browse_file, 
                    bg="#4A90E2", hover_bg="#357ABD", 
                    width=130, height=36, radius=8).pack(side=tk.LEFT, padx=3)
        
        RoundedButton(btn_row1, "Set Output", self.choose_output, 
                    bg="#9C27B0", hover_bg="#7B1FA2", 
                    width=130, height=36, radius=8).pack(side=tk.LEFT, padx=3)
        
        btn_row2 = tk.Frame(right_controls, bg="#ffffff")
        btn_row2.pack()
        
        RoundedButton(btn_row2, "Select All", self.select_all, 
                    bg="#7B68EE", hover_bg="#6A5ACD", 
                    width=90, height=36, radius=8).pack(side=tk.LEFT, padx=3)
        
        RoundedButton(btn_row2, "Clear", self.clear_selection, 
                    bg="#95a5a6", hover_bg="#7f8c8d", 
                    width=70, height=36, radius=8).pack(side=tk.LEFT, padx=3)
        
        self.delete_btn = RoundedButton(btn_row2, "Delete & Save", self.delete_pages, 
                    bg="#e53935", hover_bg="#c62828", 
                    width=140, height=36, radius=8)
        self.delete_btn.pack(side=tk.LEFT, padx=3)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="#f5f5f5")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Instructions
        instr = tk.Label(content_frame, 
                        text="Click on pages below to mark them for deletion", 
                        font=("Segoe UI", 10), 
                        fg="#666666", bg="#f5f5f5")
        instr.pack(pady=(0, 10))
        
        # Scrollable page grid
        canvas_frame = tk.Frame(content_frame, bg="#ffffff", relief=tk.FLAT, bd=0)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ffffff")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Empty state
        self.empty_label = tk.Label(self.scrollable_frame, 
                                    text="Open a PDF file to get started", 
                                    font=("Segoe UI", 14), 
                                    fg="#cccccc", bg="#ffffff")
        self.empty_label.pack(pady=100)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            self.load_pdf(filename)
    
    def choose_output(self):
        if not self.pdf_path:
            self.message_banner.show_message("Please open a PDF file first", "warning")
            return
        
        # Suggest default name
        base, ext = os.path.splitext(self.pdf_path)
        default_name = f"{os.path.basename(base)}_modified{ext}"
        
        filename = filedialog.asksaveasfilename(
            title="Save PDF as",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            self.output_path = filename
            self.output_label.config(text=os.path.basename(filename), fg="#333333")
            self.message_banner.show_message(f"Output path set: {os.path.basename(filename)}", "success")
    
    def load_pdf(self, filename):
        try:
            self.pdf_path = filename
            reader = PdfReader(filename)
            self.total_pages = len(reader.pages)
            self.selected_pages.clear()
            
            # Auto-set output path
            base, ext = os.path.splitext(filename)
            self.output_path = f"{base}_modified{ext}"
            
            self.file_label.config(text=os.path.basename(filename), fg="#333333")
            self.output_label.config(text=os.path.basename(self.output_path), fg="#333333")
            self.pages_label.config(text=f"Total: {self.total_pages} pages")
            self.update_selection_label()
            
            self.message_banner.show_message(f"Loaded PDF with {self.total_pages} pages", "success")
            
            # Generate previews
            self.generate_previews(filename)
            self.display_pages()
            
        except Exception as e:
            self.message_banner.show_message(f"Failed to load PDF: {str(e)}", "error")
    
    def generate_previews(self, filename):
        """Generate thumbnail previews for pages"""
        self.preview_images = []
        try:
            if self.total_pages <= 50:
                images = convert_from_path(filename, dpi=50, first_page=1, 
                                          last_page=min(50, self.total_pages))
                self.preview_images = images
        except Exception as e:
            print(f"Preview generation failed (not critical): {e}")
    
    def display_pages(self):
        # Clear existing thumbnails
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.thumbnails = []
        
        # Create grid of page thumbnails
        cols = 6
        for i in range(self.total_pages):
            page_num = i + 1
            row = i // cols
            col = i % cols
            
            thumb = PageThumbnail(self.scrollable_frame, page_num, 
                                 page_num in self.selected_pages,
                                 self.toggle_page)
            thumb.grid(row=row, column=col, padx=8, pady=8)
            
            # Add preview if available
            if i < len(self.preview_images):
                thumb.set_preview(self.preview_images[i])
            
            self.thumbnails.append(thumb)
    
    def toggle_page(self, page_num):
        if page_num in self.selected_pages:
            self.selected_pages.remove(page_num)
        else:
            self.selected_pages.add(page_num)
        
        # Update thumbnail appearance
        for thumb in self.thumbnails:
            if thumb.page_num == page_num:
                thumb.set_selected(page_num in self.selected_pages)
        
        self.update_selection_label()
    
    def select_all(self):
        if not self.pdf_path:
            self.message_banner.show_message("Please open a PDF file first", "warning")
            return
        
        self.selected_pages = set(range(1, self.total_pages + 1))
        for thumb in self.thumbnails:
            thumb.set_selected(True)
        self.update_selection_label()
        self.message_banner.show_message(f"Selected all {self.total_pages} pages", "info")
    
    def clear_selection(self):
        if not self.selected_pages:
            return
        
        count = len(self.selected_pages)
        self.selected_pages.clear()
        for thumb in self.thumbnails:
            thumb.set_selected(False)
        self.update_selection_label()
        self.message_banner.show_message(f"Cleared {count} selected pages", "info")
    
    def update_selection_label(self):
        if self.selected_pages:
            count = len(self.selected_pages)
            self.selected_label.config(
                text=f"⚠ {count} page{'s' if count != 1 else ''} marked for deletion"
            )
        else:
            self.selected_label.config(text="")
    
    def delete_pages(self):
        if not self.pdf_path:
            self.message_banner.show_message("Please open a PDF file first", "warning")
            return
        
        if not self.selected_pages:
            self.message_banner.show_message("Please select pages to delete", "warning")
            return
        
        count = len(self.selected_pages)
        remaining = self.total_pages - count
        
        if remaining == 0:
            self.message_banner.show_message("Cannot delete all pages! At least one page must remain.", "error")
            return
        
        try:
            reader = PdfReader(self.pdf_path)
            writer = PdfWriter()
            
            # Add pages that should be kept
            for i in range(len(reader.pages)):
                page_num = i + 1
                if page_num not in self.selected_pages:
                    writer.add_page(reader.pages[i])
            
            # Use the output path
            output_path = self.output_path
            
            # Handle existing file
            if os.path.exists(output_path):
                base, ext = os.path.splitext(output_path)
                counter = 1
                while os.path.exists(output_path):
                    output_path = f"{base}_{counter}{ext}"
                    counter += 1
            
            # Save
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            self.message_banner.show_message(
                f"Success! Deleted {count} page{'s' if count != 1 else ''}, saved to {os.path.basename(output_path)}", 
                "success"
            )
            
            # Reload the modified PDF
            self.load_pdf(output_path)
            
        except Exception as e:
            self.message_banner.show_message(f"Failed to process PDF: {str(e)}", "error")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFPageDeleter(root)
    root.mainloop()