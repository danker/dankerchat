#!/usr/bin/env bash
# UV Helper Functions for DankerChat Project
# Provides utility functions for UV package management and development workflows

set -e

# Color definitions for consistent output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${CYAN}[DEBUG]${NC} $1"; }

# Get project root directory
get_project_root() {
    local current="$(pwd)"
    while [[ "$current" != "/" ]]; do
        if [[ -f "$current/pyproject.toml" ]]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    echo "."
}

# Check if UV is installed and functional
check_uv_installation() {
    if ! command -v uv &> /dev/null; then
        log_error "UV is not installed or not in PATH"
        log_info "Install UV with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    local uv_version
    uv_version=$(uv --version 2>/dev/null) || {
        log_error "UV is installed but not functional"
        return 1
    }
    
    log_debug "UV is installed: $uv_version"
    return 0
}

# Check if project has pyproject.toml
check_pyproject() {
    local project_root
    project_root=$(get_project_root)
    
    if [[ ! -f "$project_root/pyproject.toml" ]]; then
        log_error "No pyproject.toml found in project root: $project_root"
        log_info "Initialize with: uv init"
        return 1
    fi
    
    log_debug "Found pyproject.toml at: $project_root/pyproject.toml"
    return 0
}

# Check if UV environment is synced
check_uv_sync() {
    local project_root
    project_root=$(get_project_root)
    
    if [[ ! -d "$project_root/.venv" ]]; then
        log_warning "Virtual environment not found"
        log_info "Run: uv sync"
        return 1
    fi
    
    if [[ ! -f "$project_root/uv.lock" ]]; then
        log_warning "Lock file not found"
        log_info "Run: uv lock"
        return 1
    fi
    
    # Check if lock file is newer than pyproject.toml
    if [[ "$project_root/pyproject.toml" -nt "$project_root/uv.lock" ]]; then
        log_warning "pyproject.toml is newer than uv.lock"
        log_info "Dependencies may be out of sync. Run: uv sync"
        return 1
    fi
    
    log_debug "UV environment appears to be synced"
    return 0
}

# Smart UV sync - only sync if needed
smart_sync() {
    local force_sync=false
    
    if [[ "${1:-}" == "--force" ]]; then
        force_sync=true
        shift
    fi
    
    if [[ "$force_sync" == true ]] || ! check_uv_sync 2>/dev/null; then
        log_info "Syncing UV environment..."
        uv sync "$@"
        log_success "Environment synced"
    else
        log_info "Environment already synced, skipping"
    fi
}

# Add dependency with smart categorization
smart_add() {
    local package="$1"
    local dev_flag=""
    
    if [[ -z "$package" ]]; then
        log_error "Package name required"
        echo "Usage: smart_add <package-name> [--dev]"
        return 1
    fi
    
    # Check if this looks like a dev dependency
    if [[ "$package" == *"test"* ]] || [[ "$package" == *"dev"* ]] || [[ "$package" == *"lint"* ]] || 
       [[ "$package" == *"format"* ]] || [[ "$package" == "black" ]] || [[ "$package" == "ruff" ]] ||
       [[ "$package" == "mypy" ]] || [[ "$package" == "pytest"* ]] || [[ "$2" == "--dev" ]]; then
        dev_flag="--dev"
        log_info "Adding as development dependency: $package"
    else
        log_info "Adding as runtime dependency: $package"
    fi
    
    uv add $dev_flag "$package"
    log_success "Added $package"
}

# Show UV environment status
show_uv_status() {
    local project_root
    project_root=$(get_project_root)
    
    echo "=== UV Environment Status ==="
    
    # UV version
    if check_uv_installation; then
        echo "UV Version: $(uv --version)"
    fi
    
    # Project info
    echo "Project Root: $project_root"
    
    # Python version
    if [[ -f "$project_root/.venv/bin/python" ]]; then
        echo "Python Version: $($project_root/.venv/bin/python --version)"
    elif [[ -f "$project_root/.venv/Scripts/python.exe" ]]; then
        echo "Python Version: $($project_root/.venv/Scripts/python.exe --version)"
    else
        echo "Python Version: Not available (no virtual environment)"
    fi
    
    # Dependencies count
    if [[ -f "$project_root/uv.lock" ]]; then
        local dep_count
        dep_count=$(grep -c "^name = " "$project_root/uv.lock" 2>/dev/null || echo "0")
        echo "Dependencies: $dep_count packages"
    fi
    
    # Environment status
    if check_uv_sync 2>/dev/null; then
        log_success "Environment is synced"
    else
        log_warning "Environment needs syncing"
    fi
    
    # Disk usage
    if [[ -d "$project_root/.venv" ]]; then
        local venv_size
        venv_size=$(du -sh "$project_root/.venv" 2>/dev/null | cut -f1 || echo "unknown")
        echo "Virtual Environment Size: $venv_size"
    fi
}

