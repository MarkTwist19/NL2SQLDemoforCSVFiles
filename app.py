import sys
import os

# Fix for PyInstaller bundled app
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

# Rest of your Streamlit app...