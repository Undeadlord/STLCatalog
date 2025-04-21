import os
import json

# Configuration constants
DB_FILE = "stl_catalog.db"
SETTINGS_FILE = "stl_catalog_settings.json"
DEFAULT_TAGS = ["FDM", "Resin"]

def get_script_dir():
    """Get the directory where the script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def load_settings():
    """Load settings from JSON file or create default settings"""
    default_settings = {
        "show_success_messages": True,
        "confirm_delete": True,
        "remember_window_geometry": False,  # New default setting for window geometry
        "window_geometry": "",  # Empty string means use default size/position
    }
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                # Merge with defaults to ensure all settings exist
                return {**default_settings, **loaded_settings}
        except json.JSONDecodeError:
            print("Settings file is corrupted. Creating a new one.")
            return default_settings
    else:
        return default_settings

def save_settings(settings):
    """Save settings to JSON file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False