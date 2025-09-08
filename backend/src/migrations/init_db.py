"""
Database initialization script for DankerChat application.

Creates all tables and sets up initial data including default roles.
"""

import sys
import os

# Add the backend/src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from flask import Flask
from database import db
# Import all models so SQLAlchemy can discover them
from models.role import Role
from models.user import User
from models.session import Session
from models.channel import Channel
from models.message import Message
from models.direct_conversation import DirectConversation
from models.channel_membership import ChannelMembership


def init_database(app: Flask) -> None:
    """
    Initialize the database with all tables and default data.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        # Drop all tables (for development - remove in production)
        print("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        # Create default roles
        print("Creating default roles...")
        create_default_roles()
        
        print("Database initialization complete!")


def create_default_roles() -> None:
    """Create the default system roles."""
    # Check if roles already exist
    if Role.query.count() > 0:
        print("Roles already exist, skipping creation...")
        return
    
    # Create default roles
    roles = [
        Role(
            name='admin',
            description='System administrator with full permissions',
            permissions={
                'can_create_channels': True,
                'can_delete_channels': True,
                'can_modify_channels': True,
                'can_ban_users': True,
                'can_delete_messages': True,
                'can_create_users': True,
                'can_modify_users': True
            }
        ),
        Role(
            name='moderator',
            description='Channel moderator with content management permissions',
            permissions={
                'can_create_channels': True,
                'can_delete_channels': False,
                'can_modify_channels': True,
                'can_ban_users': True,
                'can_delete_messages': True,
                'can_create_users': False,
                'can_modify_users': False
            }
        ),
        Role(
            name='user',
            description='Regular user with basic chat permissions',
            permissions={
                'can_create_channels': True,
                'can_delete_channels': False,
                'can_modify_channels': False,
                'can_ban_users': False,
                'can_delete_messages': False,
                'can_create_users': False,
                'can_modify_users': False
            }
        )
    ]
    
    for role in roles:
        db.session.add(role)
        print(f"Created role: {role.name}")
    
    db.session.commit()
    print(f"Successfully created {len(roles)} default roles")


def create_sample_data(app: Flask) -> None:
    """
    Create sample data for development/testing.
    
    Args:
        app: Flask application instance
    """
    # Models already imported at top
    import bcrypt
    
    with app.app_context():
        # Get default user role
        user_role = Role.query.filter_by(name='user').first()
        admin_role = Role.query.filter_by(name='admin').first()
        
        if not user_role or not admin_role:
            print("Default roles not found. Run init_database first.")
            return
        
        # Create sample users
        password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        users = [
            User(
                username='admin',
                password_hash=password_hash,
                role_id=str(admin_role.id),
                email='admin@dankerchat.dev',
                display_name='Administrator'
            ),
            User(
                username='alice',
                password_hash=password_hash,
                role_id=str(user_role.id),
                email='alice@example.com',
                display_name='Alice Johnson'
            ),
            User(
                username='bob',
                password_hash=password_hash,
                role_id=str(user_role.id),
                email='bob@example.com',
                display_name='Bob Smith'
            )
        ]
        
        for user in users:
            db.session.add(user)
        
        db.session.flush()  # Get IDs without committing
        
        # Create sample channels
        general_channel = Channel(
            name='general',
            display_name='General Discussion',
            description='General chat for everyone',
            created_by=str(users[0].id),  # Admin creates the channel
            is_private=False
        )
        
        random_channel = Channel(
            name='random',
            display_name='Random',
            description='Random discussions and off-topic chat',
            created_by=str(users[1].id),  # Alice creates the channel
            is_private=False
        )
        
        private_channel = Channel(
            name='private-team',
            display_name='Private Team',
            description='Private channel for team discussions',
            created_by=str(users[0].id),  # Admin creates the channel
            is_private=True,
            max_members=10
        )
        
        db.session.add(general_channel)
        db.session.add(random_channel)
        db.session.add(private_channel)
        db.session.flush()
        
        # Add users to channels
        from models.channel_membership import MembershipRole
        
        memberships = [
            # All users join general channel
            ChannelMembership(str(general_channel.id), str(users[0].id), role=MembershipRole.ADMIN),
            ChannelMembership(str(general_channel.id), str(users[1].id), role=MembershipRole.MEMBER),
            ChannelMembership(str(general_channel.id), str(users[2].id), role=MembershipRole.MEMBER),
            
            # Alice and Bob join random channel
            ChannelMembership(str(random_channel.id), str(users[1].id), role=MembershipRole.ADMIN),
            ChannelMembership(str(random_channel.id), str(users[2].id), role=MembershipRole.MEMBER),
            
            # Only admin in private channel
            ChannelMembership(str(private_channel.id), str(users[0].id), role=MembershipRole.ADMIN),
        ]
        
        for membership in memberships:
            db.session.add(membership)
        
        db.session.commit()
        print(f"Successfully created {len(users)} sample users and {len(memberships)} channel memberships")


if __name__ == '__main__':
    from flask import Flask
    from database import configure_database
    
    # Create Flask app for migration
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dankerchat.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    configure_database(app)
    
    # Initialize database
    init_database(app)
    
    # Optionally create sample data
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--sample-data':
        create_sample_data(app)