#!/usr/bin/env bash
# Environment Setup Script for DankerChat with UV
# Handles environment variable configuration and validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source UV helpers
source "$SCRIPT_DIR/uv-helpers.sh"

# Change to project root
cd "$REPO_ROOT"

# Function to create .env file from example
setup_env_file() {
    if [[ -f ".env" ]]; then
        log_info ".env file already exists"
        return 0
    fi
    
    if [[ ! -f ".env.example" ]]; then
        log_error ".env.example file not found"
        return 1
    fi
    
    log_info "Creating .env file from .env.example..."
    cp ".env.example" ".env"
    
    log_success ".env file created"
    log_warning "Please update .env file with your actual configuration values"
    log_info "Edit: $REPO_ROOT/.env"
}

# Function to validate environment variables
validate_env() {
    local required_vars=(
        "FLASK_SECRET_KEY"
        "JWT_SECRET_KEY"
        "DATABASE_URL"
    )
    
    local missing_vars=()
    
    # Load .env file if it exists
    if [[ -f ".env" ]]; then
        set -a
        source ".env"
        set +a
    fi
    
    # Check required variables
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]] || [[ "${!var:-}" == *"your-"*"-here" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing or placeholder values for required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_info "Please update your .env file with actual values"
        return 1
    fi
    
    log_success "All required environment variables are set"
    return 0
}

# Function to show environment status
show_env_status() {
    log_info "Environment Configuration Status"
    
    # Check .env file
    if [[ -f ".env" ]]; then
        log_success ".env file exists"
    else
        log_warning ".env file missing"
    fi
    
    # Check .env.example
    if [[ -f ".env.example" ]]; then
        log_success ".env.example file exists"
    else
        log_warning ".env.example file missing"
    fi
    
    # Load and show non-sensitive variables
    if [[ -f ".env" ]]; then
        log_info "Current environment configuration:"
        
        set -a
        source ".env" 2>/dev/null || true
        set +a
        
        # Show non-sensitive variables
        echo "  FLASK_ENV: ${FLASK_ENV:-not set}"
        echo "  FLASK_DEBUG: ${FLASK_DEBUG:-not set}"
        echo "  DATABASE_URL: ${DATABASE_URL:-not set}"
        echo "  REDIS_URL: ${REDIS_URL:-not set}"
        echo "  APP_NAME: ${APP_NAME:-not set}"
        echo "  APP_VERSION: ${APP_VERSION:-not set}"
        echo "  HOST: ${HOST:-not set}"
        echo "  PORT: ${PORT:-not set}"
        echo "  LOG_LEVEL: ${LOG_LEVEL:-not set}"
        
        # Check for sensitive variables without showing values
        if [[ -n "${FLASK_SECRET_KEY:-}" ]]; then
            echo "  FLASK_SECRET_KEY: ✓ set"
        else
            echo "  FLASK_SECRET_KEY: ✗ not set"
        fi
        
        if [[ -n "${JWT_SECRET_KEY:-}" ]]; then
            echo "  JWT_SECRET_KEY: ✓ set"
        else
            echo "  JWT_SECRET_KEY: ✗ not set"
        fi
    fi
    
    # UV-specific environment variables
    echo ""
    log_info "UV Environment Variables:"
    echo "  UV_PYTHON_PREFERENCE: ${UV_PYTHON_PREFERENCE:-default}"
    echo "  UV_SYSTEM_PYTHON: ${UV_SYSTEM_PYTHON:-default}"
    echo "  UV_COMPILE_BYTECODE: ${UV_COMPILE_BYTECODE:-default}"
    echo "  UV_PROJECT_ENVIRONMENT: ${UV_PROJECT_ENVIRONMENT:-default}"
}

# Function to generate secure secrets
generate_secrets() {
    log_info "Generating secure secrets..."
    
    # Generate Flask secret key
    local flask_secret
    flask_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "FLASK_SECRET_KEY=$flask_secret"
    
    # Generate JWT secret key  
    local jwt_secret
    jwt_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "JWT_SECRET_KEY=$jwt_secret"
    
    log_info "Copy these values to your .env file"
}

# Function to test environment loading
test_env_loading() {
    log_info "Testing environment loading with UV..."
    
    # Test loading environment in UV context
    uv run python -c "
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Test required variables
required_vars = ['FLASK_SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
missing = []

for var in required_vars:
    if not os.getenv(var) or 'your-' in os.getenv(var, ''):
        missing.append(var)

if missing:
    print(f'Missing variables: {missing}')
    exit(1)
else:
    print('✓ All required environment variables loaded successfully')
    print(f'Flask Debug: {os.getenv(\"FLASK_DEBUG\", \"false\")}')
    print(f'Database: {os.getenv(\"DATABASE_URL\", \"not set\")}')
"
    
    if [[ $? -eq 0 ]]; then
        log_success "Environment loading test passed"
    else
        log_error "Environment loading test failed"
        return 1
    fi
}

# Function to setup development environment
setup_development() {
    log_info "Setting up development environment..."
    
    # Ensure UV environment is ready
    smart_sync
    
    # Setup .env file
    setup_env_file
    
    # Create logs directory
    mkdir -p logs
    log_info "Created logs directory"
    
    # Create instance directory for Flask
    mkdir -p instance
    log_info "Created instance directory"
    
    log_success "Development environment setup complete"
    log_info "Next steps:"
    log_info "1. Edit .env file with your configuration"
    log_info "2. Run: ./scripts/env-setup.sh validate"
    log_info "3. Run: ./scripts/dev-commands.sh test"
}

# Main command dispatcher
case "${1:-help}" in
    "setup")
        setup_development
        ;;
    "env")
        setup_env_file
        ;;
    "validate")
        validate_env
        ;;
    "status")
        show_env_status
        ;;
    "secrets")
        generate_secrets
        ;;
    "test")
        test_env_loading
        ;;
    "help"|*)
        echo "Environment Setup Script for DankerChat"
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  setup      Complete development environment setup"
        echo "  env        Create .env file from .env.example"
        echo "  validate   Validate environment configuration"
        echo "  status     Show environment status"
        echo "  secrets    Generate secure secret keys"
        echo "  test       Test environment loading"
        echo "  help       Show this help"
        echo ""
        echo "Example workflow:"
        echo "  $0 setup     # Initial setup"
        echo "  $0 secrets   # Generate secrets"
        echo "  # Edit .env with generated secrets"
        echo "  $0 validate  # Verify configuration"
        ;;
esac