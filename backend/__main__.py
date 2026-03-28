"""
Backend Application Entry Point
================================
Allows running backend as a module: python -m backend
"""

from backend.api.app import app

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
