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

# Configuration
app.config['DOWNLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
app.config['MAX_FILE_AGE'] = 24  # hours

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

@app.route('/download_file/<path:filename>')
def download_file(filename):
    """Download a specific file from the downloads directory"""
    try:
        # Get the file path
        file_path = file_manager.get_file_path(filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            app.logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404
            
        # Get the directory and filename
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        # Send file
        return send_from_directory(
            directory,
            filename,
            as_attachment=True,
            download_name=filename  # Ensure correct filename
        )
    except Exception as e:
        app.logger.error(f"Error downloading file {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/downloads/<filename>')
def serve_file(filename):
    """
    File download route
    Serve a downloaded file
    """
    try:
        file_path = file_manager.get_file_path(filename)
        if not os.path.exists(file_path):
            return jsonify({
                'error': 'File not found'
            }), 404
            
        # Get MIME type based on file extension
        mime_type = None  # Let Flask detect the MIME type
        
        # Set response headers for better download handling
        response = send_from_directory(
            directory=app.config['DOWNLOAD_FOLDER'],
            path=filename,
            as_attachment=True,
            download_name=filename.replace('%20', ' ')  # Clean filename
        )
        
        # Add headers for better download handling
        response.headers['Content-Length'] = os.path.getsize(file_path)
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache'
        
        return response
        
    except Exception as e:
        print(f"Download error: {str(e)}")  # Log the error
        return jsonify({
            'error': f'Error downloading file: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Development server with debug mode
    print("Running in development mode with auto-reloading enabled...")
    app.run(debug=True, port=5000)
