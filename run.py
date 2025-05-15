"""
Run script for the Wayback Ecommerce Chatbot.
This script provides a convenient way to start the application.
"""

import os
import sys
import importlib.util
from dotenv import load_dotenv

def main():
    """Main entry point for the application"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable is not set.")
        print("You can set it in a .env file or provide it in the application UI.")
    
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        print(f"Created cache directory: {cache_dir}")
    
    # Determine the path to the main.py file
    main_py_path = os.path.join(os.path.dirname(__file__), "app", "main.py")
    
    # Check if the file exists
    if not os.path.exists(main_py_path):
        print(f"Error: Could not find {main_py_path}")
        sys.exit(1)
    
    # Get the Streamlit port from environment variable or use default
    port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")
    
    # Print startup message
    print("Starting Wayback Ecommerce Chatbot...")
    print(f"The application will be available at http://localhost:{port}")
    print("Press Ctrl+C to stop the application")
    
    # Import and run the main module directly
    try:
        # Add the app directory to the Python path
        app_dir = os.path.join(os.path.dirname(__file__), "app")
        sys.path.insert(0, app_dir)
        
        # Import the main module
        spec = importlib.util.spec_from_file_location("main", main_py_path)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # The main module will be executed when imported
        print("Application started successfully!")
        
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"Error starting the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()