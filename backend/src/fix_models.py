"""
Script to fix remaining model issues for SQLite compatibility.
"""

import os
import re

def fix_model_file(file_path):
    """Fix a single model file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix UUID defaults
    content = re.sub(r'default=uuid\.uuid4,\s*', 'default=lambda: str(uuid.uuid4())', content)
    
    # Fix duplicate defaults
    content = re.sub(r'default=([^,\n]+),\s*default=([^,\n]+)', r'default=\2', content)
    
    # Fix DateTime defaults
    content = re.sub(r'default=db\.text\("CURRENT_TIMESTAMP"\)', 'default=datetime.utcnow', content)
    
    # Add missing String import
    if 'from sqlalchemy import' in content and 'String' not in content:
        content = re.sub(r'from sqlalchemy import ([^)]+)', 
                        r'from sqlalchemy import String, \1', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

def main():
    """Fix all model files."""
    models_dir = os.path.dirname(os.path.abspath(__file__)) + '/models'
    
    model_files = [
        'role.py', 'session.py', 'channel.py', 'message.py', 
        'direct_conversation.py', 'channel_membership.py'
    ]
    
    for model_file in model_files:
        file_path = os.path.join(models_dir, model_file)
        if os.path.exists(file_path):
            fix_model_file(file_path)

if __name__ == '__main__':
    main()