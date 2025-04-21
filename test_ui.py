import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os

class ModernSTLCatalogApp:
    def __init__(self, root):
        self.root = root
        self.script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory this script is in
        self.root.title("STL Catalog")
        self.root.geometry("1000x600")
        self.style = ttk.Style(self.root)
        self.set_dark_theme()

        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()

    def set_dark_theme(self):
        self.root.configure(bg="#2e2e2e")
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#2e2e2e")
        self.style.configure("TLabel", background="#2e2e2e", foreground="white", font=("Segoe UI", 10))
        self.style.configure("TButton", background="#3c3f41", foreground="white", padding=6, font=("Segoe UI", 10))
        self.style.map("TButton", background=[("active", "#5c5f61")])

    def create_widgets(self):
        # Top Bar
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="STL Catalog", font=("Segoe UI", 16, "bold"))

        # Button Section
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.add_button(button_frame, "Add STL", self.add_stl)
        self.add_button(button_frame, "Import Folder", self.import_folder)
        self.add_button(button_frame, "Settings", self.open_settings)

        # Placeholder for catalog display
        display_frame = ttk.Frame(self.main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(display_frame, text="[Catalog Content Placeholder]", anchor=tk.CENTER).pack(expand=True)

    def add_button(self, parent, text, command):
        icon_filename = f"{text.lower().replace(' ', '_')}.png"
        icon_path = os.path.join(self.script_dir, "icons", icon_filename)
        print(f"Looking for icon at: {icon_path}")

        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            img = img.resize((16, 16), Image.LANCZOS)
            icon = ImageTk.PhotoImage(img)
            btn = ttk.Button(parent, text=f" {text}", image=icon, compound=tk.LEFT, command=command)
            btn.image = icon  # Keep reference
        else:
            print(f"Icon not found: {icon_path}")
            btn = ttk.Button(parent, text=text, command=command)

        btn.pack(side=tk.LEFT, padx=5)


    def add_stl(self):
        messagebox.showinfo("Add STL", "This would open the add STL dialog.")

    def import_folder(self):
        filedialog.askdirectory(title="Select STL Folder")

    def open_settings(self):
        messagebox.showinfo("Settings", "This would open the settings dialog.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernSTLCatalogApp(root)
    root.mainloop()
