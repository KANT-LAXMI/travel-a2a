"""
Vercel Serverless API Entry Point
==================================
Optimized backend for Vercel deployment with semantic-kernel.
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the Flask app
from backend.api.app import app

# Vercel handler
app = app

# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=5000)
