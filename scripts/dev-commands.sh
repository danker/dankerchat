#!/usr/bin/env bash
# Development commands using UV for DankerChat project
# Common development tasks wrapped in UV commands

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$REPO_ROOT"

# Color output for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if UV is available
if ! command -v uv &> /dev/null; then
    echo_error "UV is not installed. Please install UV first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Function to run tests
run_tests() {
    echo_info "Running tests with UV..."
    uv run pytest tests/ -v --cov=src/dankerchat --cov-report=term-missing
    echo_success "Tests completed"
}

# Function to run linting
run_lint() {
    echo_info "Running linting with UV..."
    uv run ruff check src/ tests/
    uv run black --check src/ tests/
    echo_success "Linting completed"
}

# Function to format code
format_code() {
    echo_info "Formatting code with UV..."
    uv run black src/ tests/
    uv run ruff --fix src/ tests/
    echo_success "Code formatting completed"
}

# Function to run type checking
run_typecheck() {
    echo_info "Running type checking with UV..."
    uv run mypy src/dankerchat
    echo_success "Type checking completed"
}

# Function to sync dependencies
sync_deps() {
    echo_info "Syncing dependencies with UV..."
    uv sync
    echo_success "Dependencies synced"
}

# Function to add dependency
add_dep() {
    if [ -z "$1" ]; then
        echo_error "Usage: $0 add <package-name>"
        exit 1
    fi
    
    echo_info "Adding dependency: $1"
    uv add "$1"
    echo_success "Added dependency: $1"
}

# Function to add dev dependency
add_dev_dep() {
    if [ -z "$1" ]; then
        echo_error "Usage: $0 add-dev <package-name>"
        exit 1
    fi
    
    echo_info "Adding dev dependency: $1"
    uv add --dev "$1"
    echo_success "Added dev dependency: $1"
}

# Function to remove dependency
remove_dep() {
    if [ -z "$1" ]; then
        echo_error "Usage: $0 remove <package-name>"
        exit 1
    fi
    
    echo_info "Removing dependency: $1"
    uv remove "$1"
    echo_success "Removed dependency: $1"
}

# Function to run development server
run_server() {
    echo_info "Starting DankerChat development server with UV..."
    uv run python -c "
try:
    from dankerchat.server import create_app
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
except ImportError:
    print('Server module not yet implemented. Run: uv run python -m flask --version')
    import flask
    print(f'Flask {flask.__version__} is available for development.')
"
}

# Function to start interactive shell
start_shell() {
    echo_info "Starting UV Python shell..."
    uv run python
}

# Function to show project info
show_info() {
    echo_info "DankerChat Project Information"
    echo "=============================="
    echo "Python Version: $(uv run python --version)"
    echo "UV Version: $(uv --version)"
    echo "Project Dependencies:"
    uv run pip list | head -10
    echo "..."
    echo "Use 'uv run pip list' to see all packages"
    echo ""
    echo "Project Structure:"
    find src/ -name "*.py" | head -5
    echo "..."
    echo ""
    echo "Available Commands:"
    echo "  ./scripts/dev-commands.sh test      - Run tests"
    echo "  ./scripts/dev-commands.sh lint      - Run linting"
    echo "  ./scripts/dev-commands.sh format    - Format code"
    echo "  ./scripts/dev-commands.sh typecheck - Type checking"
    echo "  ./scripts/dev-commands.sh sync      - Sync dependencies"
    echo "  ./scripts/dev-commands.sh server    - Start dev server"
    echo "  ./scripts/dev-commands.sh shell     - Interactive shell"
}

# Main command dispatcher
case "${1:-help}" in
    "test")
        run_tests
        ;;
    "lint")
        run_lint
        ;;
    "format")
        format_code
        ;;
    "typecheck")
        run_typecheck
        ;;
    "sync")
        sync_deps
        ;;
    "add")
        add_dep "$2"
        ;;
    "add-dev")
        add_dev_dep "$2"
        ;;
    "remove")
        remove_dep "$2"
        ;;
    "server")
        run_server
        ;;
    "shell")
        start_shell
        ;;
    "info")
        show_info
        ;;
    "help"|*)
        echo "DankerChat Development Commands (UV-based)"
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  test                 Run test suite"
        echo "  lint                 Run linting (ruff + black check)"
        echo "  format               Format code (black + ruff fix)"
        echo "  typecheck            Run mypy type checking"
        echo "  sync                 Sync all dependencies"
        echo "  add <package>        Add runtime dependency"
        echo "  add-dev <package>    Add development dependency"
        echo "  remove <package>     Remove dependency"
        echo "  server               Start development server"
        echo "  shell                Start interactive Python shell"
        echo "  info                 Show project information"
        echo "  help                 Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 test              # Run all tests"
        echo "  $0 add flask-cors    # Add flask-cors dependency"
        echo "  $0 format            # Format all code"
        echo ""
        exit 0
        ;;
esac