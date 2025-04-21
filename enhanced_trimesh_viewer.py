"""
Enhanced STL viewer implementation using Trimesh with additional features:
- Custom coloring of meshes
- Scene manipulation (rotation, translation)
- Analysis features (volume, surface area, etc.)
- Loading status notifications
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import threading
import time
import json
import multiprocessing
import argparse

try:
    import trimesh
    import numpy as np
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "stl_viewer_settings.json")

class EnhancedSTLViewer:
    def __init__(self, master=None, stl_file=None):
        if not TRIMESH_AVAILABLE:
            messagebox.showerror(
                "Missing Dependency",
                "Trimesh library is not installed. Please install it with:\n\npip install trimesh pyglet<2"
            )
            return

        self.master = tk.Toplevel(master) if master else tk.Tk()
        self.master.title("Enhanced STL Viewer")
        self.master.geometry("900x700")
        self.master.minsize(600, 500)
        
        # If no master was provided and we're running in a separate process,
        # make sure we have our own event loop
        if not master:
            self.master.update()

        self.stl_file = stl_file
        self.mesh = None
        self.viewer_process = None

        self.settings = {
            'color': [180, 180, 180, 255],
            'rotation': [45, 45, 0],
            'show_wireframe': False,
            'show_axes': True,
            'background_color': [50, 50, 50, 255]
        }

        self.create_ui()
        self.load_settings()
        
        # Create status label at the top of the window
        self.status_label = ttk.Label(
            self.master, 
            text="Ready", 
            font=("Arial", 12, "bold"),
            background="#f0f0f0",
            foreground="#333333",
            padding=10
        )
        self.status_label.pack(side=tk.TOP, fill=tk.X, before=self.main_paned)
        
        if stl_file and os.path.exists(stl_file):
            # Update status to loading
            self.update_status("Loading STL... Please Wait")
            
            # Load the STL file in a thread to keep UI responsive
            threading.Thread(target=self.load_stl, daemon=True).start()
            
        self.apply_loaded_settings_to_ui()

        # Check if any existing viewer processes should be terminated
        if hasattr(multiprocessing, 'active_children'):
            for proc in multiprocessing.active_children():
                if proc.name.startswith('TrimeshViewer'):
                    try:
                        proc.terminate()
                    except:
                        pass

    def create_ui(self):
        self.main_paned = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_paned)
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=30)
        self.main_paned.add(self.right_frame, weight=70)

        self.status_bar = ttk.Label(self.master, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.create_left_panel()
        self.create_right_panel()

    def create_left_panel(self):
        appearance_frame = ttk.LabelFrame(self.left_frame, text="Appearance")
        appearance_frame.pack(fill=tk.X, padx=5, pady=5)

        color_frame = ttk.Frame(appearance_frame)
        color_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(color_frame, text="Mesh Color:").pack(side=tk.LEFT, padx=5)
        self.color_preview = tk.Canvas(color_frame, width=30, height=20, bg='gray')
        self.color_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text="Change", command=self.change_color).pack(side=tk.LEFT, padx=5)

        bg_color_frame = ttk.Frame(appearance_frame)
        bg_color_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(bg_color_frame, text="Background:").pack(side=tk.LEFT, padx=5)
        self.bg_color_preview = tk.Canvas(bg_color_frame, width=30, height=20, bg='#323232')
        self.bg_color_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(bg_color_frame, text="Change", command=self.change_background).pack(side=tk.LEFT, padx=5)

        actions_frame = ttk.LabelFrame(self.left_frame, text="Actions")
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(actions_frame, text="Open Viewer", command=self.open_external_viewer).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(actions_frame, text="Close", command=self.master.destroy).pack(fill=tk.X, padx=5, pady=5)
        
        # Controls help frame - use direct labels
        controls_frame = ttk.LabelFrame(self.left_frame, text="Viewer Controls")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Mouse controls section with header
        ttk.Label(controls_frame, text="MOUSE CONTROLS:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=(5, 2))
        ttk.Label(controls_frame, text="• Left click + drag: Rotate view").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• Right click + drag: Pan view").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• Scroll wheel: Zoom in/out").pack(anchor="w", padx=10, pady=1) 
        ttk.Label(controls_frame, text="• Middle click + drag: Alternate pan").pack(anchor="w", padx=10, pady=1)
        
        # Add a small separator
        ttk.Separator(controls_frame, orient="horizontal").pack(fill="x", padx=5, pady=5)
        
        # Keyboard controls section with header
        ttk.Label(controls_frame, text="KEYBOARD CONTROLS:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=(2, 2))
        ttk.Label(controls_frame, text="• Arrow keys: Rotate view").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• Shift + arrows: Pan view").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• +/- keys: Zoom in/out").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• Z: Reset view").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• W: Toggle wireframe").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• A: Toggle axes").pack(anchor="w", padx=10, pady=1)
        ttk.Label(controls_frame, text="• F: Switch to FullScreen/Back to Windowed").pack(anchor="w", padx=10, pady=(1, 5))

    def create_right_panel(self):
        self.info_text = tk.Text(self.right_frame, wrap=tk.WORD)
        self.info_text.insert(tk.END, '')  # Prevent missing attribute error
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.info_text.config(state=tk.DISABLED)

    def update_status(self, message, is_important=False):
        """Update the status label with a message, with optional highlighting for important messages"""
        self.status_label.config(text=message)
        
        # If it's an important message, make it stand out with different colors
        if is_important:
            self.status_label.config(background="#4a6da7", foreground="#ffffff")
        else:
            self.status_label.config(background="#f0f0f0", foreground="#333333")
            
        # Force update of UI
        self.master.update_idletasks()

    def log(self, message):
        """Add message to the log and update status bar"""
        timestamp = time.strftime("[%H:%M:%S]")
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"{timestamp} {message}\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.status_bar.config(text=message)
        
        # Also update main status label for key messages
        if "Loading" in message or "loaded" in message or "Ready" in message:
            self.update_status(message, is_important="Ready" in message)

    def change_color(self):
        """Change the mesh color using a color chooser dialog"""
        try:
            # Create a new Toplevel dialog for color choosing
            dialog = tk.Toplevel(self.master)
            dialog.title("Select Mesh Color")
            dialog.geometry("300x200")
            dialog.resizable(False, False)
            dialog.transient(self.master)  # Set as transient to master
            dialog.grab_set()  # Grab all events
            dialog.focus_set()  # Set focus to this dialog
            
            # Get current color for preview
            current_color = "#{:02x}{:02x}{:02x}".format(*self.settings['color'][:3])
            
            # Create a color preview in our custom dialog
            preview = tk.Canvas(dialog, width=100, height=100, bg=current_color)
            preview.pack(pady=10)
            
            def open_color_dialog():
                # Open the color chooser from our already-focused dialog
                color = colorchooser.askcolor(color=current_color, title="Select Mesh Color", parent=dialog)
                if color and color[1]:
                    preview.config(bg=color[1])
                    return color
                return None
            
            def apply_color():
                color = open_color_dialog()
                if color and color[1]:
                    r, g, b = [int(c) for c in color[0]]
                    self.settings['color'] = [r, g, b, self.settings['color'][3]]
                    self.color_preview.config(bg=color[1])
                    self.log(f"Mesh color changed to RGB({r}, {g}, {b})")
                    self.save_settings()
                    dialog.destroy()
            
            def cancel():
                dialog.destroy()
            
            # Create buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Select Color", command=apply_color).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=10)
            
            # Wait for the dialog to be closed
            self.master.wait_window(dialog)
            
        except Exception as e:
            self.log(f"Error changing color: {e}")

    def change_background(self):
        """Change the background color using a color chooser dialog"""
        try:
            # Create a new Toplevel dialog for color choosing
            dialog = tk.Toplevel(self.master)
            dialog.title("Select Background Color")
            dialog.geometry("300x200")
            dialog.resizable(False, False)
            dialog.transient(self.master)  # Set as transient to master
            dialog.grab_set()  # Grab all events
            dialog.focus_set()  # Set focus to this dialog
            
            # Get current color for preview
            current_color = "#{:02x}{:02x}{:02x}".format(*self.settings['background_color'][:3])
            
            # Create a color preview in our custom dialog
            preview = tk.Canvas(dialog, width=100, height=100, bg=current_color)
            preview.pack(pady=10)
            
            def open_color_dialog():
                # Open the color chooser from our already-focused dialog
                color = colorchooser.askcolor(color=current_color, title="Select Background Color", parent=dialog)
                if color and color[1]:
                    preview.config(bg=color[1])
                    return color
                return None
            
            def apply_color():
                color = open_color_dialog()
                if color and color[1]:
                    r, g, b = [int(c) for c in color[0]]
                    self.settings['background_color'] = [r, g, b, self.settings['background_color'][3]]
                    self.bg_color_preview.config(bg=color[1])
                    self.log(f"Background color changed to RGB({r}, {g}, {b})")
                    self.save_settings()
                    dialog.destroy()
            
            def cancel():
                dialog.destroy()
            
            # Create buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Select Color", command=apply_color).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=10)
            
            # Wait for the dialog to be closed
            self.master.wait_window(dialog)
            
        except Exception as e:
            self.log(f"Error changing background color: {e}")

    def load_stl(self):
        """Load the STL file with status updates"""
        try:
            # Clear existing info text
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.config(state=tk.DISABLED)
            
            # Update status - Starting load
            self.log(f"Loading STL file: {os.path.basename(self.stl_file)}")
            self.update_status(f"Loading STL file: {os.path.basename(self.stl_file)}...")
            
            # Load the file with trimesh
            start_time = time.time()
            self.mesh = trimesh.load(self.stl_file)
            load_time = time.time() - start_time
            
            # Update status - File loaded
            self.log(f"STL file loaded successfully in {load_time:.2f} seconds")
            self.update_status("Analyzing STL geometry...")
            
            # Add a small delay to make the status message visible
            time.sleep(0.5)
            
            # Calculate and display mesh information
            self.display_mesh_info()
            
            # Final status - Ready to render
            self.log("STL Loaded... Ready to Render")
            self.update_status("STL Loaded... Ready to Render", is_important=True)
            
        except Exception as e:
            self.log(f"Failed to load STL: {e}")
            self.update_status(f"Error: Failed to load STL: {str(e)}", is_important=True)

    def display_mesh_info(self):
        """Display mesh information in the info panel"""
        if self.mesh is None:
            return
            
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"\n=== Mesh Info ===\n")
        
        # Basic stats
        self.info_text.insert(tk.END, f"Vertices: {len(self.mesh.vertices)}\n")
        self.info_text.insert(tk.END, f"Faces: {len(self.mesh.faces)}\n")
        
        # Dimensions
        bounds = self.mesh.bounds
        dimensions = bounds[1] - bounds[0]
        self.info_text.insert(tk.END, f"Size (X×Y×Z): {dimensions[0]:.2f} × {dimensions[1]:.2f} × {dimensions[2]:.2f}\n")
        
        # Volume and surface area
        try:
            self.info_text.insert(tk.END, f"Volume: {self.mesh.volume:.2f} cubic units\n")
            self.info_text.insert(tk.END, f"Surface Area: {self.mesh.area:.2f} square units\n")
        except Exception as e:
            self.info_text.insert(tk.END, f"Volume/Area calculation failed: {str(e)}\n")
        
        # Watertight check
        self.info_text.insert(tk.END, f"Watertight: {self.mesh.is_watertight}\n")
        
        # Center of mass
        center = self.mesh.centroid
        self.info_text.insert(tk.END, f"Center: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})\n")
        
        self.info_text.config(state=tk.DISABLED)

    def open_external_viewer(self):
        """Open the STL with a 3D viewer in a separate process to avoid threading issues"""
        if self.mesh is None:
            messagebox.showerror("Error", "No mesh loaded")
            return

        self.log("Opening external viewer...")
        
        # Terminate any existing viewer process
        if self.viewer_process and hasattr(self.viewer_process, 'is_alive') and self.viewer_process.is_alive():
            try:
                self.viewer_process.terminate()
            except:
                pass  # Ignore errors if we can't terminate
        
        # Create a temporary settings file
        temp_settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_viewer_settings.json")
        try:
            with open(temp_settings_file, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            self.log(f"Warning: Could not save temporary settings: {e}")
        
        # Launch the viewer process
        try:
            # Start a new process to display the 3D view
            # This is the key part that fixes the threading issue
            self.viewer_process = multiprocessing.Process(
                target=show_mesh_in_process,
                args=(self.stl_file, self.settings),
                name=f"TrimeshViewer-{int(time.time())}"
            )
            self.viewer_process.daemon = True
            self.viewer_process.start()
            
            self.log("External viewer launched")
        except Exception as e:
            self.log(f"Error launching external viewer: {e}")
            
            # Fall back to running in a subprocess if multiprocessing fails
            try:
                # Get the Python executable
                python_exe = sys.executable
                
                # Create a script path for the viewer
                viewer_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_mesh_viewer.py")
                
                # Create the viewer script if it doesn't exist
                self.create_mesh_viewer_script(viewer_script)
                
                # Launch the process
                import subprocess
                subprocess.Popen([python_exe, viewer_script, self.stl_file, temp_settings_file])
                
                self.log("External viewer launched (fallback mode)")
            except Exception as e:
                self.log(f"Failed to launch viewer in fallback mode: {e}")

    def create_mesh_viewer_script(self, script_path):
        """Create a standalone viewer script for running in a subprocess"""
        try:
            with open(script_path, 'w') as f:
                f.write('''"""
