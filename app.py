"""
VidyAI Flask Backend API
Main application file with Flask configuration and route registration
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging (console-only for deployment; no local file writes)
# Use WARNING level in production to reduce I/O overhead, INFO in development
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    log_level = 'INFO'

logger = logging.getLogger("VidyAI_Flask")
logger.setLevel(getattr(logging, log_level))

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    # Simplified formatter for production (less overhead)
    if log_level == 'WARNING':
        formatter = logging.Formatter('%(levelname)s - %(message)s')
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))  # 100MB default

# CORS configuration - MUST be initialized before routes and middleware
cors_origins_env = os.getenv('CORS_ORIGINS', 'http://localhost:8080,https://vizuara-vidyai.vercel.app')
# Strip whitespace and trailing slashes from origins
cors_origins = [origin.strip().rstrip('/') for origin in cors_origins_env.split(',') if origin.strip()]

# Store in app config for access from routes
app.config['CORS_ORIGINS'] = cors_origins

# Configure CORS - use multiple patterns to ensure all routes are covered
# Flask-CORS will automatically handle OPTIONS preflight requests
cors = CORS(app, 
    resources={
        r"/api/.*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
            "expose_headers": ["Content-Type", "Content-Length"],
            "supports_credentials": True,
            "max_age": 3600
        },
        r"/api/health": {
            "origins": cors_origins,
            "methods": ["GET", "OPTIONS", "HEAD"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
            "supports_credentials": True,
            "max_age": 3600
        },
        r"/": {
            "origins": cors_origins,
            "methods": ["GET", "OPTIONS", "HEAD"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
            "supports_credentials": True
        }
    },
    supports_credentials=True,
    automatic_options=True,
    intercept_exceptions=True
)

# Add request logging middleware AFTER CORS initialization
# Only log errors and warnings in production to reduce I/O overhead
@app.before_request
def log_request_info():
    """Log incoming requests for debugging"""
    if log_level == 'DEBUG':
        logger.debug(f"Request: {request.method} {request.path} from {request.remote_addr}")
    # Only log OPTIONS in debug mode (too verbose otherwise)
    if request.method == 'OPTIONS' and log_level == 'DEBUG':
        logger.debug(f"OPTIONS preflight - Origin: {request.headers.get('Origin')}")

@app.after_request
def log_response_info(response):
    """Log response status for debugging - ensure CORS headers are present"""
    # Only log errors (4xx, 5xx) in production
    if response.status_code >= 400:
        logger.warning(f"Error {response.status_code} for {request.method} {request.path}")
    elif log_level == 'DEBUG':
        logger.debug(f"Response: {response.status_code} for {request.method} {request.path}")
    return response

# Import and register blueprints
try:
    from routes.wikipedia_routes import wikipedia_bp
    from routes.story_routes import story_bp
    from routes.image_routes import image_bp
    from routes.narration_routes import narration_bp
    from routes.audio_routes import audio_bp
    from routes.video_routes import video_bp
    from routes.storage_routes import storage_bp
    from routes.project_routes import project_bp
    from routes.progress_routes import progress_bp
    
    # Register blueprints
    app.register_blueprint(wikipedia_bp, url_prefix='/api/wikipedia')
    app.register_blueprint(story_bp, url_prefix='/api/story')
    app.register_blueprint(image_bp, url_prefix='/api/images')
    app.register_blueprint(narration_bp, url_prefix='/api/narration')
    app.register_blueprint(audio_bp, url_prefix='/api/audio')
    app.register_blueprint(video_bp, url_prefix='/api/video')
    app.register_blueprint(storage_bp, url_prefix='/api/storage')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(project_bp)  # No prefix, it already has /api/projects in the blueprint
    
    logger.info("All blueprints registered successfully")
except Exception as e:
    logger.error(f"Failed to import or register blueprints: {e}", exc_info=True)
    raise

# Health check endpoint
@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint - simple endpoint that doesn't require external services"""
    # Handle OPTIONS preflight request explicitly
    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin')
        # Normalize origin by removing trailing slash for comparison
        origin_normalized = origin.rstrip('/') if origin else None
        logger.info(f"Health check OPTIONS handler called - Origin: {origin}, Normalized: {origin_normalized}, Allowed origins: {cors_origins}")
        
        # Check if origin (normalized) is in allowed list
        if origin_normalized and origin_normalized in cors_origins:
            response = jsonify({})
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS, HEAD')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '3600')
            logger.info(f"Returning OPTIONS response with CORS headers for origin: {origin}")
            return response, 200
        else:
            logger.warning(f"OPTIONS request from disallowed origin: {origin} (not in {cors_origins})")
            # Still return CORS headers but with error status
            response = jsonify({'error': 'Origin not allowed'})
            if origin:
                response.headers.add('Access-Control-Allow-Origin', origin)
            return response, 403
    
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'VidyAI Flask Backend',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

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

