"""Database configuration and setup for DankerChat."""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData

# SQLAlchemy instance
db = SQLAlchemy()

def configure_database(app: Flask) -> None:
    """Configure database for the Flask application."""
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///dankerchat.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'echo': app.config.get('DEBUG', False),
        'pool_pre_ping': True,
    }
    
    # Initialize SQLAlchemy
    db.init_app(app)

def create_tables(app: Flask) -> None:
    """Create all database tables."""
    with app.app_context():
        db.create_all()

def drop_tables(app: Flask) -> None:
    """Drop all database tables (for testing).""" 
    with app.app_context():
        db.drop_all()