"""
Test PDF generation endpoint
"""
import sys
import os

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Flask, jsonify
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/api/test-pdf', methods=['GET'])
def test_pdf():
    """Test PDF generation capabilities"""
    
    results = {
        'imports': {},
        'environment': {},
        'test_generation': None
    }
    
    # Test imports
    try:
        import reportlab
        results['imports']['reportlab'] = f"✅ {reportlab.__version__}"
    except Exception as e:
        results['imports']['reportlab'] = f"❌ {str(e)}"
    
    try:
        from PIL import Image
        results['imports']['PIL'] = f"✅ {Image.__version__}"
    except Exception as e:
        results['imports']['PIL'] = f"❌ {str(e)}"
    
    try:
        import requests
        results['imports']['requests'] = f"✅ {requests.__version__}"
    except Exception as e:
        results['imports']['requests'] = f"❌ {str(e)}"
    
    # Check environment
    results['environment']['BLOB_READ_WRITE_TOKEN'] = '✅ Set' if os.getenv('BLOB_READ_WRITE_TOKEN') else '❌ Not set'
    results['environment']['DATABASE_URL'] = '✅ Set' if os.getenv('DATABASE_URL') else '❌ Not set'
    
    # Test PDF generation
    try:
        from backend.mcp_tools.filesystem_mcp_service.filesystem_api import FilesystemAPI
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            fs_api = FilesystemAPI(base_dir=temp_dir)
            
            # Test data
            test_data = {
                'destination': 'Mumbai',
                'duration_days': 2,
                'budget': {
                    'transport': 5000,
                    'accommodation': 6000,
                    'food': 3000,
                    'activities': 4000,
                    'miscellaneous': 1000,
                    'total': 19000,
                    'currency': 'INR'
                },
                'itinerary': {
                    'days': [
                        {
                            'day': 1,
                            'activities': [
                                {
                                    'time': '9:00 AM',
                                    'title': 'Visit Gateway of India',
                                    'description': 'Iconic monument',
                                    'location': {'name': 'Gateway of India'}
                                }
                            ]
                        }
                    ],
                    'total_days': 2
                },
                'map': {
                    'locations': [
                        {
                            'name': 'Gateway of India',
                            'latitude': 18.9220,
                            'longitude': 72.8347,
                            'day': 1,
                            'time': '9:00 AM',
                            'description': 'Historic monument'
                        }
                    ]
                }
            }
            
            pdf_result = fs_api.save_plan_as_pdf(
                destination='Mumbai',
                duration_days=2,
                plan_data=test_data,
                session_id='test'
            )
            
            if pdf_result.get('success'):
                results['test_generation'] = f"✅ PDF generated: {pdf_result['filename']} ({pdf_result['size_kb']} KB)"
            else:
                results['test_generation'] = f"❌ Failed: {pdf_result.get('error')}"
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        results['test_generation'] = f"❌ Exception: {str(e)}"
        logger.error(f"PDF generation test failed: {e}", exc_info=True)
    
    return jsonify(results), 200

# For Vercel
def handler(request):
    with app.request_context(request.environ):
        return app.full_dispatch_request()
