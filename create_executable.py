# create_executable.py
import PyInstaller.__main__
import os
import sys

# Get the directory of this script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Check if templates directory exists
templates_path = os.path.join(base_dir, 'templates')
if not os.path.exists(templates_path):
    print(f"⚠️  Templates directory not found at: {templates_path}")
    print("Creating empty templates directory...")
    os.makedirs(templates_path, exist_ok=True)

# PyInstaller arguments
args = [
    'app.py',                    # Your main app file
    '--name=NL2SQL_Demo',       # Name of executable
    '--onefile',                # Single executable file
    '--windowed',               # No console window
    '--clean',                  # Clean build
    '--noconfirm',              # Don't ask for confirmation
    '--add-data', f'templates{os.pathsep}templates',  # Add templates if they exist
    '--icon=icon.ico',          # Optional icon (remove if you don't have one)
    '--hidden-import=streamlit',  # Ensure Streamlit is included
    '--hidden-import=pandas',
    '--hidden-import=sqlite3',
    '--hidden-import=numpy',
    '--hidden-import=json',
    '--hidden-import=random',
    '--hidden-import=datetime',
    '--hidden-import=re',
]

# Remove icon argument if icon doesn't exist
if not os.path.exists('icon.ico'):
    args.remove('--icon=icon.ico')
    print("⚠️  icon.ico not found, proceeding without icon")

print("🚀 Building executable...")
print(f"Arguments: {args}")

try:
    PyInstaller.__main__.run(args)
    print("✅ Build completed successfully!")
except Exception as e:
    print(f"❌ Build failed: {e}")