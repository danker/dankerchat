"""
Role model for DankerChat application.

Represents permission sets assigned to users.
Based on specs/001-chat-application/data-model.md
"""

import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db


class Role(db.Model):
    """
    Role model representing user permission sets.
    
    Attributes:
        id: Primary key (UUID)
        name: Role name ('admin', 'moderator', 'user')
        description: Role description
        permissions: JSON field with permission flags
    """
    
    __tablename__ = 'roles'
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()))
    
    # Role identification
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Permission configuration
    permissions: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Relationships
    users: Mapped[List['User']] = relationship(
        'User',
        back_populates='role',
        lazy='dynamic'
    )
    
    def __init__(self, name: str, description: Optional[str] = None, 
                 permissions: Optional[Dict[str, Any]] = None):
        """
        Initialize a new Role.
        
        Args:
            name: Role name (e.g., 'admin', 'moderator', 'user')
            description: Optional role description
            permissions: Permission flags dictionary
        """
        self.name = name
        self.description = description
        self.permissions = permissions or self._get_default_permissions(name)
    
    def __repr__(self) -> str:
        """String representation of Role."""
        return f'<Role {self.name}>'
    
    def to_dict(self) -> dict:
        """
        Convert Role to dictionary representation.
        
        Returns:
            Dictionary representation of the role
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions
        }
    
    @staticmethod
    def _get_default_permissions(role_name: str) -> Dict[str, bool]:
        """
        Get default permissions for a role name.
        
        Args:
            role_name: Name of the role
            
        Returns:
            Dictionary of permission flags
        """
        if role_name == 'admin':
            return {
                'can_create_channels': True,
                'can_delete_channels': True,
                'can_modify_channels': True,
                'can_ban_users': True,
                'can_delete_messages': True,
                'can_create_users': True,
                'can_modify_users': True
            }
        elif role_name == 'moderator':
            return {
                'can_create_channels': True,
                'can_delete_channels': False,
                'can_modify_channels': True,
                'can_ban_users': True,
                'can_delete_messages': True,
                'can_create_users': False,
                'can_modify_users': False
            }
        else:  # 'user' or any other role
            return {
                'can_create_channels': True,
                'can_delete_channels': False,
                'can_modify_channels': False,
                'can_ban_users': False,
                'can_delete_messages': False,
                'can_create_users': False,
                'can_modify_users': False
            }
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if role has a specific permission.
        
        Args:
            permission: Permission name to check
            
        Returns:
            True if role has permission, False otherwise
        """
        return self.permissions.get(permission, False)
    
    def update_permission(self, permission: str, value: bool) -> None:
        """
        Update a specific permission for this role.
        
        Args:
            permission: Permission name
            value: Permission value (True/False)
        """
        self.permissions[permission] = value
        # Mark the JSON field as modified for SQLAlchemy
        db.session.merge(self)
    
    @classmethod
    def create_default_roles(cls) -> List['Role']:
        """
        Create the default system roles.
        
        Returns:
            List of default Role objects
        """
        roles = [
            cls(
                name='admin',
                description='System administrator with full permissions'
            ),
            cls(
                name='moderator', 
                description='Channel moderator with content management permissions'
            ),
            cls(
                name='user',
                description='Regular user with basic chat permissions'
            )
        ]
        
        return roles
    
    @classmethod
    def get_default_user_role(cls) -> 'Role':
        """
        Get the default role for new users.
        
        Returns:
            Default user Role object
        """
        return cls.query.filter_by(name='user').first()
    
    @classmethod
    def get_admin_role(cls) -> 'Role':
        """
        Get the admin role.
        
        Returns:
            Admin Role object
        """
        return cls.query.filter_by(name='admin').first()
    
    def is_admin(self) -> bool:
        """
        Check if this is an admin role.
        
        Returns:
            True if admin role, False otherwise
        """
        return self.name == 'admin'
    
    def is_moderator(self) -> bool:
        """
        Check if this is a moderator role.
        
        Returns:
            True if moderator role, False otherwise
        """
        return self.name == 'moderator'
    
    def can_manage_channels(self) -> bool:
        """
        Check if role can manage channels.
        
        Returns:
            True if can create/modify channels, False otherwise
        """
        return (self.has_permission('can_create_channels') or
                self.has_permission('can_modify_channels'))
    
    def can_moderate_content(self) -> bool:
        """
        Check if role can moderate content.
        
        Returns:
            True if can delete messages or ban users, False otherwise
        """
        return (self.has_permission('can_delete_messages') or
                self.has_permission('can_ban_users'))