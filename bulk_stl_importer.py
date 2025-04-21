import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import queue
import time
import importlib.util
import sqlite3

from app_config import DB_FILE, DEFAULT_TAGS, load_settings, save_settings
from database_manager import DatabaseManager

# Diagnostic helper

def print_diagnostic_info():
    print("\n===== DIAGNOSTIC INFORMATION =====")
    print(f"Python version: {sys.version}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

    print("\nPython path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")

    print("\nChecking for required modules:")
    for module_name in ['app_config', 'database_manager']:
        try:
            module = importlib.import_module(module_name)
            print(f"  {module_name}: Found at {module.__file__}")
        except ImportError:
            print(f"  {module_name}: Not found")
        except Exception as e:
            print(f"  {module_name}: Error - {str(e)}")

    try:
        print(f"\nDatabase file: {DB_FILE}")
        print(f"  Exists: {os.path.exists(DB_FILE)}")
        if os.path.exists(DB_FILE):
            print(f"  Size: {os.path.getsize(DB_FILE)} bytes")
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"  Tables: {[table[0] for table in tables]}")
    except Exception as e:
        print(f"  Database error: {e}")

    print("===== END DIAGNOSTIC INFORMATION =====\n")


# Safe STL folder loader

def fallback_browse_stl_folder():
    folder = filedialog.askdirectory(title="Select STL Folder")
    if not folder:
        return folder, []
    stls = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.stl')]
    return folder, stls


try:
    from ui.file_manager import browse_stl_folder
except ImportError:
    try:
        from UI.file_manager import browse_stl_folder
    except ImportError:
        browse_stl_folder = fallback_browse_stl_folder


class BulkImportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STL Catalog - Bulk Import")
        self.queue = queue.Queue()
        self.settings = load_settings()

        self.global_tags = []
        self.tag_vars = {}
        self.folders_data = []
        self.processing = False

        self.init_ui()
        try:
            DatabaseManager.create_database()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

        self.all_tags = DatabaseManager.collect_all_tags()
        self.render_tag_checkboxes()
        self.log("Bulk STL Importer ready.")

    def init_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Folder + Scan
        folder_frame = ttk.LabelFrame(frame, text="Top-Level Folder")
        folder_frame.pack(fill=tk.X)
        self.folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Scan", command=self.scan_folders).pack(side=tk.LEFT)

        # Tag section
        tag_frame = ttk.LabelFrame(frame, text="Tags")
        tag_frame.pack(fill=tk.X, pady=5)
        self.tag_box = ttk.Frame(tag_frame)
        self.tag_box.pack(fill=tk.X)

        # Options
        self.auto_select_var = tk.BooleanVar(value=True)
        self.prompt_main_file_var = tk.BooleanVar(value=True)

        options = ttk.LabelFrame(frame, text="Options")
        options.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(options, text="Auto-select first STL", variable=self.auto_select_var).pack(anchor=tk.W)
        ttk.Checkbutton(options, text="Prompt for main file when multiple", variable=self.prompt_main_file_var).pack(anchor=tk.W)

        # Folders list
        self.folder_listbox = tk.Listbox(frame, height=6)
        self.folder_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        # Progress + Log
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(frame, variable=self.progress_var, maximum=100).pack(fill=tk.X)
        self.log_area = ScrolledText(frame, height=10, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=5)
        ttk.Button(btns, text="Start Import", command=self.start_import).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btns, text="Close", command=self.root.destroy).pack(side=tk.RIGHT)

    def render_tag_checkboxes(self):
        for widget in self.tag_box.winfo_children():
            widget.destroy()
        self.tag_vars.clear()
        for i, tag in enumerate(sorted(self.all_tags)):
            var = tk.BooleanVar()
            self.tag_vars[tag] = var
            ttk.Checkbutton(self.tag_box, text=tag, variable=var).grid(row=i//3, column=i%3, sticky='w')

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.scan_folders()

    def scan_folders(self):
        base = self.folder_var.get().strip()
        if not base or not os.path.isdir(base):
            messagebox.showerror("Invalid Folder", "Please select a valid directory.")
            return

        self.folders_data.clear()
        self.folder_listbox.delete(0, tk.END)

        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if not os.path.isdir(path):
                continue
            stls = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.stl')]
            if not stls:
                continue
            clean_name = ' '.join(w.capitalize() for w in name.replace('_', ' ').replace('-', ' ').split())
            self.folders_data.append((path, stls, clean_name))
            self.folder_listbox.insert(tk.END, f"{clean_name} ({len(stls)} STLs)")

        self.log(f"Scan complete: {len(self.folders_data)} folders ready.")

    def log(self, msg):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def start_import(self):
        self.global_tags = [tag for tag, var in self.tag_vars.items() if var.get()]
        if not self.folders_data:
            messagebox.showwarning("No Folders", "Nothing to import.")
            return
        self.processing = True
        threading.Thread(target=self.import_worker, daemon=True).start()
        self.root.after(100, self.check_queue)

    def import_worker(self):
        total = len(self.folders_data)
        for i, (path, stls, name) in enumerate(self.folders_data):
            if not self.processing:
                break
            main = stls[0] if stls else None
            others = stls[1:] if len(stls) > 1 else []
            if self.prompt_main_file_var.get() and len(stls) > 1:
                main = self.prompt_for_main_file(name, stls)
                if not main:
                    self.queue.put(("log", f"Skipping {name}: No main file selected."))
                    continue
                others = [s for s in stls if s != main]
            result = DatabaseManager.add_or_update_file_with_related(None, main, others, name, self.global_tags)
            self.queue.put(("log", f"{name}: {'Imported' if result else 'Failed'}"))
            self.queue.put(("progress", ((i + 1) / total) * 100))
        self.queue.put(("log", "Import complete."))
        self.processing = False

    def check_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "log":
                    self.log(msg[1])
                elif msg[0] == "progress":
                    self.progress_var.set(msg[1])
        except queue.Empty:
            if self.processing:
                self.root.after(100, self.check_queue)

    def prompt_for_main_file(self, folder_name, stl_files):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Select Main File - {folder_name}")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select the main STL file:").pack(pady=10)
        listbox = tk.Listbox(dialog)
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        for f in stl_files:
            listbox.insert(tk.END, os.path.basename(f))
        listbox.selection_set(0)

        selected = [None]

        def confirm():
            idx = listbox.curselection()
            if idx:
                selected[0] = stl_files[idx[0]]
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btns = ttk.Frame(dialog)
        btns.pack(pady=10)
        ttk.Button(btns, text="Select", command=confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btns, text="Cancel", command=cancel).pack(side=tk.RIGHT)

        self.root.wait_window(dialog)
        return selected[0]


if __name__ == "__main__":
    root = tk.Tk()
    print_diagnostic_info()
    BulkImportApp(root)
    root.mainloop()
