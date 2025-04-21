import traceback
import sys
import os
import time

# Create a log file for debugging
DEBUG_LOG_FILE = "stl_catalog_debug.log"

def debug_log(message):
    """Write debug message to log file"""
    try:
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        with open(DEBUG_LOG_FILE, "a") as f:
            f.write(f"{timestamp} {message}\n")
    except:
        pass  # Silently fail if we can't write to the log

def setup_exception_logging():
    """Set up global exception handler to log all unhandled exceptions"""
    original_hook = sys.excepthook
    
    def exception_hook(exctype, value, traceback_obj):
        """Global exception handler to log unhandled exceptions"""
        # Call the original exception hook
        original_hook(exctype, value, traceback_obj)
        
        # Log the exception
        try:
            error_msg = "".join(traceback.format_exception(exctype, value, traceback_obj))
            debug_log(f"UNHANDLED EXCEPTION:\n{error_msg}")
        except:
            pass
    
    # Replace the exception hook
    sys.excepthook = exception_hook
    
    # Log that we've started
    debug_log("Exception logging set up")
    
    return "Exception logging set up"