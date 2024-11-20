"""
File Manager Component
Handles all file-related operations including cleanup, listing, and organization.
"""

import os
import time
from typing import List, Dict
from flask import url_for
from urllib.parse import quote

class FileManager:
    def __init__(self, download_folder: str, max_age_hours: int = 24):
        """
        Initialize FileManager
        
        Args:
            download_folder (str): Path to downloads directory
            max_age_hours (int): Maximum age of files in hours before cleanup
        """
        self.download_folder = download_folder
        self.max_age_hours = max_age_hours
        
        # Create download folder if it doesn't exist
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
    
    def list_files(self) -> List[Dict]:
        """
        List all files in the download folder, sorted by newest first
        
        Returns:
            List[Dict]: List of file information dictionaries
        """
        files = []
        if not os.path.exists(self.download_folder):
            return files
            
        file_list = []
        for filename in os.listdir(self.download_folder):
            file_path = os.path.join(self.download_folder, filename)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                mod_time = os.path.getmtime(file_path)
                
                # Only list audio files
                if filename.lower().endswith(('.mp3', '.m4a', '.ogg', '.opus', '.flac', '.wav')):
                    # URL encode the filename for download
                    safe_filename = quote(filename)
                    
                    # Clean up display name
                    display_name = os.path.splitext(filename)[0]
                    
                    file_list.append({
                        'filename': safe_filename,  # URL-safe filename for download
                        'display_name': display_name,  # Clean name for display
                        'size': f"{size / 1024 / 1024:.1f} MB",
                        'mod_time': mod_time
                    })
        
        # Sort by modification time, newest first
        file_list.sort(key=lambda x: x['mod_time'], reverse=True)
        
        # Remove mod_time from final output
        return [{k: v for k, v in f.items() if k != 'mod_time'} 
                for f in file_list]
    
    def cleanup_old_files(self) -> None:
        """
        Remove files older than max_age_hours
        """
        if not os.path.exists(self.download_folder):
            return
            
        current_time = time.time()
        max_age_seconds = self.max_age_hours * 3600
        
        for filename in os.listdir(self.download_folder):
            file_path = os.path.join(self.download_folder, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        # Log error but continue cleanup
                        print(f"Error removing file {filename}: {str(e)}")
    
    def get_file_path(self, filename: str) -> str:
        """
        Get absolute path for a file in the download directory
        
        Args:
            filename (str): Name of the file
            
        Returns:
            str: Absolute path to the file
        """
        # URL decode the filename first
        from urllib.parse import unquote
        filename = unquote(filename)
        
        # Clean the filename and ensure it's safe
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(self.download_folder, safe_filename)
        
        # Convert to absolute path
        abs_file_path = os.path.abspath(file_path)
        abs_download_folder = os.path.abspath(self.download_folder)
        
        # Verify the path is within download folder
        if not abs_file_path.startswith(abs_download_folder):
            raise ValueError("Invalid file path")
            
        return file_path
