#!/bin/bash
#
# Emergent Learning Framework - Setup Script v2.0
#
# REQUIREMENTS:
#   - Python 3.11+ (enforced - will not proceed without it)
#   - bash or compatible shell
#
# Supports: --mode fresh|merge|replace|skip
#           --core-only, --no-dashboard, --no-swarm
#           --python PATH (specify Python executable)
#           --force (skip version check - USE WITH CAUTION)
#
# Cross-platform: Works on Windows (Git Bash/MSYS2), Linux, and macOS
#

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR=11
REQUIRED_PYTHON_VERSION="$REQUIRED_PYTHON_MAJOR.$REQUIRED_PYTHON_MINOR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
ELF_DIR_DEFAULT="$CLAUDE_DIR/emergent-learning"
ELF_DIR="${ELF_BASE_PATH:-$ELF_DIR_DEFAULT}"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BASE_DIR="$ELF_DIR"

MODE="interactive"
CORE_ONLY=false
NO_DASHBOARD=false
NO_SWARM=false
FORCE_INSTALL=false
CUSTOM_PYTHON=""
VERBOSE=false

# Colors for output (if terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[ELF]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[ELF]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[ELF]${NC} Warning: $1"
}

log_error() {
    echo -e "${RED}[ELF]${NC} Error: $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[ELF]${NC} (verbose) $1"
    fi
}

show_banner() {
    echo ""
    echo "┌────────────────────────────────────────────────────────────┐"
    echo "│           Emergent Learning Framework v2.0                 │"
    echo "├────────────────────────────────────────────────────────────┤"
    echo "│                                                            │"
    echo "│      █████▒  █▒     █████▒                                 │"
    echo "│      █▒      █▒     █▒                                     │"
    echo "│      ████▒   █▒     ████▒                                  │"
    echo "│      █▒      █▒     █▒                                     │"
    echo "│      █████▒  █████▒ █▒                                     │"
    echo "│                                                            │"
    echo "│  Institutional Knowledge for AI Agents                     │"
    echo "│  Requires: Python ${REQUIRED_PYTHON_VERSION}+                                      │"
    echo "└────────────────────────────────────────────────────────────┘"
    echo ""
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode=*)
            MODE="${1#--mode=}"
            shift
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --core-only)
            CORE_ONLY=true
            NO_DASHBOARD=true
            NO_SWARM=true
            shift
            ;;
        --no-dashboard)
            NO_DASHBOARD=true
            shift
            ;;
        --no-swarm)
            NO_SWARM=true
            shift
            ;;
        --python=*)
            CUSTOM_PYTHON="${1#--python=}"
            shift
            ;;
        --python)
            CUSTOM_PYTHON="$2"
            shift 2
            ;;
        --force)
            FORCE_INSTALL=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_banner
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE       Installation mode: fresh|merge|replace|skip|interactive"
            echo "  --python PATH     Specify Python executable to use"
            echo "  --core-only       Install only core components (no dashboard/swarm)"
            echo "  --no-dashboard    Skip dashboard installation"
            echo "  --no-swarm        Skip swarm components"
            echo "  --force           Skip Python version check (not recommended)"
            echo "  --verbose, -v     Show detailed output"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Interactive installation"
            echo "  $0 --mode fresh              # Fresh install"
            echo "  $0 --python python3.12       # Use specific Python"
            echo "  $0 --mode merge --core-only  # Merge config, core only"
            exit 0
            ;;
        *)
            # Allow positional mode argument for backward compatibility
            if [[ "$1" =~ ^(fresh|merge|replace|skip|interactive)$ ]]; then
                MODE="$1"
            fi
            shift
            ;;
    esac
done

if [ "$CORE_ONLY" = true ]; then
    NO_DASHBOARD=true
    NO_SWARM=true
fi

# =============================================================================
# PYTHON VERSION DETECTION AND VALIDATION
# =============================================================================

