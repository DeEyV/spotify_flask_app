# Spotify Flask Downloader

A web application built with Flask that allows you to download songs from Spotify. You can download individual tracks, entire playlists, or albums while preserving metadata and album artwork.

## Features

- Download Spotify tracks, playlists, and albums
- Preserves song metadata and album artwork
- Clean and intuitive web interface
- Progress tracking for downloads
- Supports multiple concurrent downloads

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone this repository or download the source code:
```bash
git clone <repository-url>
cd spotify_flask_app
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. First, run the setup script to create necessary directories:
```bash
python setup_dirs.py
```

2. Start the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

4. Enter a Spotify URL (track, playlist, or album) in the input field and click "Download"

## Dependencies

The application requires the following main packages:
- Flask==2.3.3
- Werkzeug==2.3.7
- spotdl==4.2.10
- yt-dlp>=2023.7.6
- mutagen>=1.46.0
- pydub>=0.25.1
- requests>=2.31.0

## Notes

- Downloaded files will be saved in the `downloads` directory
- The application supports concurrent downloads
- Make sure you have enough disk space for your downloads

## For Developers

If you plan to develop or modify this application, it's recommended to use a virtual environment:

### Why Use a Virtual Environment?
- Isolates project dependencies from other Python projects
- Prevents conflicts between package versions
- Makes it easier to manage and reproduce development environments
- Protects your system Python installation

### Setting up a Virtual Environment

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- On Windows:
```bash
venv\Scripts\activate
```
- On macOS/Linux:
```bash
source venv/bin/activate
```

3. Then proceed with the regular installation steps.

## Troubleshooting

If you encounter any issues:
1. Make sure all dependencies are correctly installed
2. Check if the `downloads` directory exists
3. Ensure you have a stable internet connection
4. Verify that the Spotify URL is valid and accessible
