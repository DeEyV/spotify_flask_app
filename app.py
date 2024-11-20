"""
Spotify Download Flask App
A web application for downloading Spotify tracks with progress tracking.
"""

from flask import (
    Flask, 
    render_template, 
    request, 
    jsonify,
    send_from_directory
)
import os

from components.file_manager import FileManager
from components.download_manager import DownloadManager

# Initialize Flask app
app = Flask(__name__)

# Environment detection
ON_SERVER = os.getenv('ON_SERVER', False)

# Configuration
if ON_SERVER:
    # Render environment
    app.config['DOWNLOAD_FOLDER'] = '/tmp/downloads'
else:
    # Local environment (Windows/Mac/Linux)
    app.config['DOWNLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

app.config['MAX_FILE_AGE'] = 24  # hours

# Create download directory if it doesn't exist
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Initialize managers
file_manager = FileManager(app.config['DOWNLOAD_FOLDER'], app.config['MAX_FILE_AGE'])
download_manager = DownloadManager(app.config['DOWNLOAD_FOLDER'])

@app.route('/')
def index():
    """
    Main page route
    Lists all downloaded files sorted by newest first
    """
    files = file_manager.list_files()
    return render_template('index.html', files=files)

@app.route('/download', methods=['POST'])
def download():
    """
    Download route
    Starts a new download task for the given Spotify URL
    """
    try:
        data = request.get_json()
        spotify_url = data.get('url')
        format = data.get('format', 'mp3')
        bitrate = data.get('bitrate', '320k')
        
        if not spotify_url:
            return jsonify({'error': 'No Spotify URL provided'}), 400
            
        if not spotify_url.startswith('https://open.spotify.com/'):
            return jsonify({'error': 'Invalid Spotify URL'}), 400
        
        print(f"Starting download for URL: {spotify_url}")  # Debug log
        task_id = download_manager.start_download(spotify_url, format, bitrate)
        
        return jsonify({
            'task_id': task_id,
            'status': 'started'
        })
        
    except Exception as e:
        print(f"Error in download endpoint: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """
    Get progress for a specific download task
    """
    try:
        progress = download_manager.get_progress(task_id)
        if progress is None:
            return jsonify({'error': 'Task not found'}), 404
            
        return jsonify(progress)
        
    except Exception as e:
        print(f"Error in progress endpoint: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/downloads/<path:filename>')
def serve_file(filename):
    """
    File download route
    Serve a downloaded file
    """
    try:
        # Get file path and check existence
        file_path = file_manager.get_file_path(filename)
        if not os.path.exists(file_path):
            app.logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404
            
        # Get directory and clean filename
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        app.logger.info(f"Serving file: {file_path}")
        
        # Send file with proper headers
        try:
            response = send_from_directory(
                directory,
                filename,
                as_attachment=True,
                download_name=filename
            )
            
            # Add headers for better download handling
            response.headers['Content-Length'] = os.path.getsize(file_path)
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Cache-Control'] = 'no-cache'
            
            return response
            
        except Exception as e:
            app.logger.error(f"Error sending file: {str(e)}")
            return jsonify({'error': f'Error sending file: {str(e)}'}), 500
            
    except Exception as e:
        app.logger.error(f"Error in serve_file: {str(e)}")
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/download_file/<path:filename>')
def download_file(filename):
    """Redirect old download route to new one"""
    return serve_file(filename)

if __name__ == '__main__':
    # Development server with debug mode but no auto-reload
    print("Running in development mode with auto-reloading disabled...")
    app.run(
        debug=True,
        use_reloader=False,  # Disable auto-reloader
        port=5000
    )
