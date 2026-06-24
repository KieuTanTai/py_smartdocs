"""
Wrapper script to run Shiny app without sys.path conflicts.
This prevents the parent directory app/ folder from shadowing frontend/app.py
"""
import sys
from pathlib import Path

# Get the frontend directory
FRONTEND_DIR = Path(__file__).resolve().parent

# Remove parent directory from sys.path if it's there to avoid conflicts
PARENT_DIR = FRONTEND_DIR.parent
if str(PARENT_DIR) in sys.path:
    sys.path.remove(str(PARENT_DIR))

# Ensure frontend is first in path
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

# Now import the app
from app import app

# This allows Shiny to find the app object
__all__ = ['app']
