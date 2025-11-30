"""
VidyAI Flask Backend API
Main application file with Flask configuration and route registration
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding for Windows
# Prevent duplicate logs by checking if handlers already exist
logger = logging.getLogger("VidyAI_Flask")
logger.setLevel(logging.INFO)

# Only configure if handlers don't exist (prevents duplicates on reload)
if not logger.handlers:
    # Create file handler
    file_handler = logging.FileHandler("vidyai_flask.log", encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger (avoids duplicate logs)
    logger.propagate = False

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))  # 100MB default

# CORS configuration
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:8080').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Import and register blueprints
from routes.wikipedia_routes import wikipedia_bp
from routes.story_routes import story_bp
from routes.image_routes import image_bp
from routes.narration_routes import narration_bp
from routes.audio_routes import audio_bp
from routes.video_routes import video_bp
from routes.storage_routes import storage_bp
from routes.project_routes import project_bp

# Register blueprints
app.register_blueprint(wikipedia_bp, url_prefix='/api/wikipedia')
app.register_blueprint(story_bp, url_prefix='/api/story')
app.register_blueprint(image_bp, url_prefix='/api/images')
app.register_blueprint(narration_bp, url_prefix='/api/narration')
app.register_blueprint(audio_bp, url_prefix='/api/audio')
app.register_blueprint(video_bp, url_prefix='/api/video')
app.register_blueprint(storage_bp, url_prefix='/api/storage')
app.register_blueprint(project_bp)  # No prefix, it already has /api/projects in the blueprint

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'VidyAI Flask Backend',
        'version': '1.0.0'
    }), 200

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'VidyAI Flask Backend API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'wikipedia': '/api/wikipedia/*',
            'story': '/api/story/*',
            'images': '/api/images/*',
            'narration': '/api/narration/*',
            'audio': '/api/audio/*',
            'video': '/api/video/*',
            'storage': '/api/storage/*'
        }
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal error occurred'
    }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'error': 'Request Entity Too Large',
        'message': f'Maximum upload size is {app.config["MAX_CONTENT_LENGTH"]} bytes'
    }), 413

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting VidyAI Flask Backend on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"CORS origins: {cors_origins}")
    
    app.run(host=host, port=port, debug=debug)