find_suitable_python() {
    # If custom python specified, check it first
    if [ -n "$CUSTOM_PYTHON" ]; then
        if command -v "$CUSTOM_PYTHON" &> /dev/null; then
            echo "$CUSTOM_PYTHON"
            return 0
        else
            log_error "Specified Python not found: $CUSTOM_PYTHON"
            return 1
        fi
    fi

    # Search for Python in order of preference (newest first)
    local python_candidates=(
        "python3.13"
        "python3.12"
        "python3.11"
        "python3"
        "python"
    )

    for candidate in "${python_candidates[@]}"; do
        if command -v "$candidate" &> /dev/null; then
            # Check if this candidate meets version requirements
            local version_output
            version_output=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            if [ $? -eq 0 ]; then
                local major minor
                IFS='.' read -r major minor <<< "$version_output"
                if [ "$major" -ge "$REQUIRED_PYTHON_MAJOR" ] && [ "$minor" -ge "$REQUIRED_PYTHON_MINOR" ]; then
                    echo "$candidate"
                    return 0
                fi
                log_verbose "Found $candidate but version $version_output < $REQUIRED_PYTHON_VERSION"
            fi
        fi
    done

    return 1
}

get_python_version() {
    local python_cmd="$1"
    "$python_cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null
}

get_python_path() {
    local python_cmd="$1"
    "$python_cmd" -c "import sys; print(sys.executable)" 2>/dev/null
}

