"""
Settings dialog for STL Catalog application
"""
import tkinter as tk
from tkinter import ttk, messagebox

from app_config import save_settings

def open_settings_dialog(parent, settings, export_callback, import_callback):
    """
    Open settings dialog
    
    Args:
        parent: Parent window
        settings: Settings dictionary
        export_callback: Callback function for exporting database
        import_callback: Callback function for importing database
    """
    settings_dialog = tk.Toplevel(parent)
    settings_dialog.title("Settings")
    
    # Force a larger window size - increase height to make sure buttons are visible
    settings_dialog.geometry("500x500")  # Increased from 450 to 500
    settings_dialog.transient(parent)  # Make it modal
    settings_dialog.grab_set()
    settings_dialog.minsize(500, 500)  # Increase minimum size as well
    
    # Create settings content
    content_frame = ttk.Frame(settings_dialog, padding=20)
    content_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(content_frame, text="Application Settings", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    # Notification settings
    notifications_frame = ttk.LabelFrame(content_frame, text="Notifications")
    notifications_frame.pack(fill=tk.X, pady=10)
    
    # Success messages setting
    show_success_var = tk.BooleanVar(value=settings.get("show_success_messages", True))
    ttk.Checkbutton(
        notifications_frame, 
        text="Show success messages when adding/updating items", 
        variable=show_success_var
    ).pack(padx=10, pady=10, anchor="w")
    
    # Confirmation dialog setting
    confirm_delete_var = tk.BooleanVar(value=settings.get("confirm_delete", True))
    ttk.Checkbutton(
        notifications_frame, 
        text="Show confirmation dialog when deleting items", 
        variable=confirm_delete_var
    ).pack(padx=10, pady=10, anchor="w")
    
    # Window settings
    window_frame = ttk.LabelFrame(content_frame, text="Window")
    window_frame.pack(fill=tk.X, pady=10)
    
    # Remember window geometry setting
    remember_window_var = tk.BooleanVar(value=settings.get("remember_window_geometry", False))
    ttk.Checkbutton(
        window_frame,
        text="Remember window size and position",
        variable=remember_window_var
    ).pack(padx=10, pady=10, anchor="w")
    
    # Display current window geometry info
    current_geometry = parent.geometry()
    ttk.Label(
        window_frame,
        text=f"Current window size and position: {current_geometry}"
    ).pack(padx=10, pady=(0, 10), anchor="w")
    
    # Database maintenance section
    db_frame = ttk.LabelFrame(content_frame, text="Database")
    db_frame.pack(fill=tk.X, pady=10)
    
    db_buttons_frame = ttk.Frame(db_frame)
    db_buttons_frame.pack(padx=10, pady=10, fill=tk.X)
    
    ttk.Button(
        db_buttons_frame,
        text="Export Database",
        command=export_callback,
        width=20
    ).pack(side=tk.LEFT, padx=10, pady=5)
    
    ttk.Button(
        db_buttons_frame,
        text="Import Database",
        command=import_callback,
        width=20
    ).pack(side=tk.LEFT, padx=10, pady=5)
    
    # Buttons frame at the bottom with clear separation
    separator = ttk.Separator(content_frame, orient='horizontal')
    separator.pack(fill=tk.X, pady=20)
    
    button_frame = ttk.Frame(content_frame)
    button_frame.pack(fill=tk.X)
    
    def save_and_close():
        # Update settings
        settings["show_success_messages"] = show_success_var.get()
        settings["confirm_delete"] = confirm_delete_var.get()
        settings["remember_window_geometry"] = remember_window_var.get()
        
        # If remember window geometry is enabled, save current geometry
        if remember_window_var.get():
            settings["window_geometry"] = parent.geometry()
        
        # Save settings to file
        save_settings(settings)
        
        # Show confirmation
        messagebox.showinfo("Settings", "Settings saved successfully")
        
        # Close dialog
        settings_dialog.destroy()
    
    # Save button (larger and more prominent)
    save_button = ttk.Button(
        button_frame, 
        text="Save Settings",
        command=save_and_close,
        width=15
    )
    save_button.pack(side=tk.RIGHT, padx=10)
    
    # Cancel button
    ttk.Button(
        button_frame, 
        text="Cancel", 
        command=settings_dialog.destroy,
        width=15
    ).pack(side=tk.RIGHT, padx=10)