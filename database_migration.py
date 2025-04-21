"""
Database Migration Script for STL Catalog

This script updates the database structure to support multi-part STL files.
Run this script once to update your existing database.
"""
import os
import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

# Default database file name
DEFAULT_DB_FILE = "stl_catalog.db"

def find_database_file():
    """
    Attempt to find the database file in common locations
    
    Returns:
        str: Path to database file or None if not found
    """
    # First check current directory
    if os.path.exists(DEFAULT_DB_FILE):
        return os.path.abspath(DEFAULT_DB_FILE)
    
    # Check parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_path = os.path.join(parent_dir, DEFAULT_DB_FILE)
    if os.path.exists(parent_path):
        return parent_path
    
    # Check in common app directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_dirs = [
        script_dir,                              # Script directory
        os.path.join(script_dir, 'data'),        # Data subdirectory
        os.path.join(script_dir, 'db'),          # DB subdirectory
        os.path.dirname(script_dir)              # Parent directory
    ]
    
    for directory in app_dirs:
        db_path = os.path.join(directory, DEFAULT_DB_FILE)
        if os.path.exists(db_path):
            return db_path
            
    return None

def migrate_database_for_multi_part(db_file):
    """Add necessary tables and columns for multi-part STL support
    
    Args:
        db_file: Path to the database file
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if database file exists
    if not os.path.exists(db_file):
        print(f"Database file {db_file} not found.")
        return False
    
    print(f"Using database file: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Check if is_multi_part column exists
        cursor.execute("PRAGMA table_info(stl_files)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add is_multi_part column if it doesn't exist
        if 'is_multi_part' not in columns:
            print("Adding is_multi_part column to stl_files table...")
            cursor.execute("ALTER TABLE stl_files ADD COLUMN is_multi_part BOOLEAN DEFAULT 0")
        else:
            print("is_multi_part column already exists in stl_files table.")
        
        # Check if related_files table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='related_files'")
        if not cursor.fetchone():
            print("Creating related_files table...")
            # Create related files table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS related_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                main_file_id INTEGER,
                file_path TEXT,
                FOREIGN KEY (main_file_id) REFERENCES stl_files (id) ON DELETE CASCADE
            )
            ''')
        else:
            print("related_files table already exists.")
        
        # Commit the transaction
        conn.commit()
        print("Database migrated successfully for multi-part STL support.")
        return True
        
    except sqlite3.Error as e:
        # Roll back any changes if error occurs
        conn.rollback()
        print(f"Database Migration Error: {e}")
        return False
    finally:
        # Close the connection
        conn.close()

def create_ui():
    """Create a simple UI for the migration script"""
    root = tk.Tk()
    root.title("STL Catalog Database Migration")
    root.geometry("500x350")
    
    # Create main frame with padding
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    ttk.Label(
        main_frame, 
        text="STL Catalog Database Migration", 
        font=("Arial", 16, "bold")
    ).pack(pady=(0, 20))
    
    # Database file selection
    file_frame = ttk.Frame(main_frame)
    file_frame.pack(fill=tk.X, pady=5)
    
    db_path_var = tk.StringVar()
    
    # Try to find database automatically
    db_path = find_database_file()
    if db_path:
        db_path_var.set(db_path)
    
    ttk.Label(file_frame, text="Database File:").pack(side=tk.LEFT)
    entry = ttk.Entry(file_frame, textvariable=db_path_var, width=50)
    entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def browse_db():
        filename = filedialog.askopenfilename(
            title="Select STL Catalog Database",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        if filename:
            db_path_var.set(filename)
    
    ttk.Button(file_frame, text="Browse", command=browse_db).pack(side=tk.RIGHT)
    
    # Information text
    info_text = tk.Text(main_frame, height=6, wrap=tk.WORD)
    info_text.insert(tk.END, 
        "This utility will update your STL Catalog database to support multi-part STL files.\n\n"
        "The migration will add a new column and table to your existing database without losing any data.\n\n"
        "Click 'Start Migration' to begin the update process."
    )
    info_text.config(state=tk.DISABLED)
    info_text.pack(fill=tk.X, pady=10)
    
    # Result label
    result_var = tk.StringVar()
    result_label = ttk.Label(main_frame, textvariable=result_var, font=("Arial", 10))
    result_label.pack(pady=10)
    
    # Progress bar
    progress = ttk.Progressbar(main_frame, mode="indeterminate")
    progress.pack(fill=tk.X, pady=10)
    
    def start_migration():
        """Execute the migration with progress indication"""
        db_file = db_path_var.get()
        
        if not db_file:
            messagebox.showerror("Error", "Please select a database file")
            return
            
        if not os.path.exists(db_file):
            messagebox.showerror("Error", f"Database file not found: {db_file}")
            return
        
        # Disable button during migration
        migrate_button.config(state=tk.DISABLED)
        progress.start()
        result_var.set("Migration in progress...")
        
        # Update UI
        root.update_idletasks()
        
        # Run migration
        success = migrate_database_for_multi_part(db_file)
        
        # Stop progress and update result
        progress.stop()
        
        if success:
            result_var.set("Migration completed successfully!")
            messagebox.showinfo("Migration Complete", 
                "The database has been successfully updated to support multi-part STL files.")
        else:
            result_var.set("Migration failed. See console for details.")
            messagebox.showerror("Migration Failed", 
                "The database migration failed. Please check the console for error details.")
        
        # Re-enable button
        migrate_button.config(state=tk.NORMAL)
    
    # Create button
    migrate_button = ttk.Button(
        main_frame,
        text="Start Migration",
        command=start_migration,
        width=20
    )
    migrate_button.pack(pady=10)
    
    # Close button
    ttk.Button(
        main_frame,
        text="Close",
        command=root.destroy,
        width=20
    ).pack(pady=5)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Start UI
    root.mainloop()

if __name__ == "__main__":
    print("STL Catalog Database Migration Tool")
    print("===================================")
    
    # Check if --console flag is provided
    if '--console' in sys.argv:
        # Run in console mode
        # Get database file path
        db_path = None
        
        # Check if a path is provided as an argument
        if len(sys.argv) > 2:
            potential_path = sys.argv[2]
            if os.path.exists(potential_path):
                db_path = potential_path
        
        # Try to find database automatically if not provided
        if not db_path:
            db_path = find_database_file()
        
        if db_path:
            migrate_database_for_multi_part(db_path)
        else:
            print("Database file not found. Please specify the path to the database file:")
            print("python migrate_database.py --console path/to/stl_catalog.db")
    else:
        # Run with GUI
        create_ui()