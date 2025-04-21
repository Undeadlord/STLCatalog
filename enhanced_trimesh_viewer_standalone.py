"""
Simplified standalone STL viewer using Trimesh

This script is meant to be run as a separate process to avoid threading issues
with Pyglet and Trimesh.
"""
import os
import sys
import json
import argparse
import pyglet
import platform
import time
import ctypes
import threading

try:
    import trimesh
    import numpy as np
    TRIMESH_AVAILABLE = True
except ImportError:
    print("Error: Trimesh is not installed.")
    print("Please install it with: pip install trimesh pyglet<2")
    sys.exit(1)

def find_window_handle_by_partial_title(partial_title):
    from ctypes import wintypes

    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW

    matching_hwnd = []

    def foreach_window(hwnd, lParam):
        length = GetWindowTextLength(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buff, length + 1)
        title = buff.value
        if partial_title.lower() in title.lower():
            matching_hwnd.append(hwnd)
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)

    return matching_hwnd[0] if matching_hwnd else None

def maximize_window(partial_title, timeout=5.0, check_interval=0.1):
    """
    Polls for a window whose title contains `partial_title` and maximizes it.
    """
    if platform.system() != "Windows":
        return False  # This function is Windows-only

    hwnd = None
    end_time = time.time() + timeout

    while time.time() < end_time:
        hwnd = find_window_handle_by_partial_title(partial_title)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 3)  # 3 = SW_MAXIMIZE
            return True
        time.sleep(check_interval)

    print(f"Warning: Could not find window with title containing '{partial_title}' to maximize.")
    return False

def get_screen_size():
    display = pyglet.canvas.get_display()
    screen = display.get_default_screen()
    return screen.width, screen.height

def view_stl_file(stl_file, settings=None):
    """
    View an STL file with the specified settings
    
    Args:
        stl_file: Path to the STL file
        settings: Dictionary of viewer settings
    """
    if not os.path.exists(stl_file):
        print(f"Error: File not found: {stl_file}")
        return
    
    # Default settings
    default_settings = {
        'color': [180, 180, 180, 255],      # Default gray color
        'rotation': [45, 45, 0],            # Default viewing angle
        'show_wireframe': False,            # Don't show wireframe by default
        'show_axes': True,                  # Show axes by default
        'background_color': [50, 50, 50, 255], # Default dark gray background
        'direct_render': False,             # Flag for direct rendering without extra output
        'zoom_factor': 1.0,                 # Default zoom level (no zoom)
        'window_size': [1024, 768],         # Default window size
    }
    
    # Use provided settings or defaults
    if settings:
        default_settings.update(settings)
    settings = default_settings
    
    try:
        # Load the STL file
        if not settings.get('direct_render', False):
            print(f"Loading STL file: {stl_file}")
        mesh = trimesh.load(stl_file)
        
        # Create a copy for display
        display_mesh = mesh.copy()
        
        # Apply transformations
        center = display_mesh.centroid.copy()
        display_mesh.apply_transform(trimesh.transformations.translation_matrix(-center))
        
        # Apply rotations
        for angle, axis in zip(map(np.radians, settings['rotation']), [[1,0,0],[0,1,0],[0,0,1]]):
            if angle != 0:
                display_mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, axis))
        
        # Apply zoom factor by scaling the model
        zoom = settings.get('zoom_factor', 1.0)
        if zoom != 1.0:
            scale_matrix = np.eye(4)
            scale_matrix[0, 0] = zoom
            scale_matrix[1, 1] = zoom
            scale_matrix[2, 2] = zoom
            display_mesh.apply_transform(scale_matrix)
        
        # Move back to original center
        display_mesh.apply_transform(trimesh.transformations.translation_matrix(center))
        
        # Set the mesh color
        display_mesh.visual.face_colors = settings['color']
        
        # Create a new scene with the mesh
        scene = trimesh.Scene(display_mesh)
        
        # Add axes if enabled
        if settings['show_axes']:
            axis_len = float(max(display_mesh.extents)) * 0.5
            origin = display_mesh.bounds[0] - np.array([axis_len] * 3) * 0.2  # Move axes closer to the model
            
            for i, (direction, color) in enumerate(zip(
                np.eye(3), 
                [[255,0,0,255],[0,255,0,255],[0,0,255,255]]
            )):
                cyl = trimesh.creation.cylinder(
                    radius=axis_len/50, 
                    segment=np.vstack((origin, origin + direction * axis_len))
                )
                cyl.visual.face_colors = color
                scene.add_geometry(cyl)
        
        # Get background color
        bg = np.array(settings['background_color'][:3]) / 255.0
        
        # Skip printing info if direct rendering is enabled
        if not settings.get('direct_render', False):
            # Print basic mesh info
            print(f"STL file loaded. Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}")
            print("Showing mesh. Close the window when done.")
            
        # Set window title to include the file name
        window_title = f"STL Viewer - {os.path.basename(stl_file)}"
        
        # Get window size
        window_size = settings.get('window_size', [1024, 768])
        
        screen_width, screen_height = get_screen_size()
        window_size = [screen_width, screen_height]

        # Set window title
        window_title = f"STL Viewer - {os.path.basename(stl_file)}"

        # Launch the maximizer thread
        if platform.system() == "Windows":
            threading.Thread(target=maximize_window, args=(window_title,), daemon=True).start()

        if platform.system() == "Windows":
            threading.Thread(
                target=maximize_window,
                args=("enhanced_trimesh_viewer_standalone",),
                daemon=True
            ).start()

        # Show the scene with custom window size and title
        scene.show(
            background=bg[:3],
            resolution=window_size,
            window_title=window_title,
            smooth=True
        )
        
        if not settings.get('direct_render', False):
            print("Viewer closed")
        
    except Exception as e:
        print(f"Error viewing STL file: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Standalone STL Viewer')
    parser.add_argument('stl_file', help='Path to the STL file to view')
    parser.add_argument('settings', nargs='?', help='Settings as JSON string')
    
    args = parser.parse_args()
    
    # Parse settings if provided
    settings = None
    if args.settings:
        try:
            settings = json.loads(args.settings)
        except json.JSONDecodeError:
            print("Warning: Invalid settings JSON, using defaults")
    
    # View the STL file
    view_stl_file(args.stl_file, settings)

if __name__ == "__main__":
    main()