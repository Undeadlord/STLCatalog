"""
STL Catalog Main Application

This is the main entry point for the STL Catalog application.
"""
import os
import sys
import tkinter as tk
import logging

from app_config import get_script_dir
from ui.app import STLCatalogApp

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("stl_catalog.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point for the application"""
    # Set up logging
    setup_logging()
    
    # Set working directory to script location
    script_dir = get_script_dir()
    os.chdir(script_dir)
    
    logging.info("Starting STL Catalog application")
    
    try:
        # Create the main window
        root = tk.Tk()
        
        # Create and initialize the application
        app = STLCatalogApp(root)
        
        # Start the main event loop
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Error in main application: {e}", exc_info=True)
        
        # Show error message to user
        try:
            from tkinter import messagebox
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        except:
            pass

if __name__ == "__main__":
    main()