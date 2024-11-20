from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import os
import subprocess
import threading
import queue
import re
import time
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['DOWNLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
app.config['MAX_FILE_AGE'] = 24  # Maximum age of files in hours before cleanup
app.config['CLEANUP_INTERVAL'] = 1  # Cleanup interval in hours

def cleanup_downloads():
    """Clean up all files in the downloads directory"""
    try:
        if os.path.exists(app.config['DOWNLOAD_FOLDER']):
            for filename in os.listdir(app.config['DOWNLOAD_FOLDER']):
                file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {filename}: {str(e)}")
        return True
    except Exception as e:
        print(f"Error cleaning downloads: {str(e)}")
        return False

# Clean downloads on startup
print("Cleaning up downloads directory...")
cleanup_downloads()
print("Cleanup complete")

# Create downloads directory if it doesn't exist
if not os.path.exists(app.config['DOWNLOAD_FOLDER']):
    os.makedirs(app.config['DOWNLOAD_FOLDER'])

# Global variables for tracking downloads
download_progress = {}
download_queue = queue.Queue()

def cleanup_old_files():
    """Remove files older than MAX_FILE_AGE hours"""
    while True:
        try:
            max_age = timedelta(hours=app.config['MAX_FILE_AGE'])
            current_time = datetime.now()
            
            # Scan download directory
            for filename in os.listdir(app.config['DOWNLOAD_FOLDER']):
                file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
                if os.path.isfile(file_path):
                    # Get file's last modification time
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Remove if file is older than MAX_FILE_AGE
                    if current_time - file_time > max_age:
                        try:
                            os.remove(file_path)
                            print(f"Cleaned up old file: {filename}")
                        except Exception as e:
                            print(f"Error removing file {filename}: {str(e)}")
            
            # Sleep for cleanup interval
            time.sleep(app.config['CLEANUP_INTERVAL'] * 3600)
        except Exception as e:
            print(f"Error in cleanup thread: {str(e)}")
            time.sleep(300)  # Sleep for 5 minutes on error

def process_download_output(process, task_id):
    total_tracks = 0
    current_track = 0
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
            
        line = line.strip()
        if line:
            # Update progress based on output
            if "Found" in line and "tracks" in line:
                match = re.search(r'Found (\d+) tracks', line)
                if match:
                    total_tracks = int(match.group(1))
                    download_progress[task_id].update({
                        'total_tracks': total_tracks,
                        'status': 'downloading'
                    })
            elif "Downloaded" in line:
                current_track += 1
                download_progress[task_id].update({
                    'current_track': current_track,
                    'status': 'downloading'
                })
    
    # Check if download was successful
    if process.poll() == 0:
        download_progress[task_id]['status'] = 'completed'
    else:
        download_progress[task_id]['status'] = 'failed'
        error_output = process.stderr.read()
        download_progress[task_id]['error'] = error_output

def download_worker():
    while True:
        task = download_queue.get()
        if task is None:
            break
            
        task_id, command = task
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            process_download_output(process, task_id)
            
        except Exception as e:
            download_progress[task_id].update({
                'status': 'failed',
                'error': str(e)
            })
            
        finally:
            download_queue.task_done()

# Start worker threads
download_thread = threading.Thread(target=download_worker, daemon=True)
download_thread.start()

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    # Get list of downloaded files with their ages
    files = []
    current_time = datetime.now()
    
    if os.path.exists(app.config['DOWNLOAD_FOLDER']):
        for filename in os.listdir(app.config['DOWNLOAD_FOLDER']):
            file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                # Calculate time until deletion
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                time_left = app.config['MAX_FILE_AGE'] - (current_time - file_time).total_seconds() / 3600
                
                if time_left > 0:  # Only show files that haven't expired
                    files.append({
                        'name': filename,
                        'size': f"{size / 1024 / 1024:.2f} MB",
                        'download_url': url_for('download_file', filename=filename),
                        'time_left': f"{time_left:.1f} hours" if time_left > 1 else f"{time_left * 60:.0f} minutes"
                    })
    
    return render_template('index.html', files=files)

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        spotify_url = data.get('spotify_url')
        src_aud = data.get('source', 'youtube-music')
        format = data.get('format', 'mp3')
        bitrate = data.get('bitrate', '320k')

        if not spotify_url:
            return jsonify({'error': 'Spotify URL is required'}), 400

        # Generate a unique task ID
        task_id = os.urandom(8).hex()
        
        # Initialize progress tracking for this download
        download_progress[task_id] = {
            'status': 'starting',
            'total_tracks': 0,
            'current_track': 0
        }

        # Form the command based on the parameters
        command = [
            "spotdl",
            spotify_url,
            "--audio", src_aud,
            "--format", format,
            "--bitrate", bitrate,
            "--output", app.config['DOWNLOAD_FOLDER']
        ]

        # Add task to download queue
        download_queue.put((task_id, command))

        return jsonify({
            'status': 'started',
            'task_id': task_id,
            'message': 'Download started'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    if task_id not in download_progress:
        return jsonify({'error': 'Invalid task ID'}), 404
        
    progress_data = download_progress[task_id]
    
    # If download is complete, include file list with time remaining
    if progress_data['status'] == 'completed':
        files = []
        current_time = datetime.now()
        for filename in os.listdir(app.config['DOWNLOAD_FOLDER']):
            file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                time_left = app.config['MAX_FILE_AGE'] - (current_time - file_time).total_seconds() / 3600
                
                files.append({
                    'name': filename,
                    'size': f"{size / 1024 / 1024:.2f} MB",
                    'download_url': url_for('download_file', filename=filename),
                    'time_left': f"{time_left:.1f} hours" if time_left > 1 else f"{time_left * 60:.0f} minutes"
                })
        progress_data['files'] = files
        
    return jsonify(progress_data)

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    # Development server with debug mode
    print("Running in development mode with auto-reloading enabled...")
    app.run(debug=True, port=5000)