# Quick health check
health_check() {
    log_info "Running UV health check..."
    
    local errors=0
    
    # Check UV installation
    if ! check_uv_installation; then
        ((errors++))
    fi
    
    # Check pyproject.toml
    if ! check_pyproject; then
        ((errors++))
    fi
    
    # Check sync status
    if ! check_uv_sync; then
        ((errors++))
    fi
    
    # Try running a simple Python command
    if ! uv run python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor} OK')" 2>/dev/null; then
        log_error "Cannot run Python in UV environment"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "UV environment is healthy!"
        return 0
    else
        log_error "Found $errors issues with UV environment"
        return 1
    fi
}

# Clean UV caches and rebuild
clean_rebuild() {
    local project_root
    project_root=$(get_project_root)
    
    log_info "Cleaning UV environment..."
    
    # Remove virtual environment
    if [[ -d "$project_root/.venv" ]]; then
        rm -rf "$project_root/.venv"
        log_info "Removed .venv directory"
    fi
    
    # Remove lock file
    if [[ -f "$project_root/uv.lock" ]]; then
        rm -f "$project_root/uv.lock"
        log_info "Removed uv.lock file"
    fi
    
    # Remove Python cache
    find "$project_root" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$project_root" -name "*.pyc" -delete 2>/dev/null || true
    log_info "Removed Python cache files"
    
    # Rebuild environment
    log_info "Rebuilding environment..."
    uv sync
    
    log_success "Environment rebuilt successfully"
}

# Performance benchmark
benchmark_performance() {
    local project_root
    project_root=$(get_project_root)
    
    log_info "Benchmarking UV performance..."
    
    # Backup current environment
    local backup_dir="/tmp/uv-benchmark-backup-$$"
    if [[ -d "$project_root/.venv" ]]; then
        cp -r "$project_root/.venv" "$backup_dir"
    fi
    
    # Clean and time rebuild
    rm -rf "$project_root/.venv" 2>/dev/null || true
    rm -f "$project_root/uv.lock" 2>/dev/null || true
    
    local start_time
    start_time=$(date +%s.%N)
    
    uv sync >/dev/null 2>&1
    
    local end_time
    end_time=$(date +%s.%N)
    
    local duration
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "measurement failed")
    
    log_success "Environment creation completed in ${duration}s"
    
    # Restore backup if needed
    if [[ -d "$backup_dir" ]]; then
        rm -rf "$backup_dir"
    fi
    
    # Show package count
    local package_count
    package_count=$(uv run pip list 2>/dev/null | wc -l || echo "0")
    log_info "Installed $package_count packages"
}

# Export functions if this script is sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced
    export -f get_project_root check_uv_installation check_pyproject check_uv_sync
    export -f smart_sync smart_add show_uv_status health_check clean_rebuild benchmark_performance
    export -f log_info log_success log_warning log_error log_debug
    
    log_debug "UV helper functions loaded"
else
    # Script is being executed directly
    case "${1:-help}" in
        "status")
            show_uv_status
            ;;
        "health")
            health_check
            ;;
        "sync")
            smart_sync "${@:2}"
            ;;
        "add")
            smart_add "${@:2}"
            ;;
        "clean")
            clean_rebuild
            ;;
        "benchmark")
            benchmark_performance
            ;;
        "help"|*)
            echo "UV Helper Script for DankerChat"
            echo "Usage: $0 <command> [args]"
            echo ""
            echo "Commands:"
            echo "  status      Show UV environment status"
            echo "  health      Run health check"
            echo "  sync        Smart sync (only if needed)"
            echo "  add <pkg>   Smart add package (auto-detects dev deps)"
            echo "  clean       Clean and rebuild environment"
            echo "  benchmark   Benchmark environment creation performance"
            echo "  help        Show this help"
            echo ""
            echo "You can also source this script to use functions directly:"
            echo "  source $0"
            echo "  smart_sync --force"
            ;;
    esac
fi