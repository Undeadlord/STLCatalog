#!/usr/bin/env python
"""
Setup script for installing Trimesh and its dependencies for STL Catalog
"""
import os
import sys
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, messagebox

class TrimeshSetupUtility:
    def __init__(self, root):
        self.root = root
        self.root.title("Trimesh Setup Utility")
        
        # Set a much larger initial size
        self.root.geometry("800x700")
        self.root.minsize(800, 700)
        
        # Force the window to be drawn and updated
        self.root.update_idletasks()
        
        # Create a full hard-coded layout without relying on pack/grid managers
        # Use a top frame for all content (65% of window height)
        top_section = ttk.Frame(root)
        top_section.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.65)
        
        # Create a bottom frame just for the output box (30% of window height)
        bottom_section = ttk.LabelFrame(root, text="Output")
        bottom_section.place(relx=0.02, rely=0.68, relwidth=0.96, relheight=0.30)
        
        # Title at the top
        title_label = ttk.Label(
            top_section,
            text="Trimesh Installation Manager",
            font=("Arial", 16, "bold")
        )
        title_label.place(relx=0.02, rely=0.02, relwidth=0.96)
        
        # Create output text area in the bottom section
        self.output_text = tk.Text(bottom_section, height=10, width=90, wrap=tk.WORD)
        self.output_text.place(relx=0.02, rely=0.05, relwidth=0.94, relheight=0.90)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(bottom_section, orient="vertical", command=self.output_text.yview)
        scrollbar.place(relx=0.96, rely=0.05, relwidth=0.02, relheight=0.90)
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        # System info frame
        info_frame = ttk.LabelFrame(top_section, text="System Information")
        info_frame.place(relx=0.02, rely=0.08, relwidth=0.96, relheight=0.25)
        
        # Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_label = ttk.Label(
            info_frame,
            text=f"Python Version: {py_version}",
            font=("Arial", 10)
        )
        py_label.place(relx=0.05, rely=0.15, relwidth=0.90)
        
        # Platform info
        platform_text = f"Platform: {platform.system()} {platform.architecture()[0]}"
        platform_label = ttk.Label(
            info_frame,
            text=platform_text,
            font=("Arial", 10)
        )
        platform_label.place(relx=0.05, rely=0.35, relwidth=0.90)
        
        # Check Trimesh and Pyglet status
        trimesh_status, pyglet_status = self.check_dependencies_status()
        self.trimesh_status_label = ttk.Label(
            info_frame,
            text=f"Trimesh Status: {trimesh_status}",
            font=("Arial", 10)
        )
        self.trimesh_status_label.place(relx=0.05, rely=0.55, relwidth=0.90)
        
        self.pyglet_status_label = ttk.Label(
            info_frame,
            text=f"Pyglet Status: {pyglet_status}",
            font=("Arial", 10)
        )
        self.pyglet_status_label.place(relx=0.05, rely=0.75, relwidth=0.90)
        
        # Installation options frame
        install_frame = ttk.LabelFrame(top_section, text="Installation Options")
        install_frame.place(relx=0.02, rely=0.35, relwidth=0.96, relheight=0.63)
        
        # Installation description
        description_label = ttk.Label(
            install_frame,
            text="Select the appropriate installation option:",
            font=("Arial", 10)
        )
        description_label.place(relx=0.05, rely=0.05, relwidth=0.90)
        
        # Standard install button
        standard_button = ttk.Button(
            install_frame,
            text="Standard Install (Recommended)",
            command=self.install_standard,
            width=30
        )
        standard_button.place(relx=0.05, rely=0.15, relwidth=0.40, relheight=0.12)
        
        # Standard install description
        standard_desc = ttk.Label(
            install_frame,
            text="Installs Trimesh with Pyglet<2 for visualization support. This is the recommended option for most users.",
            wraplength=400,
            justify=tk.LEFT
        )
        standard_desc.place(relx=0.50, rely=0.15, relwidth=0.45)
        
        # Fix Pyglet button
        fix_button = ttk.Button(
            install_frame,
            text="Fix Pyglet Version",
            command=self.fix_pyglet,
            width=30
        )
        fix_button.place(relx=0.05, rely=0.35, relwidth=0.40, relheight=0.12)
        
        # Fix Pyglet description
        fix_desc = ttk.Label(
            install_frame,
            text="If Trimesh is installed but visualization doesn't work, use this option to install the correct version of Pyglet (must be <2.0).",
            wraplength=400,
            justify=tk.LEFT
        )
        fix_desc.place(relx=0.50, rely=0.35, relwidth=0.45)
        
        # Uninstall button
        uninstall_button = ttk.Button(
            install_frame,
            text="Uninstall Trimesh",
            command=self.uninstall_trimesh,
            width=30
        )
        uninstall_button.place(relx=0.05, rely=0.55, relwidth=0.40, relheight=0.12)
        
        # Uninstall description
        uninstall_desc = ttk.Label(
            install_frame,
            text="Remove Trimesh and its dependencies from your system.",
            wraplength=400,
            justify=tk.LEFT
        )
        uninstall_desc.place(relx=0.50, rely=0.55, relwidth=0.45)
        
        # Test button
        test_button = ttk.Button(
            install_frame,
            text="Test Trimesh Installation",
            command=self.test_trimesh,
            width=30
        )
        test_button.place(relx=0.30, rely=0.75, relwidth=0.40, relheight=0.12)
        
        # Initialize with a welcome message
        self.log("Trimesh Setup Utility ready. Select an installation option to begin.")
    
    def check_dependencies_status(self):
        """Check the status of Trimesh and Pyglet"""
        trimesh_status = "Not installed"
        pyglet_status = "Not installed"
        
        try:
            import trimesh
            trimesh_version = trimesh.__version__
            trimesh_status = f"Installed (version {trimesh_version})"
        except ImportError:
            pass
        
        try:
            import pyglet
            pyglet_version = pyglet.version
            pyglet_status = f"Installed (version {pyglet_version})"
            
            # Check if pyglet version is < 2
            major_version = int(pyglet_version.split('.')[0])
            if major_version >= 2:
                pyglet_status += " - WARNING: Version must be < 2.0 for Trimesh visualization"
        except ImportError:
            pass
        
        return trimesh_status, pyglet_status
    
    def update_status(self):
        """Update the status labels"""
        trimesh_status, pyglet_status = self.check_dependencies_status()
        self.trimesh_status_label.config(text=f"Trimesh Status: {trimesh_status}")
        self.pyglet_status_label.config(text=f"Pyglet Status: {pyglet_status}")
    
    def log(self, message):
        """Add message to the output text widget"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def run_subprocess(self, cmd, success_msg, error_msg):
        """Run a subprocess command and handle output and errors"""
        self.log(f"Running: {' '.join(cmd)}")
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read and display output line by line
            for line in process.stdout:
                self.log(line.strip())
            
            # Wait for process to complete
            process.wait()
            
            if process.returncode == 0:
                self.log(success_msg)
                return True
            else:
                self.log(error_msg)
                return False
        except Exception as e:
            self.log(f"Error: {str(e)}")
            return False
    
    def install_standard(self):
        """Install Trimesh with visualization support"""
        self.log("Installing Trimesh with visualization support...")
        
        # First, make sure pyglet is installed with correct version (must be < 2)
        self.log("Step 1/2: Installing pyglet<2")
        result1 = self.run_subprocess(
            [sys.executable, "-m", "pip", "install", "pyglet<2"],
            "Pyglet < 2.0 installed successfully.",
            "Failed to install Pyglet."
        )
        
        if not result1:
            self.log("Failed to install Pyglet. Aborting Trimesh installation.")
            self.update_status()
            return
        
        # Then install Trimesh
        self.log("Step 2/2: Installing Trimesh")
        result2 = self.run_subprocess(
            [sys.executable, "-m", "pip", "install", "trimesh[easy]"],
            "Trimesh installed successfully with visualization support.",
            "Failed to install Trimesh."
        )
        
        if result2:
            self.log("Installation complete. Trimesh is now ready to use with visualization support.")
        else:
            self.log("Trimesh installation failed, but Pyglet was installed successfully.")
        
        self.update_status()
    
    def fix_pyglet(self):
        """Fix Pyglet version (must be < 2)"""
        self.log("Fixing Pyglet version (installing version < 2.0)...")
        
        # First uninstall current pyglet
        self.log("Step 1/2: Removing existing Pyglet installation")
        self.run_subprocess(
            [sys.executable, "-m", "pip", "uninstall", "-y", "pyglet"],
            "Removed existing Pyglet installation.",
            "Failed to remove existing Pyglet or Pyglet not installed."
        )
        
        # Install correct version
        self.log("Step 2/2: Installing Pyglet < 2.0")
        result = self.run_subprocess(
            [sys.executable, "-m", "pip", "install", "pyglet<2"],
            "Pyglet < 2.0 installed successfully.",
            "Failed to install Pyglet < 2.0."
        )
        
        if result:
            self.log("Pyglet has been fixed. Trimesh visualization should now work correctly.")
        else:
            self.log("Failed to fix Pyglet. Trimesh visualization may not work correctly.")
        
        self.update_status()
    
    def uninstall_trimesh(self):
        """Uninstall Trimesh"""
        if messagebox.askyesno("Confirm Uninstall", "Are you sure you want to uninstall Trimesh?"):
            self.log("Uninstalling Trimesh...")
            result = self.run_subprocess(
                [sys.executable, "-m", "pip", "uninstall", "-y", "trimesh"],
                "Trimesh uninstalled successfully.",
                "Failed to uninstall Trimesh."
            )
            
            if result:
                # Ask if pyglet should also be uninstalled
                if messagebox.askyesno("Uninstall Dependencies", "Do you also want to uninstall Pyglet?"):
                    self.log("Uninstalling Pyglet...")
                    self.run_subprocess(
                        [sys.executable, "-m", "pip", "uninstall", "-y", "pyglet"],
                        "Pyglet uninstalled successfully.",
                        "Failed to uninstall Pyglet."
                    )
            
            self.update_status()
    
    def test_trimesh(self):
        """Test if Trimesh is installed correctly with visualization support"""
        self.log("Testing Trimesh installation...")
        
        try:
            import trimesh
            import numpy as np
            import pyglet
            
            # Check pyglet version
            pyglet_version = pyglet.version
            major_version = int(pyglet_version.split('.')[0])
            
            if major_version >= 2:
                self.log(f"WARNING: Pyglet version {pyglet_version} may not work with Trimesh. Version < 2.0 is required.")
            else:
                self.log(f"Pyglet version {pyglet_version} is compatible with Trimesh.")
            
            # Create a simple test mesh
            self.log("Creating test mesh...")
            mesh = trimesh.creation.box(extents=[1, 1, 1])
            
            # Test some basic properties
            self.log(f"Test mesh has {len(mesh.vertices)} vertices and {len(mesh.faces)} faces")
            self.log(f"Mesh volume: {mesh.volume}")
            self.log(f"Mesh surface area: {mesh.area}")
            
            self.log("Trimesh test completed successfully!")
            
            # Ask if user wants to view the test mesh
            if messagebox.askyesno("View Test Mesh", "Would you like to open the test mesh in a viewer to verify visualization works?"):
                # Use a separate thread to show the mesh
                import threading
                threading.Thread(target=lambda: mesh.show(), daemon=True).start()
                self.log("Opening test mesh in viewer. Close the viewer window when done.")
            
        except ImportError as e:
            self.log(f"Trimesh test failed: {str(e)}")
            self.log("One or more required components are not installed.")
        except Exception as e:
            self.log(f"Trimesh test failed with error: {str(e)}")
        
        self.update_status()

def main():
    root = tk.Tk()
    app = TrimeshSetupUtility(root)
    root.mainloop()

if __name__ == "__main__":
    main()