"""
Main Flask application for DankerChat backend.

Sets up the Flask app with all blueprints, middleware, and configuration.
Based on specs/001-chat-application/tasks.md T049
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from datetime import datetime
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import configure_database
from api.auth import auth_bp
from api.users import users_bp
from api.channels import channels_bp
from api.messages import messages_bp
from api.admin import admin_bp


def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Configuration dictionary (optional)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure app
    configure_app(app, config)
    
    # Setup database
    configure_database(app)
    
    # Setup CORS
    setup_cors(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup middleware and error handlers
    setup_middleware(app)
    setup_error_handlers(app)
    
    # Setup health check endpoints
    setup_health_endpoints(app)
    
    return app


def configure_app(app, config=None):
    """Configure Flask application settings."""
    
    # Default configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Secret key for JWT tokens
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Production database
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Development SQLite database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dankerchat.db'
    
    # Environment-specific settings
    environment = os.environ.get('FLASK_ENV', 'development')
    
    if environment == 'development':
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
    elif environment == 'testing':
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    elif environment == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
    
    # Override with custom config
    if config:
        app.config.update(config)


def setup_cors(app):
    """Setup Cross-Origin Resource Sharing (CORS)."""
    
    # Configure CORS for frontend integration
    cors_origins = os.environ.get('CORS_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = cors_origins.split(',')
    
    CORS(app, 
         origins=cors_origins,
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=True)


def register_blueprints(app):
    """Register API blueprints."""
    
    # Register all API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(admin_bp)


def setup_middleware(app):
    """Setup middleware for request/response processing."""
    
    @app.before_request
    def before_request():
        """Before request middleware."""
        # Log request info (in development)
        if app.config.get('DEBUG'):
            print(f"[{datetime.utcnow()}] {request.method} {request.path}")
        
        # Set request start time for performance monitoring
        g.start_time = datetime.utcnow()
    
    @app.after_request
    def after_request(response):
        """After request middleware."""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add API version header
        response.headers['X-API-Version'] = '1.0.0'
        
        # Add request duration header (for monitoring)
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


def setup_error_handlers(app):
    """Setup global error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid or malformed',
            'status_code': 400,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource',
            'status_code': 401,
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403,
            'timestamp': datetime.utcnow().isoformat()
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The HTTP method is not allowed for this endpoint',
            'status_code': 405,
            'timestamp': datetime.utcnow().isoformat()
        }), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'status_code': 429,
            'timestamp': datetime.utcnow().isoformat()
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred on the server',
            'status_code': 500,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        # Log the error in production
        if not app.config.get('DEBUG'):
            app.logger.error(f"Unhandled exception: {str(error)}")
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500,
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def setup_health_endpoints(app):
    """Setup health check and system info endpoints."""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Main health check endpoint.
        
        Returns:
            200: Service is healthy
        """
        from database import db
        
        # Check database connectivity
        try:
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            db_status = 'unhealthy'
            app.logger.error(f"Database health check failed: {str(e)}")
        
        health_status = {
            'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'components': {
                'database': db_status,
                'api': 'healthy'
            }
        }
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return jsonify(health_status), status_code
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """
        API health check endpoint.
        
        Returns:
            200: API is healthy
        """
        return jsonify({
            'service': 'dankerchat-api',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }), 200
    
    @app.route('/', methods=['GET'])
    def root():
        """
        Root endpoint with API information.
        
        Returns:
            200: API information
        """
        return jsonify({
            'name': 'DankerChat API',
            'version': '1.0.0',
            'description': 'Multi-interface chat application API',
            'documentation': '/api/docs',
            'health': '/health',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': {
                'authentication': '/api/auth',
                'users': '/api/users',
                'channels': '/api/channels',
                'messages': '/api/messages',
                'admin': '/api/admin'
            }
        }), 200
    
    @app.route('/api', methods=['GET'])
    def api_info():
        """
        API information endpoint.
        
        Returns:
            200: API version and available endpoints
        """
        return jsonify({
            'name': 'DankerChat API',
            'version': '1.0.0',
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': [
                {
                    'name': 'Authentication',
                    'path': '/api/auth',
                    'description': 'User authentication and session management'
                },
                {
                    'name': 'Users',
                    'path': '/api/users',
                    'description': 'User management and profiles'
                },
                {
                    'name': 'Channels',
                    'path': '/api/channels',
                    'description': 'Channel management and membership'
                },
                {
                    'name': 'Messages',
                    'path': '/api/messages',
                    'description': 'Message operations and communication'
                },
                {
                    'name': 'Admin',
                    'path': '/api/admin',
                    'description': 'Administrative operations and system management'
                }
            ]
        }), 200


# Create the application instance
app = create_app()


if __name__ == '__main__':
    """Run the development server."""
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting DankerChat API server...")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Server: http://{host}:{port}")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"API Info: http://{host}:{port}/api")
    
    # Initialize database if needed
    with app.app_context():
        from database import db
        
        # Create tables if they don't exist
        try:
            db.create_all()
            print("Database tables initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize database tables: {str(e)}")
    
    # Run the server
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )