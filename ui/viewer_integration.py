"""
STL file viewer integration for STL Catalog
"""
import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
import importlib.util

def check_trimesh_available():
    """Check if Trimesh is available"""
    try:
        import trimesh
        import numpy as np
        return True
    except ImportError:
        return False

def check_pyglet_version():
    """Check if Pyglet is available and has correct version"""
    try:
        import pyglet
        version = pyglet.version
        # Check if version is less than 2.0
        major_version = int(version.split('.')[0])
        if major_version < 2:
            return True
        else:
            return False
    except ImportError:
        return False

def install_dependencies():
    """Attempt to install Trimesh and correct Pyglet version"""
    try:
        import subprocess
        # Install Trimesh
        subprocess.check_call([sys.executable, "-m", "pip", "install", "trimesh"])
        # Install Pyglet < 2.0
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyglet<2"])
        messagebox.showinfo(
            "Installation Complete", 
            "Dependencies have been installed successfully! Please restart the application."
        )
        return True
    except Exception as e:
        messagebox.showerror(
            "Installation Failed", 
            f"Failed to install dependencies: {str(e)}\n\n"
            "Please install them manually using:\n\n"
            "pip install trimesh\n"
            "pip install 'pyglet<2'"
        )
        return False

def view_stl(parent, file_path):
    """View an STL file using the enhanced Trimesh viewer"""
    if not os.path.exists(file_path):
        messagebox.showerror("Error", f"File not found: {file_path}")
        return
    
    # Check if the file is an STL file
    if not file_path.lower().endswith('.stl'):
        messagebox.showerror("Error", f"Not an STL file: {file_path}")
        return
    
    # Check dependencies
    trimesh_available = check_trimesh_available()
    pyglet_version_ok = check_pyglet_version()
    
    if not trimesh_available or not pyglet_version_ok:
        # Ask user if they want to install dependencies
        if messagebox.askyesno(
            "Missing Dependencies", 
            "Some dependencies are missing or have incorrect versions:\n\n" +
            ('' if trimesh_available else "- Trimesh is not installed\n") +
            ('' if pyglet_version_ok else "- Pyglet needs to be version < 2.0\n\n") +
            "Would you like to install the required dependencies now?"
        ):
            install_dependencies()
        return
    
    # Launch the viewer directly
    launch_viewer(parent, file_path)

def view_selected_stl(parent, file_path_or_details):
    """View the selected STL file - wrapper for view_stl to match expected function name
    
    Parameters:
        parent: The parent Tk widget
        file_path_or_details: Either a string path to an STL file or a dictionary containing file details
    """
    # Extract the file path if a dictionary was provided
    if isinstance(file_path_or_details, dict):
        # Direct key lookup with fallbacks
        if 'file_path' in file_path_or_details:
            file_path = file_path_or_details['file_path']
        else:
            # Check for common key names that might contain the file path
            possible_keys = ['path', 'filepath', 'file', 'stl_path', 'location', 'full_path']
            
            file_path = None
            # Try each possible key
            for key in possible_keys:
                if key in file_path_or_details and file_path_or_details[key]:
                    file_path = file_path_or_details[key]
                    break
            
            # If no path found, show error and exit
            if not file_path:
                messagebox.showerror("Error", "Could not determine the STL file path from the provided details.")
                return
    else:
        # If a string or PathLike object was provided, use it directly
        file_path = file_path_or_details
    
    # Now call view_stl with the extracted file path
    view_stl(parent, file_path)

