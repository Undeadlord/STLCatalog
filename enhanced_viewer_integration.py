"""
Enhanced STL file viewer integration using Trimesh for STL Catalog
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
    
    try:
        # Import the enhanced viewer here to avoid import errors if dependencies are not available
        viewer_module_spec = None
        
        # Try to import the viewer module
        try:
            # First try the direct import
            from enhanced_trimesh_viewer import EnhancedSTLViewer
            
            # Create the viewer
            viewer = EnhancedSTLViewer(parent, file_path)
            
            return
        except ImportError:
            # If direct import fails, look for the module file
            module_name = "enhanced_trimesh_viewer"
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Try different locations for the viewer module
            module_paths = [
                os.path.join(script_dir, f"{module_name}.py"),
                os.path.join(os.path.dirname(script_dir), f"{module_name}.py"),
                os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{module_name}.py")
            ]
            
            for module_path in module_paths:
                if os.path.exists(module_path):
                    # Found the module, import it using importlib
                    viewer_module_spec = importlib.util.spec_from_file_location(module_name, module_path)
                    break
            
            if viewer_module_spec:
                viewer_module = importlib.util.module_from_spec(viewer_module_spec)
                viewer_module_spec.loader.exec_module(viewer_module)
                
                # Create the viewer instance
                viewer = viewer_module.EnhancedSTLViewer(parent, file_path)
                return
        
        # If we couldn't import the module, launch it as a subprocess
        if not viewer_module_spec:
            # Find the viewer script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            viewer_script = os.path.join(script_dir, "enhanced_trimesh_viewer.py")
            
            if not os.path.exists(viewer_script):
                # Try looking in the parent directory
                viewer_script = os.path.join(os.path.dirname(script_dir), "enhanced_trimesh_viewer.py")
                
            if not os.path.exists(viewer_script):
                # Try looking in the same directory as the main script
                viewer_script = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "enhanced_trimesh_viewer.py")
            
            if not os.path.exists(viewer_script):
                messagebox.showerror("Error", "Could not find the enhanced_trimesh_viewer.py script")
                return
            
            # Launch the viewer as a subprocess
            subprocess.Popen([sys.executable, viewer_script, file_path])
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open STL viewer: {str(e)}")

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
    
    try:
        # Find the viewer script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        viewer_script = os.path.join(script_dir, "enhanced_trimesh_viewer.py")
        
        if not os.path.exists(viewer_script):
            # Try looking in the parent directory
            viewer_script = os.path.join(os.path.dirname(script_dir), "enhanced_trimesh_viewer.py")
            
        if not os.path.exists(viewer_script):
            # Try looking in the same directory as the main script
            viewer_script = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "enhanced_trimesh_viewer.py")
        
        if not os.path.exists(viewer_script):
            print("Error: Could not find the enhanced_trimesh_viewer.py script")
            return False
        
        # Launch the viewer as a subprocess
        subprocess.Popen([sys.executable, viewer_script, file_path])
        return True
        
    except Exception as e:
        print(f"Error: Failed to open STL viewer: {str(e)}")
        return False

# Command line interface
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        open_stl_file(file_path)
    else:
        print("Usage: python enhanced_viewer_integration.py <stl_file>")