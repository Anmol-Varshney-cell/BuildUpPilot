import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables for Netlify
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DEMO_MODE', 'false')
os.environ.setdefault('SANDBOX_MODE', 'true')

from flask import Flask, request, jsonify
from flask_cors import CORS
import json

# Import your app configuration
from app import app
from routes import main, auth, student, admin, recruiter, api

# Configure CORS for Netlify Functions
CORS(app, origins=['*'])

# Handler for Netlify Functions
def handler(event, context):
    """
    Netlify Functions handler
    """
    try:
        # Parse the event
        if 'body' in event:
            body = json.loads(event['body']) if event['body'] else {}
        else:
            body = {}
        
        # Create a mock request
        with app.test_request_context(
            path=event.get('path', '/'),
            method=event.get('httpMethod', 'GET'),
            json=body,
            headers=event.get('headers', {}),
            query_string=event.get('queryStringParameters', {})
        ):
            # Route the request
            response = app.full_dispatch_request()
            
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5002)
