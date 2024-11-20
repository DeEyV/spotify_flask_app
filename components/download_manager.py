"""
Download Manager Component
Handles download tasks, progress tracking, and task cleanup.
"""

import os
import queue
import subprocess
import threading
import time
from typing import Dict, List, Optional, Tuple

class DownloadManager:
    def __init__(self, download_folder: str):
        """
        Initialize DownloadManager
        
        Args:
            download_folder (str): Path to downloads directory
        """
        self.download_folder = download_folder
        
        # Create download folder if it doesn't exist
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
            
        self.download_queue = queue.Queue()
        self.download_progress: Dict = {}
        self.active_tasks = set()
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._process_download_queue, daemon=True)
        self.worker_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_tasks, daemon=True)
        self.cleanup_thread.start()
    
    def start_download(self, spotify_url: str, format: str = 'mp3', bitrate: str = '320k') -> str:
        """
        Start a new download task
        
        Args:
            spotify_url (str): Spotify URL to download
            format (str): Audio format (mp3, ogg, m4a)
            bitrate (str): Audio bitrate (e.g., '320k')
            
        Returns:
            str: Task ID for tracking progress
        """
        try:
            # Clear previous downloads
            self._clear_download_folder()
            
            # Generate unique task ID
            task_id = os.urandom(8).hex()
            self.active_tasks.add(task_id)
            
            # Initialize progress tracking
            self.download_progress[task_id] = {
                'status': 'starting',
                'progress': 0,
                'message': 'Initializing download...',
                'error': None
            }
            
            # Ensure bitrate has 'k' suffix
            if not bitrate.endswith('k'):
                bitrate = f"{bitrate}k"
            
            # Create spotdl command with correct argument order for v4.2.10
            command = [
                "python",
                "-m",
                "spotdl",
                "--format", format,
                "--bitrate", bitrate,
                "--output", self.download_folder,
                spotify_url
            ]
            
            print(f"Starting download for URL: {spotify_url}")
            print(f"Starting download for task {task_id}: {' '.join(command)}")  # Debug log
            
            # Add task to queue
            self.download_queue.put((task_id, command))
            
            return task_id
            
        except Exception as e:
            print(f"Error starting download: {str(e)}")
            if task_id in self.download_progress:
                self.download_progress[task_id]['status'] = 'error'
            raise

    def _clear_download_folder(self) -> None:
        """
        Clear all files from the download folder
        """
        try:
            if os.path.exists(self.download_folder):
                for filename in os.listdir(self.download_folder):
                    filepath = os.path.join(self.download_folder, filename)
                    try:
                        if os.path.isfile(filepath):
                            os.unlink(filepath)
                    except Exception as e:
                        print(f"Error deleting file {filepath}: {str(e)}")  # Debug log
        except Exception as e:
            print(f"Error clearing download folder: {str(e)}")  # Debug log
    
    def get_progress(self, task_id: str) -> Optional[Dict]:
        """
        Get progress for a specific task
        
        Args:
            task_id (str): Task ID to check
            
        Returns:
            Optional[Dict]: Progress data if task exists, None otherwise
        """
        if task_id in self.download_progress:
            return self.download_progress[task_id]
        elif task_id in self.active_tasks:
            # Task exists but no progress yet
            return {
                'status': 'starting',
                'progress': 0,
                'message': 'Initializing download...'
            }
        return None

    def _process_download_queue(self):
        """Process downloads in the queue"""
        while True:
            try:
                # Get next task from queue
                task_id, command = self.download_queue.get()
                
                if task_id not in self.download_progress:
                    continue
                    
                # Update status to downloading
                self.download_progress[task_id]['status'] = 'downloading'
                self.download_progress[task_id]['message'] = 'Download in progress...'
                
                try:
                    # Start download process
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Monitor process output
                    start_time = time.time()
                    last_output_time = start_time
                    partial_files = set()
                    
                    while True:
                        # Read output and error streams
                        output = process.stdout.readline() if process.stdout else ''
                        error = process.stderr.readline() if process.stderr else ''
                        
                        # Update last output time if we got any output
                        if output or error:
                            last_output_time = time.time()
                            
                        # Log output for debugging
                        if output:
                            print(f"Task {task_id} output: {output.strip()}")
                        if error:
                            print(f"Task {task_id} error: {error.strip()}")
                            
                        # Check for completion or errors
                        if process.poll() is not None:
                            break
                            
                        # Check for partial and completed files
                        files = os.listdir(self.download_folder)
                        current_files = {f for f in files if f.endswith(('.mp3', '.m4a', '.ogg', '.flac', '.opus', '.wav'))}
                        
                        # Detect new files
                        new_files = current_files - partial_files
                        if new_files:
                            partial_files = current_files
                            self.download_progress[task_id]['message'] = f'Processing audio... ({len(partial_files)} files)'
                            
                        # Check for completed files (no .part extension)
                        completed_files = {f for f in current_files if not f.endswith('.part')}
                        if completed_files:
                            self.download_progress[task_id]['status'] = 'completed'
                            self.download_progress[task_id]['message'] = 'Download completed!'
                            self.download_progress[task_id]['progress'] = 100
                            process.terminate()
                            break
                            
                        # Check for timeout (no output for 5 minutes)
                        if time.time() - last_output_time > 300:  # 5 minutes
                            raise TimeoutError("Download timed out - no output for 5 minutes")
                            
                        # Check for overall timeout (15 minutes)
                        if time.time() - start_time > 900:  # 15 minutes
                            raise TimeoutError("Download timed out after 15 minutes")
                            
                        # Small sleep to prevent CPU overuse
                        time.sleep(0.5)
                        
                    # Final status check
                    if process.returncode == 0:
                        files = os.listdir(self.download_folder)
                        completed_files = [f for f in files if f.endswith(('.mp3', '.m4a', '.ogg', '.flac', '.opus', '.wav'))]
                        if completed_files:
                            self.download_progress[task_id]['status'] = 'completed'
                            self.download_progress[task_id]['message'] = 'Download completed!'
                            self.download_progress[task_id]['progress'] = 100
                        else:
                            raise Exception("No output files found after process completion")
                    else:
                        error_output = process.stderr.read() if process.stderr else 'Unknown error'
                        raise Exception(f"Process failed with error: {error_output}")
                    
                except Exception as e:
                    print(f"Error during download for task {task_id}: {str(e)}")
                    self.download_progress[task_id]['status'] = 'error'
                    self.download_progress[task_id]['message'] = f'Download failed: {str(e)}'
                    self.download_progress[task_id]['error'] = str(e)
                
                finally:
                    # Cleanup
                    if task_id in self.active_tasks:
                        self.active_tasks.remove(task_id)
                    
            except Exception as e:
                print(f"Error in download queue processor: {str(e)}")
                continue

    def _cleanup_tasks(self):
        """
        Cleanup completed/failed tasks after 5 minutes
        """
        while True:
            try:
                to_remove = []
                current_time = time.time()
                
                for task_id, progress in self.download_progress.items():
                    # Only cleanup completed or error tasks
                    if progress['status'] in ['completed', 'error']:
                        to_remove.append(task_id)
                        if task_id in self.active_tasks:
                            self.active_tasks.remove(task_id)
                
                for task_id in to_remove:
                    del self.download_progress[task_id]
                    
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Cleanup error: {str(e)}")
                time.sleep(60)  # Wait and retry on error