Standalone mesh viewer script

This script is used to open Trimesh viewer in a separate process
to avoid threading issues with pyglet.
"""
import sys
import json
import os
import time

if __name__ == "__main__":
    # Make sure Trimesh and numpy are installed
    try:
        import trimesh
        import numpy as np
    except ImportError:
        print("Error: Trimesh or numpy not installed")
        print("Install with: pip install trimesh numpy")
        sys.exit(1)
    
    # Check command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python run_mesh_viewer.py <stl_file> [settings_file]")
        sys.exit(1)
    
    stl_file = sys.argv[1]
    settings_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Default settings
    settings = {
        'color': [180, 180, 180, 255],
        'rotation': [45, 45, 0],
        'show_wireframe': False,
        'show_axes': True,
        'background_color': [50, 50, 50, 255]
    }
    
    # Load settings if provided
    if settings_file and os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
        except Exception as e:
            print(f"Warning: Failed to load settings: {e}")
    
    print(f"Loading STL... Please Wait")
    start_time = time.time()
    
    # Load the mesh
    try:
        mesh = trimesh.load(stl_file)
        load_time = time.time() - start_time
        print(f"STL file loaded in {load_time:.2f} seconds")
        print(f"Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}")
    except Exception as e:
        print(f"Error loading mesh: {e}")
        sys.exit(1)
    
    print("STL Loaded... Ready to Render")
    
    # Create a copy for display
    display_mesh = mesh.copy()
    
    # Apply color
    display_mesh.visual.face_colors = settings['color']
    
    # Apply transformations
    center = display_mesh.centroid.copy()
    display_mesh.apply_transform(trimesh.transformations.translation_matrix(-center))
    
    for angle, axis in zip(map(np.radians, settings['rotation']), [[1,0,0],[0,1,0],[0,0,1]]):
        if angle != 0:
            display_mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, axis))
    
    display_mesh.apply_transform(trimesh.transformations.translation_matrix(center))
    
    # Create scene
    scene = trimesh.Scene(display_mesh)
    
    # Add axes if enabled
    if settings['show_axes']:
        axis_len = float(max(display_mesh.extents)) * 0.5
        origin = display_mesh.bounds[0] - np.array([axis_len] * 3) * 0.5
        
        for direction, color in zip(np.eye(3), [[255,0,0,255],[0,255,0,255],[0,0,255,255]]):
            cyl = trimesh.creation.cylinder(
                radius=axis_len/50, 
                segment=np.vstack((origin, origin + direction * axis_len))
            )
            cyl.visual.face_colors = color
            scene.add_geometry(cyl)
    
    # Show the scene
    try:
        bg = np.array(settings['background_color'][:3]) / 255.0
        scene.show(background=bg)
    except Exception as e:
        print(f"Error showing scene: {e}")
        sys.exit(1)
''')
            return True
        except Exception as e:
            self.log(f"Error creating mesh viewer script: {e}")
            return False

    def apply_transformations(self, mesh):
        center = mesh.centroid.copy()
        mesh.apply_transform(trimesh.transformations.translation_matrix(-center))
        for angle, axis in zip(map(np.radians, self.settings['rotation']), [[1,0,0],[0,1,0],[0,0,1]]):
            if angle != 0:
                mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, axis))
        mesh.apply_transform(trimesh.transformations.translation_matrix(center))

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.log("Settings saved")
        except Exception as e:
            self.log(f"Failed to save settings: {e}")

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults
                    self.settings.update(loaded_settings)
                self.log("Settings loaded")
        except Exception as e:
            self.log(f"Failed to load settings: {e}")

    def apply_loaded_settings_to_ui(self):
        # Update color previews to reflect loaded settings
        mesh_color = self.settings['color']
        bg_color = self.settings['background_color']
        mesh_color_hex = "#{:02x}{:02x}{:02x}".format(*mesh_color[:3])
        bg_color_hex = "#{:02x}{:02x}{:02x}".format(*bg_color[:3])
        self.color_preview.config(bg=mesh_color_hex)
        self.bg_color_preview.config(bg=bg_color_hex)
        
    def run(self):
        """Start the main loop"""
        self.master.mainloop()

# Function that runs in a separate process to show the mesh
def show_mesh_in_process(stl_file, settings):
    """
    Show a mesh in a separate process to avoid threading issues
    
    This function must be at the module level to work with multiprocessing
    """
    try:
        # Import here to avoid conflicts
        import trimesh
        import numpy as np
        
        print("Loading STL... Please Wait")
        
        # Load the STL file
        start_time = time.time()
        mesh = trimesh.load(stl_file)
        load_time = time.time() - start_time
        
        print(f"STL file loaded in {load_time:.2f} seconds")
        print(f"Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}")
        print("STL Loaded... Ready to Render")
        
        # Create a copy for display
        display_mesh = mesh.copy()
        
        # Apply color
        display_mesh.visual.face_colors = settings['color']
        
        # Apply transformations
        center = display_mesh.centroid.copy()
        display_mesh.apply_transform(trimesh.transformations.translation_matrix(-center))
        
        for angle, axis in zip(map(np.radians, settings['rotation']), [[1,0,0],[0,1,0],[0,0,1]]):
            if angle != 0:
                display_mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, axis))
        
        display_mesh.apply_transform(trimesh.transformations.translation_matrix(center))
        
        # Create scene
        scene = trimesh.Scene(display_mesh)
        
        # Add axes if enabled
        if settings['show_axes']:
            axis_len = float(max(display_mesh.extents)) * 0.5
            origin = display_mesh.bounds[0] - np.array([axis_len] * 3) * 0.5
            
            for direction, color in zip(np.eye(3), [[255,0,0,255],[0,255,0,255],[0,0,255,255]]):
                cyl = trimesh.creation.cylinder(
                    radius=axis_len/50, 
                    segment=np.vstack((origin, origin + direction * axis_len))
                )
                cyl.visual.face_colors = color
                scene.add_geometry(cyl)
        
        # Show the scene
        bg = np.array(settings['background_color'][:3]) / 255.0
        scene.show(background=bg)
    except Exception as e:
        print(f"Error in viewer process: {e}")

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Enhanced STL Viewer")
    parser.add_argument('stl_file', nargs='?', help='STL file to view')
    parser.add_argument('--parent-id', help='ID of parent window', dest='parent_id')
    args = parser.parse_args()
    
    # Get STL file path
    stl_file = args.stl_file
    if not stl_file:
        # No file provided, open file dialog
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        stl_file = filedialog.askopenfilename(title="Select STL File", filetypes=[("STL Files", "*.stl")])
        if not stl_file:
            print("No file selected. Exiting.")
            return

    # Create and run the viewer
    master = None
    if args.parent_id:
        try:
            # Try to create a Toplevel with an existing window as parent
            root = tk.Tk()
            root.withdraw()
            master = root
        except:
            master = None
    
    viewer = EnhancedSTLViewer(master=master, stl_file=stl_file)
    viewer.run()

if __name__ == "__main__":
    # On Windows, we need to use multiprocessing
    # with the 'spawn' method for proper isolation
    if sys.platform == 'win32' and hasattr(multiprocessing, 'set_start_method'):
        # set_start_method must be called at most once in the program
        try:
            multiprocessing.set_start_method('spawn')
        except RuntimeError:
            pass
    
    main()