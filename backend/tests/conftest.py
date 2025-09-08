"""
Test configuration and fixtures for DankerChat backend tests.
"""

import pytest
import sys
import os
from pathlib import Path

# Add backend src to Python path
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

from flask import Flask
from database import configure_database, create_tables, drop_tables


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
    
    # Use in-memory SQLite for tests
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure database
    configure_database(app)
    
    with app.app_context():
        # This will fail until we implement the Flask app creation
        create_tables(app)
    
    yield app
    
    with app.app_context():
        drop_tables(app)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers():
    """Provide mock authentication headers for testing."""
    # This fixture will provide a mock JWT token for testing
    # Will be implemented when JWT service is created
    return {"Authorization": "Bearer mock_jwt_token"}


@pytest.fixture
def expired_token():
    """Provide an expired JWT token for testing."""
    # This will be a real expired token when JWT service is implemented
    return "expired_jwt_token"


@pytest.fixture
def auth_token():
    """Provide a valid JWT token for WebSocket testing."""
    # This fixture will provide a valid JWT token for WebSocket authentication
    # Will be implemented when JWT service is created
    return "valid_websocket_jwt_token"