def launch_direct_viewer(stl_file_path):
    """
    Launch the STL viewer directly with the given file path,
    bypassing any intermediate metadata window.
    
    Args:
        stl_file_path: Path to the STL file to view
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(stl_file_path):
        messagebox.showerror("Error", f"File not found: {stl_file_path}")
        return False
        
    try:
        # Get the Python executable path
        python_exe = sys.executable
        
        # First, try to find the standalone viewer which can be launched with settings
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_standalone_paths = [
            # Try these locations for standalone viewer
            os.path.join(script_dir, "..", "enhanced_trimesh_viewer_standalone.py"),
            os.path.join(os.path.dirname(script_dir), "enhanced_trimesh_viewer_standalone.py"),
            os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "enhanced_trimesh_viewer_standalone.py"),
            os.path.join(script_dir, "enhanced_trimesh_viewer_standalone.py"),
        ]
        
        # Find the first existing standalone path
        standalone_script = None
        for path in possible_standalone_paths:
            if os.path.exists(path):
                standalone_script = path
                print(f"Found standalone viewer script at: {path}")
                break
        
        if standalone_script:
            # Build the command with direct render settings
            settings = {
                'color': [120, 255, 150, 255],         # Light green color
                'background_color': [0, 0, 0, 255],    # Black background
                'show_axes': True,                     # Show coordinate axes
                'rotation': [45, 45, 0],               # Default rotation for good view
                'direct_render': True,                 # Flag to bypass metadata display
                'zoom_factor': 1.5,                    # Zoom in by 50%
            }
            
            import json
            settings_str = json.dumps(settings)
            
            # Launch the standalone viewer with settings
            print(f"Launching direct render: {python_exe} {standalone_script} {stl_file_path}")
            subprocess.Popen([python_exe, standalone_script, stl_file_path, settings_str])
            return True
        
        # Fallback to regular viewer if standalone not found
        possible_regular_paths = [
            os.path.join(script_dir, "..", "enhanced_trimesh_viewer.py"),
            os.path.join(os.path.dirname(script_dir), "enhanced_trimesh_viewer.py"),
            os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "enhanced_trimesh_viewer.py"),
            os.path.join(script_dir, "enhanced_trimesh_viewer.py"),
        ]
        
        # Find the first existing regular path
        regular_script = None
        for path in possible_regular_paths:
            if os.path.exists(path):
                regular_script = path
                print(f"Found regular viewer script at: {path}")
                break
        
        if not regular_script:
            messagebox.showerror("Error", "Could not find any viewer script")
            return False
        
        # Launch regular viewer as fallback
        print(f"Launching regular viewer: {python_exe} {regular_script} {stl_file_path}")
        subprocess.Popen([python_exe, regular_script, stl_file_path])
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch STL viewer: {str(e)}")
        print(f"Error launching viewer: {e}")
        return False
    
def launch_viewer(parent, file_path):
    """Launch the viewer directly with correct arguments"""
    try:
        # Get the Python executable path
        python_exe = sys.executable
        
        # Find the path to the viewer module
        possible_paths = []
        
        # Current directory
        possible_paths.append(os.path.join(os.getcwd(), "enhanced_trimesh_viewer.py"))
        
        # Script directory
        possible_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_trimesh_viewer.py"))
        
        # Parent directory of script
        possible_paths.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "enhanced_trimesh_viewer.py"))
        
        # Directory of the main script
        possible_paths.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "enhanced_trimesh_viewer.py"))
        
        # Find the first existing path
        viewer_script = None
        for path in possible_paths:
            if os.path.exists(path):
                viewer_script = path
                break
        
        if not viewer_script:
            raise FileNotFoundError("Could not find enhanced_trimesh_viewer.py")
        
        # Create and launch the command
        cmd = [python_exe, viewer_script, file_path]
        
        # To properly handle Tkinter parent windows, we need to know if this is a module the viewer requires
        # If it's a module, we'll pass the parent window's ID
        if parent:
            if hasattr(parent, 'winfo_id'):
                # Get the window ID to pass to the viewer, which allows proper parenting
                # This ensures the viewer window appears as a child window
                window_id = parent.winfo_id()
                cmd.append("--parent-id")
                cmd.append(str(window_id))
            
        # Launch the viewer in a separate process to avoid threading issues
        subprocess.Popen(cmd)
        
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch STL viewer: {str(e)}")
        return False

# Function to open the viewer directly from command line
def open_stl_file(file_path):
    """Open an STL file directly in the enhanced viewer"""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    # Check if the file is an STL file
    if not file_path.lower().endswith('.stl'):
        print(f"Error: Not an STL file: {file_path}")
        return False
    
    # Check dependencies
    if not check_trimesh_available() or not check_pyglet_version():
        print("Error: Required dependencies are missing or have incorrect versions.")
        print("Please install them with: pip install trimesh 'pyglet<2'")
        return False
    
    return launch_viewer(None, file_path)

# Command line interface
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        open_stl_file(file_path)
    else:
        print("Usage: python viewer_integration.py <stl_file>")