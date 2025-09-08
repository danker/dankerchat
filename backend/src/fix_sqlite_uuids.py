"""
Script to fix UUID columns for SQLite compatibility.
Replaces PostgreSQL UUID types with String(36) for SQLite.
"""

import os
import re

def fix_uuid_columns(file_path):
    """Fix UUID columns in a model file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove PostgreSQL UUID import
    content = re.sub(r'from sqlalchemy\.dialects\.postgresql import UUID\n', '', content)
    
    # Replace UUID(as_uuid=True) with String(36)
    content = re.sub(r'UUID\(as_uuid=True\)', 'String(36)', content)
    
    # Fix server defaults that use PostgreSQL functions
    content = re.sub(r'server_default=db\.text\("gen_random_uuid\(\)"\)', '', content)
    content = re.sub(r'server_default=db\.text\("CURRENT_TIMESTAMP"\)', 'default=db.text("CURRENT_TIMESTAMP")', content)
    content = re.sub(r'server_default=db\.text\("true"\)', 'default=True', content)
    content = re.sub(r'server_default=db\.text\("false"\)', 'default=False', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed UUID columns in {file_path}")

def main():
    """Fix UUID columns in all model files."""
    models_dir = os.path.dirname(os.path.abspath(__file__)) + '/models'
    
    model_files = [
        'role.py',
        'session.py', 
        'channel.py',
        'message.py',
        'direct_conversation.py',
        'channel_membership.py'
    ]
    
    for model_file in model_files:
        file_path = os.path.join(models_dir, model_file)
        if os.path.exists(file_path):
            fix_uuid_columns(file_path)

if __name__ == '__main__':
    main()