"""
Main application class for STL Catalog
"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import os

from app_config import DEFAULT_TAGS, load_settings, save_settings
from database_manager import DatabaseManager
from utils.geometry import apply_window_geometry, save_window_geometry
from ui.settings_dialog import open_settings_dialog
from ui.file_manager import (
    browse_stl_file, browse_stl_folder, add_file_to_catalog, update_file_in_catalog, 
    delete_files_from_catalog, export_database, import_database
)
from ui.viewer_integration import view_selected_stl
from tag_manager import open_tag_manager

class STLCatalogApp:
    """Main application class for STL Catalog"""
    
    def __init__(self, root):
        """
        Initialize the application
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("STL Catalog")
        
        # Load settings
        self.settings = load_settings()
        
        # First apply the default geometry to ensure a reasonable size
        self.root.geometry("800x600")
        
        # Center window on screen before applying saved geometry
        self.center_window()
        
        # Apply saved window geometry if enabled
        if self.settings.get("remember_window_geometry", False):
            # Use saved geometry
            geometry_str = self.settings.get("window_geometry", "")
            if geometry_str:
                # Delay to ensure window is fully created
                self.root.after(100, lambda: self.root.geometry(geometry_str))
                
            # Check for maximized state
            if self.settings.get("window_maximized", False):
                # Delay to ensure window is fully created before maximizing
                self.root.after(200, self.maximize_window)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Ensure database exists
        DatabaseManager.create_database()
        
        # Get all tags
        self.all_tags = DatabaseManager.collect_all_tags()

        # List to store related STL files when browsing a folder
        self.related_stl_files = []
        
        # Tag checkbox variables dictionary
        self.tag_vars = {}
        
        # Edit mode tracking
        self.edit_mode = False
        self.editing_file_id = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create UI components
        self.create_ui()
        
        # Migrate JSON data if it exists and database is empty
        DatabaseManager.migrate_json_if_needed()
    
    def on_window_close(self):
        """Handle window close event"""
        # Check if window is maximized - use platform-specific approaches
        is_maximized = False
        
        if sys.platform == "win32":
            # Windows-specific approach
            is_maximized = self.root.wm_state() == 'zoomed'
        else:
            # Linux/macOS approach - safely check if the attribute exists
            try:
                is_maximized = bool(self.root.attributes('-zoomed'))
            except tk.TclError:
                # Attribute not supported, try alternative method
                try:
                    is_maximized = bool(self.root.attributes('-fullscreen'))
                except tk.TclError:
                    # Neither attribute works, default to False
                    is_maximized = False
        
        # Save maximized state in settings
        self.settings["window_maximized"] = is_maximized
        
        # Only save geometry if not maximized (otherwise it can cause issues)
        if not is_maximized:
            # Save window geometry if enabled
            save_window_geometry(self.root, self.settings)
        
        # Save settings
        save_settings(self.settings)
        
        # Close window
        self.root.destroy()
    
    def center_window(self):
        """Center the window on the screen"""
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        width = 800  # Default width
        height = 600  # Default height
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set the position
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def maximize_window(self):
        """Maximize the window based on platform"""
        if sys.platform == "win32":
            # Windows approach
            self.root.wm_state('zoomed')
        else:
            # Linux/macOS approach - try different methods
            try:
                self.root.attributes('-zoomed', True)
            except tk.TclError:
                # If -zoomed is not supported, try -fullscreen
                try:
                    self.root.attributes('-fullscreen', True)
                except tk.TclError:
                    # If neither works, just make it big
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    def create_ui(self):
        """Create the user interface"""
        # Top bar for settings
        top_bar = ttk.Frame(self.main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        # App title on left
        ttk.Label(top_bar, text="STL Catalog", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Settings button on right
        settings_button = ttk.Button(top_bar, text="⚙️ Settings", command=self.open_settings)
        settings_button.pack(side=tk.RIGHT)
        
        # Main content area
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - File selection and metadata input
        left_panel = ttk.Frame(content_frame, padding="5")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Form label (changes based on edit mode)
        self.form_label_var = tk.StringVar(value="Add STL File")
        self.form_label = ttk.Label(left_panel, textvariable=self.form_label_var, font=("Arial", 14, "bold"))
        self.form_label.pack(pady=(0, 10))
        
        # File selection
        # Find the file selection section - after the file selection buttons, add the Quick Render button
        file_frame = ttk.Frame(left_panel)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(file_frame, text="STL File:").pack(side=tk.LEFT)
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse File", command=self.browse_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Browse Folder", command=self.browse_folder).pack(side=tk.LEFT)
        
        # Add the Quick Render button - initially disabled
        self.quick_render_button = ttk.Button(
            file_frame,
            text="🔍 Quick Render",
            command=self.quick_render,
            state=tk.DISABLED  # Initially disabled until a file is selected
        )
        self.quick_render_button.pack(side=tk.LEFT, padx=5)
        
        # Add a trace to the file_path_var to enable/disable the Quick Render button
        self.file_path_var.trace_add("write", self.update_quick_render_button_state)
        
        # Name input
        name_frame = ttk.Frame(left_panel)
        name_frame.pack(fill=tk.X, pady=5)
        
        self.name_var = tk.StringVar()
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        ttk.Entry(name_frame, textvariable=self.name_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Tags input
        tags_frame = ttk.Frame(left_panel)
        tags_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(tags_frame, text="Tags:").pack(side=tk.LEFT)
        self.tags_var = tk.StringVar()
        ttk.Entry(tags_frame, textvariable=self.tags_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(tags_frame, text="(comma separated)").pack(side=tk.LEFT)
        
        # Dynamic tags frame
        self.tags_frame = ttk.LabelFrame(left_panel, text="Tags")
        self.tags_frame.pack(fill=tk.X, pady=10)
        
        # Add controls for tags
        tag_control_frame = ttk.Frame(self.tags_frame)
        tag_control_frame.pack(fill=tk.X, pady=5)
        
        self.new_tag_var = tk.StringVar()
        ttk.Label(tag_control_frame, text="New Tag:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(tag_control_frame, textvariable=self.new_tag_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(tag_control_frame, text="Add Tag", command=self.add_new_tag).pack(side=tk.LEFT, padx=5)
        
        # Add Tag Manager button
        ttk.Button(
            tag_control_frame, 
            text="Tag Manager", 
            command=self.open_tag_manager
        ).pack(side=tk.RIGHT, padx=5)
        
        # Create the tags checkboxes container
        self.tag_checkboxes_frame = ttk.Frame(self.tags_frame)
        self.tag_checkboxes_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create checkboxes for existing tags
        self.create_tag_checkboxes()
        
        # Buttons frame
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.pack(pady=10)
        
        # Add/Update button (text changes based on mode)
        self.submit_button_var = tk.StringVar(value="Add to Catalog")
        self.submit_button = ttk.Button(
            buttons_frame, 
            textvariable=self.submit_button_var,
            command=self.submit_entry
        )
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # Cancel edit button (only shown in edit mode)
        self.cancel_button = ttk.Button(
            buttons_frame,
            text="Cancel",
            command=self.cancel_edit,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Catalog display
        right_panel = ttk.Frame(content_frame, padding="5")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_panel, text="Catalog", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Search frame
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.update_file_list())
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Control buttons for catalog entries
        catalog_controls_frame = ttk.Frame(right_panel)
        catalog_controls_frame.pack(fill=tk.X, pady=5)
        
        self.edit_button = ttk.Button(
            catalog_controls_frame,
            text="Edit",
            command=self.edit_selected,
            state=tk.DISABLED
        )
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(
            catalog_controls_frame,
            text="Delete",
            command=self.delete_selected,
            state=tk.DISABLED
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # File listbox with scrollbar
        list_frame = ttk.Frame(right_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.file_listbox = tk.Listbox(list_frame, width=40, height=15, selectmode=tk.EXTENDED)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.file_listbox.bind('<Double-1>', self.on_file_double_click)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Details area
        self.details_frame = ttk.LabelFrame(right_panel, text="Details")
        self.details_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create layout with text area and buttons
        details_layout = ttk.Frame(self.details_frame)
        details_layout.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Button area at the bottom
        button_area = ttk.Frame(details_layout)
        button_area.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # Create View STL button (initially disabled)
        self.view_button = ttk.Button(
            button_area,
            text="View STL",
            command=self.view_selected_stl,
            state=tk.DISABLED  # Start disabled
        )
        self.view_button.pack(side=tk.RIGHT, padx=5)

        # Details text area above the button
        self.details_text = ScrolledText(details_layout, width=40, height=10, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        self.details_text.config(state=tk.DISABLED)
        
        # Update file list
        self.update_file_list()
    
    def update_quick_render_button_state(self, *args):
        """Enable or disable the Quick Render button based on file path"""
        file_path = self.file_path_var.get().strip()
        
        if file_path and os.path.exists(file_path) and file_path.lower().endswith('.stl'):
            self.quick_render_button.config(state=tk.NORMAL)
        else:
            self.quick_render_button.config(state=tk.DISABLED)

    def quick_render(self):
        """Show a quick preview of the current STL file"""
        file_path = self.file_path_var.get().strip()
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid STL file first")
            return
        
        # Use the direct launcher if it's available
        try:
            # First check if our launcher is available
            from ui.viewer_integration import launch_direct_viewer
            launch_direct_viewer(file_path)
        except Exception as e:
            # In case of any error, show the message and print the details
            messagebox.showerror("Error", f"Failed to launch STL viewer: {str(e)}")
            print(f"Error launching STL viewer: {e}")

    def browse_folder(self):
        """Open folder dialog to select a folder containing STL files"""
        folder_path, stl_files = browse_stl_folder(self.root, self.file_path_var, self.name_var, self.edit_mode)
        
        if folder_path and stl_files:
            # Store the list of related files
            self.related_stl_files = stl_files
            
            # If we have files, select the first one as the main file by default
            if stl_files:
                self.file_path_var.set(stl_files[0])
                
                # Show the selection dialog for the main file
                self.select_main_stl_file()

    def select_main_stl_file(self):
        """Open a dialog to select the main STL file from the folder"""
        if not hasattr(self, 'related_stl_files') or not self.related_stl_files:
            return
        
        # Create a dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Main STL File")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create content
        ttk.Label(dialog, text="Select the main STL file:", font=("Arial", 12)).pack(pady=10)
        
        # Create file listbox with scrollbar
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        file_listbox = tk.Listbox(list_frame, width=80, height=15)
        file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Fill listbox with file names
        for file_path in self.related_stl_files:
            file_name = os.path.basename(file_path)
            file_listbox.insert(tk.END, file_name)
        
        # Select the first file by default
        if self.related_stl_files:
            file_listbox.selection_set(0)
        
        # Create button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_select():
            selection = file_listbox.curselection()
            if selection:
                index = selection[0]
                if index < len(self.related_stl_files):
                    self.file_path_var.set(self.related_stl_files[index])
                    dialog.destroy()
            else:
                dialog.destroy()
        
        ttk.Button(button_frame, text="Select", command=on_select).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def browse_file(self):
        """Open file dialog to select an STL file"""
        browse_stl_file(self.root, self.file_path_var, self.name_var, self.edit_mode)
    
    def open_settings(self):
        """Open settings dialog"""
        open_settings_dialog(
            self.root, 
            self.settings, 
            self.export_database_callback, 
            self.import_database_callback
        )
        
    def open_tag_manager(self):
        """Open tag manager dialog"""
        # Get current tags from the tags text box
        current_tags = [tag.strip() for tag in self.tags_var.get().split(',') if tag.strip()]
        
        # Open tag manager dialog
        open_tag_manager(
            self.root, 
            self.update_after_database_change,
            current_tags,
            self.handle_tag_updates
        )

    def create_tag_checkboxes(self):
        """Create checkboxes for all known tags in alphabetical order"""
        # Clear existing checkboxes
        for widget in self.tag_checkboxes_frame.winfo_children():
            widget.destroy()
        
        # Create a new set of checkboxes
        row = 0
        col = 0
        max_cols = 3  # Number of checkbox columns
        
        # Sort tags alphabetically
        sorted_tags = sorted(self.all_tags)
        
        for tag in sorted_tags:
            if tag not in self.tag_vars:
                self.tag_vars[tag] = tk.BooleanVar(value=False)
            
            cb = ttk.Checkbutton(
                self.tag_checkboxes_frame, 
                text=tag, 
                variable=self.tag_vars[tag],
                command=lambda t=tag: self.update_tags_from_checkboxes()
            )
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def handle_tag_updates(self, renamed_tags):
        """Handle tag updates from the Tag Manager
        
        Args:
            renamed_tags: Dictionary of old_name -> new_name for renamed tags
        """
        if not renamed_tags:
            return
                
        # Get current tags from the tags text box
        current_tags = [tag.strip() for tag in self.tags_var.get().split(',') if tag.strip()]
        
        # Replace renamed tags
        updated_tags = []
        for tag in current_tags:
            if tag in renamed_tags:
                updated_tags.append(renamed_tags[tag])
            else:
                updated_tags.append(tag)
        
        # Update the tags text box
        self.tags_var.set(', '.join(updated_tags))
        
        # Refresh all tags
        self.all_tags = DatabaseManager.collect_all_tags()
        self.create_tag_checkboxes()
        
        # Update checkbox states based on the updated tags
        for tag, var in self.tag_vars.items():
            var.set(tag in updated_tags)


    def update_tags_from_checkboxes(self):
        """Update tags input field based on checkbox states"""
        selected_tags = []
        
        for tag, var in self.tag_vars.items():
            if var.get():
                selected_tags.append(tag)
                
        self.tags_var.set(', '.join(selected_tags))
    
    def update_checkboxes_from_tags(self):
        """Update checkboxes based on tags input field"""
        # Reset all checkboxes
        for tag, var in self.tag_vars.items():
            var.set(False)
            
        # Get current tags from input field
        current_tags = [t.strip() for t in self.tags_var.get().split(',') if t.strip()]
        
        # Set checkboxes for matching tags
        for tag in current_tags:
            if tag in self.tag_vars:
                self.tag_vars[tag].set(True)
    
    def add_new_tag(self):
        """Add a new tag to the list of available tags"""
        new_tag = self.new_tag_var.get().strip()
        
        if not new_tag:
            return
            
        # Add to database
        if DatabaseManager.add_tag(new_tag):
            # Update local list
            if new_tag not in self.all_tags:
                self.all_tags.append(new_tag)
                self.all_tags.sort()  # Keep alphabetical order
                self.create_tag_checkboxes()
                
                # Select the new tag
                self.tag_vars[new_tag].set(True)
                self.update_tags_from_checkboxes()
                
            # Clear the input field
            self.new_tag_var.set("")
    
    def submit_entry(self):
        """Add or update entry in catalog based on current mode"""
        if self.edit_mode:
            self.update_in_catalog()
        else:
            self.add_to_catalog()
    
    def add_to_catalog(self):
        """Add current file to catalog"""
        file_path = self.file_path_var.get().strip()
        name = self.name_var.get().strip()
        tags = [tag.strip() for tag in self.tags_var.get().split(',') if tag.strip()]
        
        if not file_path:
            messagebox.showerror("Error", "Please select an STL file")
            return
            
        if not name:
            messagebox.showerror("Error", "Please enter a name for the STL file")
            return
        
        # Get related files
        related_files = []
        if hasattr(self, 'related_stl_files'):
            related_files = self.related_stl_files
        
        # Add to database with related files
        if DatabaseManager.add_or_update_file_with_related(None, file_path, related_files, name, tags):
            # Show success message if enabled
            if self.settings.get("show_success_messages", True):
                messagebox.showinfo("Success", f"Added '{name}' to catalog")
                
            # Clear inputs and update UI
            self.file_path_var.set("")
            self.name_var.set("")
            self.tags_var.set("")
            self.related_stl_files = []
            
            # Reset all checkboxes
            for tag, var in self.tag_vars.items():
                var.set(False)
                
            # Update UI
            self.update_file_list()
            self.all_tags = DatabaseManager.collect_all_tags()
            self.create_tag_checkboxes()
        else:
            messagebox.showerror("Error", "Failed to add item to catalog")
    
    def update_in_catalog(self):
        """Update the current file in the catalog"""
        if not self.edit_mode or self.editing_file_id is None:
            return
                
        file_path = self.file_path_var.get().strip()
        name = self.name_var.get().strip()
        tags = [tag.strip() for tag in self.tags_var.get().split(',') if tag.strip()]
        
        if not file_path:
            messagebox.showerror("Error", "Please select an STL file")
            return
            
        if not name:
            messagebox.showerror("Error", "Please enter a name for the STL file")
            return
        
        # Get related files
        related_files = []
        if hasattr(self, 'related_stl_files'):
            related_files = self.related_stl_files
        
        # Update database with related files
        if DatabaseManager.add_or_update_file_with_related(self.editing_file_id, file_path, related_files, name, tags):
            # Show success message if enabled
            if self.settings.get("show_success_messages", True):
                messagebox.showinfo("Success", f"Updated '{name}' in catalog")
                
            # Exit edit mode
            self.exit_edit_mode()
                    
            # Update UI
            self.update_file_list()
        else:
            messagebox.showerror("Error", "Failed to update item in catalog")

    
    def update_file_list(self):
        """Update the file listbox with filtered catalog items"""
        self.file_listbox.delete(0, tk.END)
        
        search_term = self.search_var.get()
        
        # Get files from database
        files = DatabaseManager.get_filtered_files(search_term)
        
        # We'll store mapping of index -> file_id
        self.listbox_mapping = {}
        
        for index, file_data in files.items():
            self.file_listbox.insert(tk.END, file_data['name'])
            # Store file_id in our mapping
            self.listbox_mapping[index] = file_data['id']
        
        # Disable edit/delete buttons if no selection
        self.edit_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        self.view_button.config(state=tk.DISABLED)
    
    def update_after_database_change(self):
        """Update UI after database changes"""
        # Refresh tags list
        self.all_tags = DatabaseManager.collect_all_tags()
        self.create_tag_checkboxes()
        
        # Update file list
        self.update_file_list()
    
    def on_file_select(self, event):
        """Display details for the selected file and enable/disable buttons"""
        selection = self.file_listbox.curselection()
        if not selection:
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            self.view_button.config(state=tk.DISABLED)
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.config(state=tk.DISABLED)
            return
                    
        # Enable buttons for single selection
        if len(selection) == 1:
            self.edit_button.config(state=tk.NORMAL)
        else:
            self.edit_button.config(state=tk.DISABLED)
                    
        # Enable delete button for any selection
        self.delete_button.config(state=tk.NORMAL)
                    
        # Get the file_id from our mapping for the first selected item
        index = selection[0]
        if index not in self.listbox_mapping:
            return
                    
        file_id = self.listbox_mapping[index]
                
        # Get file details from database using the new method
        details = DatabaseManager.get_file_details_with_related(file_id)
                
        if not details:
            return
                    
        # Update details text
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
                
        details_text = f"Name: {details['name']}\n\n"
        details_text += f"Main File: {os.path.basename(details['file_path'])}\n\n"
        
        # Add related files if multi-part
        if details['is_multi_part'] and details['related_files']:
            details_text += "Related Files:\n"
            for i, related_file in enumerate(details['related_files']):
                details_text += f"  {i+1}. {os.path.basename(related_file)}\n"
            details_text += "\n"
        
        details_text += f"Date Added: {details['date_added']}\n\n"
        details_text += f"Tags: {details['tags']}"
                
        self.details_text.insert(tk.INSERT, details_text)
        self.details_text.config(state=tk.DISABLED)
                
        # Enable view button if file exists and selection is single
        if len(selection) == 1 and os.path.exists(details['file_path']):
            self.view_button.config(state=tk.NORMAL)
        else:
            # Disable the view button for multiple selections
            self.view_button.config(state=tk.DISABLED)
    
    def view_selected_stl(self):
        """Open the STL viewer for the selected file"""
        selection = self.file_listbox.curselection()
        if not selection or len(selection) != 1:
            return
                
        index = selection[0]
        if index not in self.listbox_mapping:
            return
                
        file_id = self.listbox_mapping[index]
        
        # Use the new method that includes related files
        details = DatabaseManager.get_file_details_with_related(file_id)
        
        if not details:
            return
            
        # Use the viewer integration module to view the main file
        view_selected_stl(self.root, details)

    def on_file_double_click(self, event):
        """Handle double-click on file entry to edit it"""
        selection = self.file_listbox.curselection()
        if not selection or len(selection) != 1:
            return
            
        # If already in edit mode, do nothing
        if self.edit_mode:
            return
            
        # Start edit mode for the selected file
        self.edit_selected()
    
    def edit_selected(self):
        """Load the selected file for editing"""
        selection = self.file_listbox.curselection()
        if not selection or len(selection) != 1:
            return
                
        # If already in edit mode, do nothing
        if self.edit_mode:
            return
                
        # Get the file_id from our mapping
        index = selection[0]
        if index not in self.listbox_mapping:
            return
                
        file_id = self.listbox_mapping[index]
        
        # Get file details from database using the new method
        details = DatabaseManager.get_file_details_with_related(file_id)
        
        if not details:
            return
                
        # Enter edit mode
        self.enter_edit_mode(file_id)
        
        # Populate form with data
        self.file_path_var.set(details['file_path'])
        self.name_var.set(details['name'])
        
        # Set related files
        self.related_stl_files = details['related_files']
        if details['file_path'] not in self.related_stl_files:
            self.related_stl_files.append(details['file_path'])
        
        # Set tags
        self.tags_var.set(details['tags'])
        
        # Update checkboxes
        self.update_checkboxes_from_tags()
    
    def enter_edit_mode(self, file_id):
        """Enter edit mode for a specific file"""
        self.edit_mode = True
        self.editing_file_id = file_id
        
        # Update UI elements
        self.form_label_var.set("Edit STL File")
        self.submit_button_var.set("Update in Catalog")
        self.cancel_button.config(state=tk.NORMAL)
        
        # Disable list controls while editing
        self.edit_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        self.file_listbox.config(state=tk.DISABLED)
    
    def exit_edit_mode(self):
        """Exit edit mode and reset form"""
        self.edit_mode = False
        self.editing_file_id = None
        
        # Clear related files list
        self.related_stl_files = []

        # Reset form
        self.file_path_var.set("")
        self.name_var.set("")
        self.tags_var.set("")
        
        # Reset all checkboxes
        for tag, var in self.tag_vars.items():
            var.set(False)
        
        # Update UI elements
        self.form_label_var.set("Add STL File")
        self.submit_button_var.set("Add to Catalog")
        self.cancel_button.config(state=tk.DISABLED)
        
        # Re-enable list controls
        self.file_listbox.config(state=tk.NORMAL)
        
        # Update selection state
        self.on_file_select(None)
    
    def cancel_edit(self):
        """Cancel current edit operation"""
        self.exit_edit_mode()
    
    def delete_selected(self):
        """Delete selected entries from the catalog"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        # Get selected file IDs
        file_ids = []
        file_names = []
        for index in selection:
            if index in self.listbox_mapping:
                file_id = self.listbox_mapping[index]
                
                # Get the file name for the confirmation message
                name = self.file_listbox.get(index)
                
                file_ids.append(file_id)
                file_names.append(name)
        
        # Use the file manager module to delete files
        delete_files_from_catalog(file_ids, file_names, self.settings, self.update_after_database_change)
        
        # Clear details if no selection
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.config(state=tk.DISABLED)
    
    def export_database_callback(self):
        """Export database callback for settings dialog"""
        export_database()
    
    def import_database_callback(self):
        """Import database callback for settings dialog"""
        if import_database(self.update_after_database_change):
            # Clear any selection
            self.on_file_select(None)
    
    def open_settings(self):
        """Open settings dialog"""
        open_settings_dialog(
            self.root, 
            self.settings, 
            self.export_database_callback, 
            self.import_database_callback
        )