validate_python_version() {
    local python_cmd="$1"

    if [ -z "$python_cmd" ]; then
        return 1
    fi

    local version_output
    version_output=$("$python_cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)

    if [ $? -ne 0 ]; then
        return 1
    fi

    local major minor
    IFS='.' read -r major minor <<< "$version_output"

    if [ "$major" -lt "$REQUIRED_PYTHON_MAJOR" ]; then
        return 1
    fi

    if [ "$major" -eq "$REQUIRED_PYTHON_MAJOR" ] && [ "$minor" -lt "$REQUIRED_PYTHON_MINOR" ]; then
        return 1
    fi

    return 0
}

check_python_requirements() {
    log_info "Checking Python version requirements..."

    PYTHON_CMD=$(find_suitable_python)

    if [ -z "$PYTHON_CMD" ]; then
        echo ""
        log_error "No suitable Python found!"
        echo ""
        echo "  ELF requires Python ${REQUIRED_PYTHON_VERSION} or higher."
        echo ""
        echo "  Your options:"
        echo "    1. Install Python ${REQUIRED_PYTHON_VERSION}+ from https://python.org"
        echo "    2. Use pyenv: pyenv install ${REQUIRED_PYTHON_VERSION}"
        echo "    3. On Ubuntu/Debian: sudo apt install python${REQUIRED_PYTHON_VERSION}"
        echo "    4. On macOS: brew install python@${REQUIRED_PYTHON_VERSION}"
        echo "    5. Specify a Python path: --python /path/to/python${REQUIRED_PYTHON_VERSION}"
        echo ""

        if [ "$FORCE_INSTALL" = true ]; then
            log_warn "Force mode enabled - attempting with system python anyway..."
            PYTHON_CMD=$(command -v python3 || command -v python)
            if [ -z "$PYTHON_CMD" ]; then
                log_error "No Python found at all. Cannot continue."
                exit 1
            fi
        else
            exit 1
        fi
    fi

    local version=$(get_python_version "$PYTHON_CMD")
    local path=$(get_python_path "$PYTHON_CMD")

    log_success "Found Python $version at $path"

    # Verify essential modules
    log_verbose "Checking essential Python modules..."

    if ! "$PYTHON_CMD" -c "import venv" 2>/dev/null; then
        log_warn "Python venv module not available"
        echo "  On Debian/Ubuntu: sudo apt install python${REQUIRED_PYTHON_VERSION}-venv"
    fi

    if ! "$PYTHON_CMD" -c "import sqlite3" 2>/dev/null; then
        log_error "Python sqlite3 module not available - this is required!"
        exit 1
    fi
}

# =============================================================================
# DIRECTORY SETUP
# =============================================================================

setup_directories() {
    log_info "Setting up directories..."

    mkdir -p "$CLAUDE_DIR/commands"
    mkdir -p "$BASE_DIR/.coordination"
    mkdir -p "$ELF_DIR/.coordination"
    mkdir -p "$ELF_DIR/memory/successes"
    mkdir -p "$ELF_DIR/memory/sessions"
    mkdir -p "$ELF_DIR/failure-analysis"
    mkdir -p "$ELF_DIR/ceo-inbox"

    log_verbose "Created directory structure at $ELF_DIR"
}

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

db_has_user_data() {
    local db_path="$1"
    if [ -z "$PYTHON_CMD" ] || [ ! -f "$db_path" ]; then
        return 1
    fi

    local result
    set +e
    result=$("$PYTHON_CMD" - "$db_path" << 'PY'
import sqlite3
import sys

db_path = sys.argv[1]
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    if not tables:
        print("0")
        sys.exit(0)
    skip_tables = {"schema_version", "db_operations"}
    for table in tables:
        if table in skip_tables:
            continue
        cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
        if cursor.fetchone():
            print("1")
            sys.exit(0)
    print("0")
except Exception:
    print("1")
finally:
    try:
        conn.close()
    except Exception:
        pass
PY
    )
    local status=$?
    set -e
    if [ $status -ne 0 ]; then
        return 0
    fi

    [ "$result" = "1" ]
}

migrate_legacy_data() {
    local legacy_dir="$ELF_DIR_DEFAULT"
    local target_dir="$ELF_DIR"

    if [ ! -d "$legacy_dir" ]; then
        return
    fi

    if [ "$(cd "$legacy_dir" && pwd)" = "$(cd "$target_dir" && pwd)" ]; then
        return
    fi

    local legacy_db="$legacy_dir/memory/index.db"
    if [ ! -f "$legacy_db" ]; then
        return
    fi

    local target_db="$target_dir/memory/index.db"
    if db_has_user_data "$target_db"; then
        log_verbose "Target database already has data, skipping migration"
        return
    fi

    log_info "Migrating legacy data from $legacy_dir..."

    mkdir -p "$(dirname "$target_db")"
    if [ -f "$target_db" ]; then
        cp "$target_db" "$target_db.pre-legacy-migration"
    fi

    cp "$legacy_db" "$target_db"

    local legacy_golden="$legacy_dir/memory/golden-rules.md"
    local target_golden="$target_dir/memory/golden-rules.md"
    if [ -f "$legacy_golden" ] && [ ! -f "$target_golden" ]; then
        cp "$legacy_golden" "$target_golden"
    fi

    log_success "Migrated legacy data to $target_dir"
}

# =============================================================================
# VIRTUAL ENVIRONMENT
# =============================================================================

install_venv() {
    local venv_dir="$ELF_DIR/.venv"
    local requirements="$REPO_ROOT/requirements.txt"

    # Fallback locations for requirements
    if [ ! -f "$requirements" ]; then
        requirements="$SCRIPT_DIR/../../requirements.txt"
    fi
    if [ ! -f "$requirements" ]; then
        requirements="$ELF_DIR/requirements.txt"
    fi

    if [ -z "$PYTHON_CMD" ]; then
        log_warn "Python not available. Skipping venv setup."
        return 1
    fi

    # Determine venv python path based on OS
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        VENV_PYTHON="$venv_dir/Scripts/python.exe"
    else
        VENV_PYTHON="$venv_dir/bin/python"
    fi

    # Check if existing venv is valid
    local need_create=false
    local need_upgrade=false

    if [ ! -d "$venv_dir" ]; then
        need_create=true
    elif [ ! -f "$VENV_PYTHON" ]; then
        log_warn "Existing venv appears broken, recreating..."
        rm -rf "$venv_dir"
        need_create=true
    elif ! "$VENV_PYTHON" -c "import sys; sys.exit(0)" 2>/dev/null; then
        log_warn "Existing venv Python not working, recreating..."
        rm -rf "$venv_dir"
        need_create=true
    else
        # Check venv Python version
        local venv_version
        venv_version=$("$VENV_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        local venv_major venv_minor
        IFS='.' read -r venv_major venv_minor <<< "$venv_version"

        if [ "$venv_major" -lt "$REQUIRED_PYTHON_MAJOR" ] || \
           ([ "$venv_major" -eq "$REQUIRED_PYTHON_MAJOR" ] && [ "$venv_minor" -lt "$REQUIRED_PYTHON_MINOR" ]); then
            log_warn "Existing venv uses Python $venv_version (< $REQUIRED_PYTHON_VERSION), recreating..."
            rm -rf "$venv_dir"
            need_create=true
        fi
    fi

    # Create venv if needed
    if [ "$need_create" = true ]; then
        log_info "Creating Python virtual environment with $PYTHON_CMD..."

        local venv_output
        venv_output=$("$PYTHON_CMD" -m venv "$venv_dir" 2>&1)
        local venv_exit=$?

        if [ $venv_exit -ne 0 ]; then
            log_error "Failed to create venv (exit code $venv_exit)"
            if echo "$venv_output" | grep -qi "ensurepip"; then
                echo "  Hint: On Debian/Ubuntu: sudo apt install python${REQUIRED_PYTHON_VERSION}-venv"
            elif echo "$venv_output" | grep -qi "permission"; then
                echo "  Hint: Permission denied. Check write access to $ELF_DIR"
            else
                echo "  Error: $venv_output"
            fi
            VENV_PYTHON=""
            return 1
        fi
    fi

    # Verify venv python exists
    if [ ! -f "$VENV_PYTHON" ]; then
        log_error "Venv python not found at $VENV_PYTHON"
        VENV_PYTHON=""
        return 1
    fi

    # Show venv python version
    local venv_full_version
    venv_full_version=$("$VENV_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null)
    log_success "Virtual environment ready (Python $venv_full_version)"

    # Upgrade pip
    log_info "Upgrading pip..."
    "$VENV_PYTHON" -m pip install --upgrade pip --quiet 2>&1 || true

    # Install requirements
    if [ -f "$requirements" ]; then
        log_info "Installing Python dependencies..."

        local pip_output
        pip_output=$("$VENV_PYTHON" -m pip install -r "$requirements" 2>&1)
        local pip_exit=$?

        if [ $pip_exit -ne 0 ]; then
            log_warn "Some dependencies failed to install:"
            echo "$pip_output" | grep -i "error\|failed" | head -5
            echo "  Core features may still work."
        else
            log_verbose "Dependencies installed successfully"
        fi
    else
        log_warn "requirements.txt not found at $requirements"
    fi

    # Install project in editable mode
    log_info "Installing ELF package..."
    if "$VENV_PYTHON" -m pip install -e "$REPO_ROOT" --quiet 2>&1; then
        log_verbose "Package installed in editable mode"
    else
        log_warn "Failed to install editable package"
    fi

    # Install dashboard backend dependencies (if dashboard is enabled)
    if [ "$NO_DASHBOARD" = false ]; then
        local dashboard_requirements="$REPO_ROOT/apps/dashboard/backend/requirements.txt"
        if [ -f "$dashboard_requirements" ]; then
            log_info "Installing dashboard dependencies..."
            if "$VENV_PYTHON" -m pip install -r "$dashboard_requirements" --quiet 2>&1; then
                log_verbose "Dashboard dependencies installed"
            else
                log_warn "Some dashboard dependencies failed to install"
            fi
        fi
    fi

    # Final verification
    if ! "$VENV_PYTHON" -c "import peewee_aio" 2>/dev/null; then
        log_warn "Core dependency peewee_aio not available"
        echo "  Try: $VENV_PYTHON -m pip install peewee-aio[aiosqlite]"
    fi

    log_success "Virtual environment ready at: $venv_dir"
    return 0
}

# Global variable for venv python path
VENV_PYTHON=""

# =============================================================================
# INSTALLATION FUNCTIONS
# =============================================================================

install_commands() {
    log_info "Installing slash commands..."

    local commands_src="$REPO_ROOT/library/commands"
    if [ ! -d "$commands_src" ]; then
        commands_src="$SCRIPT_DIR/../../library/commands"
    fi

    if [ ! -d "$commands_src" ]; then
        log_warn "Commands directory not found"
        return
    fi

    local count=0
    for file in "$commands_src/"*; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        if [ ! -f "$CLAUDE_DIR/commands/$filename" ]; then
            cp "$file" "$CLAUDE_DIR/commands/$filename"
            ((count++))
        fi
    done

    if [ $count -gt 0 ]; then
        log_verbose "Installed $count new commands"
    fi
}

install_core_files() {
    log_info "Installing core files to $ELF_DIR..."
    mkdir -p "$ELF_DIR"

    # =========================================================================
    # CRITICAL: Protect user data directories
    # These directories contain user-generated data and MUST NOT be overwritten
    # =========================================================================
    local protected_dirs=(
        "memory"           # Contains index.db, golden-rules.md, sessions/, successes/
        "failure-analysis" # User's failure analyses
        "ceo-inbox"        # Pending CEO decisions
        ".coordination"    # Multi-agent coordination state
        ".venv"            # Virtual environment (handled separately)
    )

    # Backup protected directories if they exist in destination
    log_verbose "Protecting user data directories..."
    for dir in "${protected_dirs[@]}"; do
        if [ -d "$ELF_DIR/$dir" ]; then
            log_verbose "  Protected: $dir"
        fi
    done

    # Copy src contents SELECTIVELY (not the entire directory blindly)
    local src_dir="$REPO_ROOT/src"
    if [ ! -d "$src_dir" ]; then
        src_dir="$SCRIPT_DIR/../../src"
    fi

    if [ -d "$src_dir" ]; then
        # Copy each subdirectory/file individually, SKIPPING protected dirs
        for item in "$src_dir"/*; do
            [ -e "$item" ] || continue
            local basename=$(basename "$item")

            # Skip protected directories
            local is_protected=false
            for protected in "${protected_dirs[@]}"; do
                if [ "$basename" = "$protected" ]; then
                    is_protected=true
                    log_verbose "  Skipping protected: $basename"
                    break
                fi
            done

            if [ "$is_protected" = true ]; then
                continue
            fi

            # Copy the item (file or directory)
            if [ -d "$item" ]; then
                # For directories, use rsync-like behavior: update without deleting
                cp -r "$item" "$ELF_DIR/"
            else
                cp "$item" "$ELF_DIR/"
            fi
        done
        log_verbose "Copied src/ contents (protected user data preserved)"
    fi

    # Ensure protected directories exist (create if missing, don't overwrite)
    mkdir -p "$ELF_DIR/memory/successes"
    mkdir -p "$ELF_DIR/memory/sessions"
    mkdir -p "$ELF_DIR/failure-analysis"
    mkdir -p "$ELF_DIR/ceo-inbox"
    mkdir -p "$ELF_DIR/.coordination"

    # Copy scripts
    mkdir -p "$ELF_DIR/scripts"
    local scripts_src="$REPO_ROOT/tools/scripts"
    if [ ! -d "$scripts_src" ]; then
        scripts_src="$SCRIPT_DIR/../scripts"
    fi

    if [ -d "$scripts_src" ]; then
        cp "$scripts_src/"*.sh "$ELF_DIR/scripts/" 2>/dev/null || true
        cp "$scripts_src/"*.py "$ELF_DIR/scripts/" 2>/dev/null || true
        log_verbose "Copied scripts"
    fi

    # Copy requirements.txt for future reference
    if [ -f "$REPO_ROOT/requirements.txt" ]; then
        cp "$REPO_ROOT/requirements.txt" "$ELF_DIR/"
    fi

    # Copy dashboard (if not disabled)
    if [ "$NO_DASHBOARD" = false ]; then
        local dashboard_src="$REPO_ROOT/apps/dashboard"
        if [ ! -d "$dashboard_src" ]; then
            dashboard_src="$SCRIPT_DIR/../../apps/dashboard"
        fi

        if [ -d "$dashboard_src" ]; then
            rm -rf "$ELF_DIR/dashboard-app"
            cp -r "$dashboard_src" "$ELF_DIR/dashboard-app"
            log_verbose "Installed dashboard (including TalkinHead)"
        fi
    fi

    # Copy head_overlay app (optional avatar overlay)
    local head_overlay_src="$REPO_ROOT/apps/head_overlay"
    if [ -d "$head_overlay_src" ]; then
        rm -rf "$ELF_DIR/head_overlay"
        cp -r "$head_overlay_src" "$ELF_DIR/head_overlay"
        log_verbose "Installed head_overlay"
    fi

    # Copy query migrations
    local migrations_src="$REPO_ROOT/src/query/migrations"
    if [ -d "$migrations_src" ]; then
        mkdir -p "$ELF_DIR/query/migrations"
        cp "$migrations_src/"*.sql "$ELF_DIR/query/migrations/" 2>/dev/null || true
        log_verbose "Installed query migrations"
    fi

    log_success "Core files installed (user data preserved)"
}

install_settings() {
    log_info "Configuring Claude settings..."

    BASE_DIR="$BASE_DIR" VENV_PYTHON_PATH="$VENV_PYTHON" "$PYTHON_CMD" << 'PYTHON_SCRIPT'
import json
import os
import sys
from pathlib import Path
from typing import Optional

claude_dir = Path.home() / ".claude"
base_dir_env = os.environ.get("ELF_BASE_PATH") or os.environ.get("BASE_DIR")
elf_dir = Path(base_dir_env).expanduser() if base_dir_env else (claude_dir / "emergent-learning")

# Hook paths
hook_candidates = [
    elf_dir / "hooks" / "learning-loop",
    elf_dir / "src" / "hooks" / "learning-loop",
]
elf_hooks = next((p for p in hook_candidates if p.exists()), hook_candidates[0])
settings_file = claude_dir / "settings.json"

# Get venv python path
venv_python = os.environ.get("VENV_PYTHON_PATH", "")

if not venv_python:
    venv_dir = elf_dir / ".venv"
    if sys.platform == "win32":
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"
    if candidate.exists():
        venv_python = str(candidate)

# Determine python command for hooks
if venv_python and Path(venv_python).exists():
    python_cmd = f'"{venv_python}"'
else:
    python_cmd = "python3"

# Hook paths
elf_hooks_main = elf_hooks.parent
checkin_hook_path = elf_hooks_main / "UserPromptSubmit" / "detect_checkin.py"

if sys.platform == "win32":
    pre_hook = str(elf_hooks / "pre_tool_learning.py").replace("\\", "\\\\")
    post_hook = str(elf_hooks / "post_tool_learning.py").replace("\\", "\\\\")
    checkin_hook = str(checkin_hook_path).replace("\\", "\\\\")
    if venv_python:
        python_cmd = f'"{venv_python.replace(chr(92), chr(92)+chr(92))}"'
else:
    pre_hook = str(elf_hooks / "pre_tool_learning.py")
    post_hook = str(elf_hooks / "post_tool_learning.py")
    checkin_hook = str(checkin_hook_path)

settings = {
    "hooks": {
        "PreToolUse": [
            {
                "hooks": [
                    {
                        "command": f'cd "{elf_dir}" && {python_cmd} -m query.query --context',
                        "type": "command"
                    },
                    {
                        "command": f'{python_cmd} "{pre_hook}"',
                        "type": "command"
                    }
                ],
                "matcher": "Task"
            }
        ],
        "PostToolUse": [
            {
                "hooks": [
                    {
                        "command": f'{python_cmd} "{post_hook}"',
                        "type": "command"
                    }
                ],
                "matcher": "Task"
            }
        ]
    }
}

if checkin_hook_path.exists():
    settings["hooks"]["UserPromptSubmit"] = [
        {
            "hooks": [
                {
                    "command": f'{python_cmd} "{checkin_hook}"',
                    "type": "command"
                }
            ],
            "matcher": ""
        }
    ]

# Merge with existing settings
if settings_file.exists():
    try:
        with open(settings_file) as f:
            existing = json.load(f)
        existing["hooks"] = settings["hooks"]
        settings = existing
    except (json.JSONDecodeError, KeyError):
        pass

with open(settings_file, "w") as f:
    json.dump(settings, f, indent=4)

print(f"[ELF] Hooks configured at: {elf_hooks}")
PYTHON_SCRIPT
}

install_git_hooks() {
    local git_hooks_dir=""

    if [ -d "$REPO_ROOT/.git/hooks" ]; then
        git_hooks_dir="$REPO_ROOT/.git/hooks"
    elif [ -d "$ELF_DIR/.git/hooks" ]; then
        git_hooks_dir="$ELF_DIR/.git/hooks"
    fi

    if [ -n "$git_hooks_dir" ] && [ -d "$git_hooks_dir" ]; then
        local pre_commit_src="$SCRIPT_DIR/git-hooks/pre-commit"
        if [ -f "$pre_commit_src" ]; then
            cp "$pre_commit_src" "$git_hooks_dir/pre-commit"
            chmod +x "$git_hooks_dir/pre-commit"
            log_verbose "Git pre-commit hook installed"
        fi
    fi
}

copy_template() {
    local template_src="$REPO_ROOT/templates/CLAUDE.md.template"
    if [ ! -f "$template_src" ]; then
        template_src="$SCRIPT_DIR/../../templates/CLAUDE.md.template"
    fi

    local dest="$CLAUDE_DIR/CLAUDE.md"

    if [ ! -f "$template_src" ]; then
        log_warn "Template not found at $template_src"
        return
    fi

    cp "$template_src" "$dest"

    # Replace paths if using non-default location
    if [ "$ELF_DIR" != "$ELF_DIR_DEFAULT" ]; then
        ESCAPED_TARGET=$(echo "$ELF_DIR" | sed 's/\//\\\//g')
        ESCAPED_DEFAULT="~\/.claude\/emergent-learning"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/$ESCAPED_DEFAULT/$ESCAPED_TARGET/g" "$dest"
        else
            sed -i "s/$ESCAPED_DEFAULT/$ESCAPED_TARGET/g" "$dest"
        fi
    fi

    log_verbose "CLAUDE.md template installed"
}

# =============================================================================
# VERIFICATION
# =============================================================================

verify_installation() {
    log_info "Verifying installation..."

    local errors=0

    # Check CLAUDE.md
    if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
        if grep -q "Emergent Learning Framework" "$CLAUDE_DIR/CLAUDE.md" 2>/dev/null; then
            log_verbose "CLAUDE.md: OK"
        else
            log_warn "CLAUDE.md exists but doesn't contain ELF instructions"
        fi
    else
        log_warn "CLAUDE.md not found"
        ((errors++))
    fi

    # Check venv
    if [ -n "$VENV_PYTHON" ] && [ -f "$VENV_PYTHON" ]; then
        log_verbose "Virtual environment: OK"
    else
        log_warn "Virtual environment not properly configured"
        ((errors++))
    fi

    # Check settings.json
    if [ -f "$CLAUDE_DIR/settings.json" ]; then
        if grep -q "hooks" "$CLAUDE_DIR/settings.json" 2>/dev/null; then
            log_verbose "settings.json: OK"
        else
            log_warn "settings.json missing hooks configuration"
            ((errors++))
        fi
    else
        log_warn "settings.json not found"
        ((errors++))
    fi

    # Check core files
    if [ -d "$ELF_DIR/query" ]; then
        log_verbose "Query system: OK"
    else
        log_warn "Query system not found at $ELF_DIR/query"
        ((errors++))
    fi

    # Test query system import
    if [ -n "$VENV_PYTHON" ]; then
        if "$VENV_PYTHON" -c "import sys; sys.path.insert(0, '$ELF_DIR'); from query import QuerySystem" 2>/dev/null; then
            log_verbose "Query system import: OK"
        else
            log_warn "Query system import failed"
            ((errors++))
        fi
    fi

    if [ $errors -eq 0 ]; then
        log_success "All checks passed!"
        return 0
    else
        log_warn "$errors verification check(s) failed"
        return 1
    fi
}

# =============================================================================
# MAIN INSTALLATION LOGIC
# =============================================================================

run_installation() {
    local mode="$1"

    case "$mode" in
        fresh)
            copy_template
            install_commands
            install_core_files
            install_venv
            install_settings
            install_git_hooks
            ;;
        merge)
            if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
                cp "$CLAUDE_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md.backup"
                {
                    cat "$CLAUDE_DIR/CLAUDE.md"
                    echo ""
                    echo ""
                    echo "# =============================================="
                    echo "# EMERGENT LEARNING FRAMEWORK - AUTO-APPENDED"
                    echo "# =============================================="
                    echo ""
                    cat "$REPO_ROOT/templates/CLAUDE.md.template" 2>/dev/null || \
                    cat "$SCRIPT_DIR/../../templates/CLAUDE.md.template"
                } > "$CLAUDE_DIR/CLAUDE.md.new"
                mv "$CLAUDE_DIR/CLAUDE.md.new" "$CLAUDE_DIR/CLAUDE.md"
                log_success "Merged with existing config (backup: CLAUDE.md.backup)"
            fi
            install_commands
            install_core_files
            install_venv
            install_settings
            install_git_hooks
            ;;
        replace)
            if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
                cp "$CLAUDE_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md.backup"
                log_info "Backed up existing CLAUDE.md"
            fi
            copy_template
            install_commands
            install_core_files
            install_venv
            install_settings
            install_git_hooks
            ;;
        skip)
            log_warn "Skipping CLAUDE.md modification"
            log_warn "ELF may not function correctly without CLAUDE.md instructions"
            install_commands
            install_core_files
            install_venv
            install_settings
            install_git_hooks
            ;;
    esac
}

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

main() {
    show_banner

    # Step 1: Check Python
    check_python_requirements

    # Step 2: Setup directories
    setup_directories

    # Step 3: Migrate legacy data
    if [ -n "$PYTHON_CMD" ]; then
        migrate_legacy_data
    fi

    # Step 4: Run installation based on mode
    case "$MODE" in
        fresh|merge|replace|skip)
            run_installation "$MODE"
            ;;
        interactive|*)
            if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
                if grep -q "Emergent Learning Framework" "$CLAUDE_DIR/CLAUDE.md" 2>/dev/null; then
                    log_info "ELF already configured in CLAUDE.md"
                    install_commands
                    install_core_files
                    install_venv
                    install_settings
                    install_git_hooks
                else
                    echo ""
                    echo "Existing CLAUDE.md found."
                    echo ""
                    echo "Options:"
                    echo "  1) Merge - Keep yours, add ELF below"
                    echo "  2) Replace - Use ELF only (yours backed up)"
                    echo "  3) Skip - Don't modify CLAUDE.md"
                    echo ""
                    read -p "Choice [1/2/3]: " choice
                    case "$choice" in
                        1) run_installation "merge" ;;
                        2) run_installation "replace" ;;
                        3) run_installation "skip" ;;
                        *) log_error "Invalid choice"; exit 1 ;;
                    esac
                fi
            else
                run_installation "fresh"
            fi
            ;;
    esac

    # Step 5: Verify
    echo ""
    verify_installation

    # Done
    echo ""
    log_success "Installation complete!"
    echo ""
    echo "  Next steps:"
    echo "    1. Start a new Claude Code session"
    echo "    2. Claude will automatically query the building"
    echo "    3. Use /checkin to record learnings"
    echo ""
    echo "  Dashboard (optional):"
    echo "    bash $ELF_DIR/dashboard-app/run-dashboard.sh"
    echo ""
}

# Run main
main
