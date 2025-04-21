"""
File management operations for STL Catalog
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from database_manager import DatabaseManager

def browse_stl_file(parent, file_path_var, name_var, edit_mode=False):
    """
    Open file dialog to select an STL file
    
    Args:
        parent: Parent window
        file_path_var: StringVar for file path
        name_var: StringVar for file name
        edit_mode: Whether in edit mode (don't auto-set name if in edit mode and name is not empty)
    """
    filepath = filedialog.askopenfilename(
        title="Select STL File",
        filetypes=[("STL Files", "*.stl"), ("All Files", "*.*")]
    )
    
    if filepath:
        file_path_var.set(filepath)
        # Auto-set name from filename without extension if not in edit mode or name is empty
        if not edit_mode or not name_var.get():
            filename = os.path.basename(filepath)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Replace hyphens and underscores with spaces
            clean_name = name_without_ext.replace('-', ' ').replace('_', ' ')
            
            # Remove leading numbers and spaces
            clean_name = clean_name.lstrip('0123456789 ')
            
            # Capitalize the first letter of each word
            clean_name = ' '.join(word.capitalize() for word in clean_name.split())
            
            # If clean_name ended up empty, use original name
            if not clean_name:
                clean_name = name_without_ext.capitalize()
                
            name_var.set(clean_name)

def add_file_to_catalog(file_path, name, tags, settings, update_callback):
    """
    Add a file to the catalog
    
    Args:
        file_path: Path to the STL file
        name: Display name for the file
        tags: List of tags associated with the file
        settings: Settings dictionary
        update_callback: Callback to update UI after operation
        
    Returns:
        bool: True if successful, False otherwise
    """
    file_path = file_path.strip()
    name = name.strip()
    tags = [tag.strip() for tag in tags if tag.strip()]
    
    if not file_path:
        messagebox.showerror("Error", "Please select an STL file")
        return False
        
    if not name:
        messagebox.showerror("Error", "Please enter a name for the STL file")
        return False
        
    # Add to database
    if DatabaseManager.add_or_update_file(None, file_path, name, tags):
        # Show success message if enabled
        if settings.get("show_success_messages", True):
            messagebox.showinfo("Success", f"Added '{name}' to catalog")
            
        # Update UI
        update_callback()
        return True
    else:
        messagebox.showerror("Error", "Failed to add item to catalog")
        return False

def browse_stl_folder(parent, file_path_var, name_var, edit_mode=False):
    """
    Open folder dialog to select a directory containing STL files
    
    Args:
        parent: Parent window
        file_path_var: StringVar for main STL file path
        name_var: StringVar for folder name
        edit_mode: Whether in edit mode
    
    Returns:
        tuple: (folder_path, stl_files)
    """
    folder_path = filedialog.askdirectory(
        title="Select Folder Containing STL Files"
    )
    
    if not folder_path:
        return None, []
        
    # Get all STL files in the folder
    stl_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith('.stl'):
            stl_files.append(os.path.join(folder_path, file))
    
    if not stl_files:
        messagebox.showinfo("No STL Files", "No STL files found in the selected folder.")
        return None, []
    
    # Auto-set name from folder name if not in edit mode or name is empty
    if not edit_mode or not name_var.get():
        folder_name = os.path.basename(folder_path)
        
        # Clean up the folder name
        clean_name = folder_name.replace('-', ' ').replace('_', ' ')
        
        # Remove leading numbers and spaces
        clean_name = clean_name.lstrip('0123456789 ')
        
        # Capitalize the first letter of each word
        clean_name = ' '.join(word.capitalize() for word in clean_name.split())
        
        # If clean_name ended up empty, use original name
        if not clean_name:
            clean_name = folder_name.capitalize()
            
        name_var.set(clean_name)
    
    return folder_path, stl_files


def update_file_in_catalog(file_id, file_path, name, tags, settings, update_callback):
    """
    Update a file in the catalog
    
    Args:
        file_id: Database ID of the file to update
        file_path: Path to the STL file
        name: Display name for the file
        tags: List of tags associated with the file
        settings: Settings dictionary
        update_callback: Callback to update UI after operation
        
    Returns:
        bool: True if successful, False otherwise
    """
    file_path = file_path.strip()
    name = name.strip()
    tags = [tag.strip() for tag in tags if tag.strip()]
    
    if not file_path:
        messagebox.showerror("Error", "Please select an STL file")
        return False
        
    if not name:
        messagebox.showerror("Error", "Please enter a name for the STL file")
        return False
        
    # Update database
    if DatabaseManager.add_or_update_file(file_id, file_path, name, tags):
        # Show success message if enabled
        if settings.get("show_success_messages", True):
            messagebox.showinfo("Success", f"Updated '{name}' in catalog")
            
        # Update UI
        update_callback()
        return True
    else:
        messagebox.showerror("Error", "Failed to update item in catalog")
        return False

def delete_files_from_catalog(file_ids, file_names, settings, update_callback):
    """
    Delete files from the catalog
    
    Args:
        file_ids: List of file IDs to delete
        file_names: List of file names (for confirmation/success messages)
        settings: Settings dictionary
        update_callback: Callback to update UI after operation
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not file_ids:
        return False
    
    # Confirmation dialog if enabled
    if settings.get("confirm_delete", True):
        if len(file_ids) == 1:
            message = f"Are you sure you want to delete '{file_names[0]}'?"
        else:
            message = f"Are you sure you want to delete {len(file_ids)} selected items?"
            
        if not messagebox.askyesno("Confirm Delete", message):
            return False
    
    # Delete from database
    if DatabaseManager.delete_files(file_ids):
        # Show success message if enabled
        if settings.get("show_success_messages", True):
            if len(file_ids) == 1:
                messagebox.showinfo("Success", f"Deleted '{file_names[0]}' from catalog")
            else:
                messagebox.showinfo("Success", f"Deleted {len(file_ids)} items from catalog")
        
        # Update UI
        update_callback()
        return True
    else:
        messagebox.showerror("Error", "Failed to delete items from catalog")
        return False

def export_database():
    """
    Export the database to a JSON file
    
    Returns:
        str: Path to exported file, or None if canceled/failed
    """
    export_path = filedialog.asksaveasfilename(
        title="Export Database",
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    
    if not export_path:
        return None
        
    if DatabaseManager.export_to_json(export_path):
        messagebox.showinfo("Export Complete", f"Successfully exported database to {export_path}")
        return export_path
    else:
        messagebox.showerror("Export Error", "Failed to export database")
        return None

def import_database(update_callback):
    """
    Import data from a JSON file
    
    Args:
        update_callback: Callback to update UI after operation
        
    Returns:
        bool: True if successful, False otherwise
    """
    import_path = filedialog.askopenfilename(
        title="Import Database",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    
    if not import_path:
        return False
        
    # Ask if user wants to merge or replace
    result = messagebox.askyesno(
        "Import Confirmation",
        "Do you want to merge with existing data or replace it?\n\n" +
        "Yes = Merge (keep existing entries)\n" +
        "No = Replace (delete all existing entries)"
    )
    
    # Import data
    if DatabaseManager.import_from_json(import_path, replace=not result):
        # Update UI
        update_callback()
        
        messagebox.showinfo("Import Complete", "Successfully imported data")
        return True
    else:
        messagebox.showerror("Import Error", "Failed to import data")
        return False