"""
Admin API endpoints for DankerChat application.

Provides REST endpoints for administrative operations including system management, monitoring, and moderation.
Based on specs/001-chat-application/tasks.md T048
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from services.auth import require_auth, require_permission
from services.admin import AdminService, AdminError
from services.auth import AuthorizationError


admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/stats', methods=['GET'])
@require_auth
@require_permission('can_modify_users')
def get_system_stats():
    """
    Get comprehensive system statistics (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: System statistics
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        
        stats = AdminService.get_system_stats(admin)
        
        return jsonify(stats), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/activity-report', methods=['GET'])
@require_auth
@require_permission('can_modify_users')
def get_activity_report():
    """
    Generate activity report for specified time period (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        days: Number of days to analyze (default: 7, max: 30)
    
    Returns:
        200: Activity report
        400: Invalid parameters
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        days = request.args.get('days', 7, type=int)
        
        if days < 1 or days > 30:
            return jsonify({'error': 'days must be between 1 and 30'}), 400
        
        report = AdminService.get_activity_report(admin, days)
        
        return jsonify(report), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/users', methods=['GET'])
@require_auth
@require_permission('can_modify_users')
def get_user_management_list():
    """
    Get paginated list of users for management (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        page: Page number (default: 1)
        per_page: Results per page (default: 50, max: 100)
        role: Filter by role name
        status: Filter by status ('active', 'inactive')
        search: Search in username/email/display_name
    
    Returns:
        200: Paginated user list
        400: Invalid parameters
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        filter_role = request.args.get('role')
        filter_status = request.args.get('status')
        search_query = request.args.get('search')
        
        if page < 1:
            return jsonify({'error': 'page must be >= 1'}), 400
        
        if per_page < 1 or per_page > 100:
            return jsonify({'error': 'per_page must be between 1 and 100'}), 400
        
        if filter_status and filter_status not in ['active', 'inactive']:
            return jsonify({'error': 'status must be active or inactive'}), 400
        
        result = AdminService.get_user_management_list(
            admin=admin,
            page=page,
            per_page=per_page,
            filter_role=filter_role,
            filter_status=filter_status,
            search_query=search_query
        )
        
        return jsonify(result), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/moderation/queue', methods=['GET'])
@require_auth
@require_permission('can_delete_messages')
def get_moderation_queue():
    """
    Get content moderation queue (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        limit: Maximum items (default: 50, max: 100)
    
    Returns:
        200: Content moderation queue
        400: Invalid parameters
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        limit = request.args.get('limit', 50, type=int)
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        queue = AdminService.get_content_moderation_queue(admin, limit)
        
        return jsonify({
            'queue': queue,
            'total': len(queue),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/moderation/messages/<message_id>', methods=['POST'])
@require_auth
@require_permission('can_delete_messages')
def moderate_content(message_id):
    """
    Take moderation action on content (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        message_id: Message ID to moderate
    
    Request body:
    {
        "action": "string (delete|restore|flag)",
        "reason": "string (optional)"
    }
    
    Returns:
        200: Moderation action taken
        400: Invalid action or validation error
        404: Message not found
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        action = data.get('action')
        reason = data.get('reason')
        
        if not action:
            return jsonify({'error': 'action is required'}), 400
        
        if action not in ['delete', 'restore', 'flag']:
            return jsonify({'error': 'action must be delete, restore, or flag'}), 400
        
        success = AdminService.moderate_content(admin, message_id, action, reason)
        
        if success:
            return jsonify({
                'message': f'Message {action} action completed successfully',
                'message_id': message_id,
                'action': action,
                'reason': reason
            }), 200
        else:
            return jsonify({'error': f'Failed to {action} message'}), 500
            
    except AdminError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/system/health', methods=['GET'])
@require_auth
@require_permission('can_modify_users')
def get_system_health():
    """
    Get system health and performance metrics (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: System health metrics
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        
        health = AdminService.get_system_health(admin)
        
        return jsonify(health), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/system/maintenance', methods=['POST'])
@require_auth
@require_permission('can_modify_users')
def perform_maintenance():
    """
    Perform system maintenance tasks (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "tasks": ["string array of task names"]
    }
    
    Available tasks:
    - cleanup_sessions
    - archive_old_conversations
    - cleanup_deleted_messages
    - update_statistics
    
    Returns:
        200: Maintenance completed
        400: Invalid tasks
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        tasks = data.get('tasks', [])
        
        if not isinstance(tasks, list) or not tasks:
            return jsonify({'error': 'tasks must be a non-empty array'}), 400
        
        valid_tasks = [
            'cleanup_sessions',
            'archive_old_conversations', 
            'cleanup_deleted_messages',
            'update_statistics'
        ]
        
        invalid_tasks = [task for task in tasks if task not in valid_tasks]
        if invalid_tasks:
            return jsonify({
                'error': f'Invalid tasks: {invalid_tasks}',
                'valid_tasks': valid_tasks
            }), 400
        
        results = AdminService.perform_maintenance(admin, tasks)
        
        return jsonify({
            'message': 'Maintenance tasks completed',
            'results': results
        }), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/users/bulk', methods=['POST'])
@require_auth
@require_permission('can_modify_users')
def bulk_user_operation():
    """
    Perform bulk operations on multiple users (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "user_ids": ["array of user IDs"],
        "operation": "string (deactivate|reactivate|change_role)",
        "new_role": "string (required for change_role operation)"
    }
    
    Returns:
        200: Bulk operation results
        400: Invalid parameters or validation error
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        admin = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        user_ids = data.get('user_ids', [])
        operation = data.get('operation')
        new_role = data.get('new_role')
        
        if not isinstance(user_ids, list) or not user_ids:
            return jsonify({'error': 'user_ids must be a non-empty array'}), 400
        
        if not operation:
            return jsonify({'error': 'operation is required'}), 400
        
        if operation not in ['deactivate', 'reactivate', 'change_role']:
            return jsonify({'error': 'operation must be deactivate, reactivate, or change_role'}), 400
        
        if operation == 'change_role' and not new_role:
            return jsonify({'error': 'new_role is required for change_role operation'}), 400
        
        kwargs = {}
        if new_role:
            kwargs['new_role'] = new_role
        
        results = AdminService.bulk_user_operation(admin, user_ids, operation, **kwargs)
        
        return jsonify({
            'message': f'Bulk {operation} operation completed',
            'results': results
        }), 200
        
    except AdminError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/roles', methods=['GET'])
@require_auth
@require_permission('can_modify_users')
def get_roles():
    """
    Get list of available roles (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: List of roles
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        from models.role import Role
        
        roles = Role.query.all()
        roles_data = [role.to_dict() for role in roles]
        
        return jsonify({
            'roles': roles_data,
            'total': len(roles_data)
        }), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/roles', methods=['POST'])
@require_auth
@require_permission('can_modify_users')
def create_role():
    """
    Create a new role (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "name": "string (required, unique)",
        "description": "string (optional)",
        "permissions": "object (permission keys and boolean values)"
    }
    
    Returns:
        201: Role created
        400: Validation error or role exists
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        name = data.get('name')
        description = data.get('description')
        permissions = data.get('permissions', {})
        
        if not name:
            return jsonify({'error': 'name is required'}), 400
        
        from models.role import Role
        from database import db
        
        # Check if role already exists
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            return jsonify({'error': 'Role already exists'}), 400
        
        # Create role
        role = Role(
            name=name,
            description=description,
            permissions=permissions
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'message': 'Role created successfully',
            'role': role.to_dict()
        }), 201
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/roles/<role_id>', methods=['PUT'])
@require_auth
@require_permission('can_modify_users')
def update_role(role_id):
    """
    Update a role (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        role_id: Role ID
    
    Request body:
    {
        "description": "string (optional)",
        "permissions": "object (permission keys and boolean values, optional)"
    }
    
    Returns:
        200: Role updated
        404: Role not found
        400: Validation error
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        from models.role import Role
        from database import db
        
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        description = data.get('description')
        permissions = data.get('permissions')
        
        if description is not None:
            role.description = description
        
        if permissions is not None:
            if not isinstance(permissions, dict):
                return jsonify({'error': 'permissions must be an object'}), 400
            role.permissions = permissions
        
        role.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Role updated successfully',
            'role': role.to_dict()
        }), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/roles/<role_id>', methods=['DELETE'])
@require_auth
@require_permission('can_modify_users')
def delete_role(role_id):
    """
    Delete a role (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        role_id: Role ID
    
    Returns:
        200: Role deleted
        404: Role not found
        400: Cannot delete role
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        from models.role import Role
        from models.user import User
        from database import db
        
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        # Cannot delete default roles
        if role.name in ['admin', 'moderator', 'user']:
            return jsonify({'error': 'Cannot delete default system roles'}), 400
        
        # Check if any users have this role
        users_with_role = User.query.filter_by(role_id=str(role.id)).count()
        if users_with_role > 0:
            return jsonify({
                'error': f'Cannot delete role: {users_with_role} users still have this role'
            }), 400
        
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({'message': 'Role deleted successfully'}), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@admin_bp.route('/system/config', methods=['GET'])
@require_auth
@require_permission('can_modify_users')
def get_system_config():
    """
    Get system configuration (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: System configuration
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        # This would typically load from a configuration file or database
        config = {
            'max_channels_per_user': 100,
            'max_message_length': 5000,
            'max_channel_members': 200,
            'session_timeout_hours': 24,
            'max_failed_logins': 5,
            'registration_enabled': True,
            'public_channel_creation': True,
            'private_channel_creation': True,
            'message_editing_enabled': True,
            'message_deletion_enabled': True
        }
        
        return jsonify({
            'config': config,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Health check endpoint
@admin_bp.route('/health', methods=['GET'])
def admin_health():
    """
    Admin service health check.
    
    Returns:
        200: Service healthy
    """
    return jsonify({
        'service': 'admin',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Error handlers for the admin blueprint
@admin_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@admin_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401


@admin_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403


@admin_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@admin_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500