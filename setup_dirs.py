import os

# Create templates directory
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

# Create downloads directory
downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
if not os.path.exists(downloads_dir):
    os.makedirs(downloads_dir)

print("Directories created successfully!")
