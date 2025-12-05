import PyInstaller.__main__
import os

# Create spec file
PyInstaller.__main__.run([
    'app.py',
    '--name=NL2SQL_Demo',
    '--onefile',
    '--windowed',  # No console window
    '--add-data=templates;templates',  # If you have templates
    '--icon=icon.ico',  # Optional icon
    '--clean',
    '--noconfirm'
])