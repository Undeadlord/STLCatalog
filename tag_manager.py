"""
Tag Manager for STL Catalog application

This module provides functionality to view, edit, and delete tags.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from database_manager import DatabaseManager

class TagManager:
    """Class for managing tags in the STL Catalog"""
    
    def __init__(self, parent, update_callback=None, current_tags=None, update_ui_callback=None):
        """Initialize the Tag Manager dialog
        
        Args:
            parent: Parent window
            update_callback: Function to call when tags are updated
            current_tags: List of currently selected tags
            update_ui_callback: Function to call to update UI after tag operations
        """
        self.parent = parent
        self.update_callback = update_callback
        self.current_tags = current_tags or []
        self.update_ui_callback = update_ui_callback
        
        # Tracking for tag renaming
        self.renamed_tags = {}  # old_name -> new_name
        
        # Create the dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Tag Manager")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)  # Make it modal
        self.dialog.grab_set()
        self.dialog.minsize(500, 400)
        
        # Load tags from database
        self.load_tags()
        
        # Create UI
        self.create_ui()
        
        # Set a callback for when the dialog is closed
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def load_tags(self):
        """Load tags from database"""
        self.tags = DatabaseManager.collect_all_tags()
        # Sort tags alphabetically
        self.tags.sort()
    
    def create_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            main_frame, 
            text="Manage Tags", 
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 10))
        
        # Instructions
        ttk.Label(
            main_frame,
            text="Select tags to edit or delete. You can also add new tags.",
            wraplength=400
        ).pack(pady=(0, 10))
        
        # Create tag list frame with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create listbox for tags
        self.tag_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.tag_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tag_listbox.bind('<<ListboxSelect>>', self.on_tag_select)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tag_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tag_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Populate tag listbox
        self.update_tag_list()
        
        # Create frame for editing
        edit_frame = ttk.Frame(main_frame)
        edit_frame.pack(fill=tk.X, pady=10)
        
        # Tag name entry
        ttk.Label(edit_frame, text="Tag Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tag_name_var = tk.StringVar()
        self.tag_entry = ttk.Entry(edit_frame, textvariable=self.tag_name_var, width=30)
        self.tag_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Usage count (read-only, informational)
        ttk.Label(edit_frame, text="Usage Count:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.usage_count_var = tk.StringVar(value="0")
        ttk.Label(edit_frame, textvariable=self.usage_count_var).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Add new tag button
        self.add_button = ttk.Button(
            button_frame,
            text="Add New Tag",
            command=self.add_tag,
            width=15
        )
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        # Update selected tag button
        self.update_button = ttk.Button(
            button_frame,
            text="Update Tag",
            command=self.update_tag,
            width=15,
            state=tk.DISABLED
        )
        self.update_button.pack(side=tk.LEFT, padx=5)
        
        # Delete selected tag button
        self.delete_button = ttk.Button(
            button_frame,
            text="Delete Tag",
            command=self.delete_tag,
            width=15,
            state=tk.DISABLED
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.on_close,
            width=15
        )
        close_button.pack(side=tk.RIGHT, padx=5)
    
    def on_close(self):
        """Handle dialog close event"""
        # If any tags were renamed, update the UI
        if self.renamed_tags and self.update_ui_callback:
            self.update_ui_callback(self.renamed_tags)
        
        # Destroy the dialog
        self.dialog.destroy()
    
    def update_tag_list(self):
        """Update the tag listbox with current tags"""
        # Clear listbox
        self.tag_listbox.delete(0, tk.END)
        
        # Refresh tag list from database
        self.load_tags()
        
        # Add tags to listbox
        for tag in self.tags:
            self.tag_listbox.insert(tk.END, tag)
    
    def on_tag_select(self, event):
        """Handle tag selection in listbox"""
        selection = self.tag_listbox.curselection()
        if not selection:
            # Clear entry and disable buttons if no selection
            self.tag_name_var.set("")
            self.usage_count_var.set("0")
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            return
        
        # Get selected tag
        index = selection[0]
        selected_tag = self.tag_listbox.get(index)
        
        # Set tag name in entry field
        self.tag_name_var.set(selected_tag)
        
        # Get usage count
        usage_count = self.get_tag_usage_count(selected_tag)
        self.usage_count_var.set(str(usage_count))
        
        # Enable buttons
        self.update_button.config(state=tk.NORMAL)
        self.delete_button.config(state=tk.NORMAL)
    
    def get_tag_usage_count(self, tag_name):
        """Get the number of files using this tag
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            int: Number of files using this tag
        """
        return DatabaseManager.get_tag_usage_count(tag_name)
    
    def add_tag(self):
        """Add a new tag"""
        tag_name = self.tag_name_var.get().strip()
        
        if not tag_name:
            messagebox.showerror("Error", "Please enter a tag name")
            return
        
        # Check if tag already exists
        if tag_name in self.tags:
            messagebox.showerror("Error", f"Tag '{tag_name}' already exists")
            return
        
        # Add tag to database
        if DatabaseManager.add_tag(tag_name):
            # Update UI
            self.update_tag_list()
            
            # Select the new tag
            try:
                index = self.tags.index(tag_name)
                self.tag_listbox.selection_clear(0, tk.END)
                self.tag_listbox.selection_set(index)
                self.tag_listbox.see(index)
                self.on_tag_select(None)  # Trigger selection event
            except ValueError:
                pass
            
            # Clear entry field
            self.tag_name_var.set("")
            
            # Call update callback if provided
            if self.update_callback:
                self.update_callback()
        else:
            messagebox.showerror("Error", f"Failed to add tag '{tag_name}'")
    
    def update_tag(self):
        """Update the selected tag"""
        selection = self.tag_listbox.curselection()
        if not selection:
            return
        
        # Get selected tag
        index = selection[0]
        old_tag_name = self.tag_listbox.get(index)
        new_tag_name = self.tag_name_var.get().strip()
        
        if not new_tag_name:
            messagebox.showerror("Error", "Please enter a tag name")
            return
        
        if old_tag_name == new_tag_name:
            # No change, just return
            return
        
        # Check if new tag name already exists
        if new_tag_name in self.tags and new_tag_name != old_tag_name:
            messagebox.showerror("Error", f"Tag '{new_tag_name}' already exists")
            return
        
        # Confirm update
        if not messagebox.askyesno("Confirm Update", f"Are you sure you want to rename '{old_tag_name}' to '{new_tag_name}'?"):
            return
        
        # Update tag in database
        if DatabaseManager.update_tag(old_tag_name, new_tag_name):
            # Keep track of renamed tags
            self.renamed_tags[old_tag_name] = new_tag_name
            
            # Update UI
            self.update_tag_list()
            
            # Try to select the updated tag
            try:
                index = self.tags.index(new_tag_name)
                self.tag_listbox.selection_clear(0, tk.END)
                self.tag_listbox.selection_set(index)
                self.tag_listbox.see(index)
                self.on_tag_select(None)  # Trigger selection event
            except ValueError:
                pass
            
            # Call update callback if provided
            if self.update_callback:
                self.update_callback()
                
            # Show a success message
            messagebox.showinfo("Success", f"Tag '{old_tag_name}' has been renamed to '{new_tag_name}'")
        else:
            messagebox.showerror("Error", f"Failed to update tag '{old_tag_name}'")
    
    def delete_tag(self):
        """Delete the selected tag"""
        selection = self.tag_listbox.curselection()
        if not selection:
            return
        
        # Get selected tag
        index = selection[0]
        tag_name = self.tag_listbox.get(index)
        
        # Get usage count
        usage_count = self.get_tag_usage_count(tag_name)
        
        # Warn if tag is in use
        warning_message = f"Are you sure you want to delete the tag '{tag_name}'?"
        if usage_count > 0:
            warning_message += f"\n\nThis tag is currently used by {usage_count} file(s). Deleting it will remove this tag from all files."
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion", warning_message):
            return
        
        # Delete tag from database
        if DatabaseManager.delete_tag(tag_name):
            # Update UI
            self.update_tag_list()
            
            # Clear entry field
            self.tag_name_var.set("")
            self.usage_count_var.set("0")
            
            # Disable buttons
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            
            # Call update callback if provided
            if self.update_callback:
                self.update_callback()
        else:
            messagebox.showerror("Error", f"Failed to delete tag '{tag_name}'")

def open_tag_manager(parent, update_callback=None, current_tags=None, update_ui_callback=None):
    """Open the Tag Manager dialog
    
    Args:
        parent: Parent window
        update_callback: Function to call when tags are updated
        current_tags: List of currently selected tags
        update_ui_callback: Function to call to update UI after tag operations
    """
    TagManager(parent, update_callback, current_tags, update_ui_callback)