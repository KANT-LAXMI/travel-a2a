"""
Vercel Serverless Function for Host Agent
==========================================
Simplified host agent that works in Vercel's serverless environment
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/', methods=['POST'])
def handle_task():
    """
    Handle A2A task requests in JSON-RPC format
    
    This is a simplified version for Vercel deployment.
    The full orchestration with SK Planner requires long-running processes.
    """
    try:
        data = request.get_json()
        
        logger.info(f"Received request: {data.get('method')}")
        
        if data.get('method') == 'tasks/send':
            params = data.get('params', {})
            message = params.get('message', {})
            user_text = message.get('parts', [{}])[0].get('text', '')
            
            logger.info(f"User query: {user_text}")
            
            # Simple response for now
            response = {
                "jsonrpc": "2.0",
                "id": data.get('id'),
                "result": {
                    "id": params.get('id'),
                    "sessionId": params.get('sessionId'),
                    "status": {
                        "state": "completed"
                    },
                    "history": [
                        message,
                        {
                            "role": "agent",
                            "parts": [{
                                "type": "text",
                                "text": f"Received your request: {user_text}\n\nNote: Full orchestration with multiple agents is not yet available in serverless mode."
                            }]
                        }
                    ]
                }
            }
            
            return jsonify(response), 200
        
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }), 404
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get('id') if data else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }), 500


# Vercel handler
app = app

if __name__ == "__main__":
    app.run(debug=True, port=10000)
