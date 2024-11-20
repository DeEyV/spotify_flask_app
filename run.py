# run.py - Production Server
import os
import platform

from app import app

if __name__ == '__main__':
    system = platform.system().lower()
    
    if system == 'windows':
        # Windows: Use Waitress for production
        from waitress import serve
        print("Running production server on Windows using Waitress...")
        serve(app, host='0.0.0.0', port=5000)
    
    elif system == 'darwin' or system == 'linux':
        # Mac/Linux: Use Gunicorn for production
        print("Running production server on Mac/Linux using Gunicorn...")
        os.system('gunicorn app:app')
    
    else:
        # Fallback to Flask production server
        print("Running Flask production server...")
        app.run(host='0.0.0.0', port=5000, debug=False)