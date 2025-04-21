"""
Window geometry utilities for STL Catalog application
"""
import tkinter as tk
import logging

def apply_window_geometry(window, geometry_str=None, default_geometry="800x600"):
    """
    Apply window geometry to a tkinter window
    
    Args:
        window: The tkinter window to apply geometry to
        geometry_str: The geometry string to apply (format: "WIDTHxHEIGHT+X+Y")
        default_geometry: Default geometry to use if geometry_str is None or invalid
    """
    # If no geometry string provided, center the window with default size
    if not geometry_str:
        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Parse default geometry
        parts = default_geometry.split('x')
        width = int(parts[0])
        height = int(parts[1])
        
        # Calculate position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Apply centered default geometry
        window.geometry(f"{width}x{height}+{x}+{y}")
        return
    
    try:
        # Apply custom geometry
        window.geometry(geometry_str)
    except Exception as e:
        logging.error(f"Error applying window geometry: {e}")
        # Fallback to default if there's an error
        window.geometry(default_geometry)

def save_window_geometry(window, settings):
    """
    Save current window geometry to settings
    
    Args:
        window: The tkinter window to get geometry from
        settings: The settings dictionary to save to
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    if settings.get("remember_window_geometry", False):
        try:
            # Get current geometry
            current_geometry = window.geometry()
            
            # Save to settings
            settings["window_geometry"] = current_geometry
            return True
        except Exception as e:
            logging.error(f"Error saving window geometry: {e}")
            return False
    
    return False