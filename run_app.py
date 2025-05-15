"""
Simple script to run the Wayback Ecommerce Chatbot application.
This script adds the current directory to the Python path to make imports work correctly.
"""

import os
import sys
import streamlit.web.cli as stcli

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    """Run the Streamlit application"""
    # Use port 8506 to avoid conflicts
    sys.argv = ["streamlit", "run", "app/main.py", "--server.port=8506"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()