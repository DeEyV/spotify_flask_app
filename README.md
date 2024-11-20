# Spotify Track Downloader

A sleek web application built with Flask that allows you to download individual tracks from Spotify. Features a modern, responsive interface with real-time download progress tracking.

## ✨ Features

- 🎵 Download individual Spotify tracks
- 🎨 Modern, responsive UI with multiple themes
- 📊 Real-time download progress tracking
- 🎧 Multiple audio format support (MP3, FLAC, M4A, etc.)
- 🔊 Customizable bitrate options
- 🗑️ Automatic file cleanup (24-hour retention)

## 🚀 Quick Start

1. Install Python 3.8 or higher
2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
# For Windows
python run.py

# For production (Windows)
waitress-serve --port=5000 app:app

# For production (Mac/Linux)
gunicorn -w 4 app:app
```

4. Open your browser and visit: `http://localhost:5000`

## 🌐 Deployment

### Render Deployment
1. Set these environment variables in your Render dashboard:
```
ON_SERVER=true
FLASK_ENV=production
```

2. Use this start command:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --log-file -
```

3. The app will automatically use `/tmp/downloads` for file storage on the server

### Local Development
- No environment variables needed
- Files are stored in the local `downloads` directory
- Automatically uses the appropriate server (Waitress for Windows, Gunicorn for Mac/Linux)

## 💻 Usage

1. Open the web interface
2. (Optional) Choose your preferred theme
3. Paste a Spotify track URL
4. Select your preferred audio format and quality
5. Click Download
6. Wait for the download to complete
7. Click the download button next to the file to save it

## 🛠️ Supported Formats

- MP3 (128k - 320k)
- FLAC (Lossless)
- M4A
- OGG
- OPUS
- WAV

## ⚙️ Requirements

Core dependencies:
- Flask==2.3.3
- spotdl==4.2.10
- waitress>=2.0.0 (Windows deployment)
- gunicorn>=21.2.0 (Mac/Linux/Server deployment)

## 📝 Notes

- Downloads are automatically deleted after 24 hours
- Large files (like FLAC) may take longer to process
- Internet connection required for downloading

## 🔧 Troubleshooting

1. **Download not starting?**
   - Check your internet connection
   - Verify the Spotify URL is correct
   - Ensure spotdl is properly installed

2. **File not downloading?**
   - Try refreshing the page
   - Check if the file exists in the downloads section
   - Try a different audio format

3. **Slow downloads?**
   - Try a lower quality setting
   - Check your internet speed
   - Consider using MP3 instead of FLAC

## 🔒 Security Notes

- All downloads are temporary (24-hour retention)
- Files are served securely
- Input validation for all user data
- Safe file handling and sanitization

## 🌟 Contributing

Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

