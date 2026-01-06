# Changelog

All notable changes to the Emergent Learning Framework will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.14] - 2026-01-06

### Added
- **install-2.0.sh** - New installation script with Python 3.11+ enforcement
  - Data protection: Won't overwrite memory/, failure-analysis/, ceo-inbox/
  - `--python PATH` flag for custom Python executable
  - `--verbose` flag for detailed output
  - Colored output and better error messages
- **Merged v0.3.12 features** - Incorporated upstream improvements:
  - Game Leaderboard system with anti-cheat filtering
  - Comprehensive API documentation (`docs/api/`)
  - Database schema documentation (`docs/database/`)
  - Developer guides for testing, performance, extensions
  - Query system migrations (`src/query/migrations/`)
  - TalkinHead hooks and overlay

### Fixed
- **Python 3.11+ Requirement** - Changed from >=3.8 to >=3.11 (code uses 3.10+ syntax)
- **Type Hint Compatibility** - Fixed `Path | None` to `Optional[Path]` in setup.py
- **npm peer dependencies** - Added `--legacy-peer-deps` to dashboard npm install
- **Query Building Hook** - Added automatic building query in PreToolUse hooks

### Security
- **SQL Injection Protection** - Whitelist-based validation in main.py (from v0.3.12)
- **Path Traversal Protection** - Hardened admin.py file access (from v0.3.12)
- **Thread-Safe Session Index** - Added threading.RLock protection (from v0.3.11)
- **Exponential Backoff** - Auto-capture error handling (from v0.3.11)

### Changed
- Version bumped to 0.3.14
- pyproject.toml updated with test markers and filterwarnings

## [0.3.1] - 2025-12-25

### Fixed
- **Windows Installer** - Fixed PowerShell Join-Path syntax errors for new users
  - Join-Path now correctly uses 2 parameters instead of 3
  - Fixed venv Python path, pip path, and hook path resolution
  - Database validation now uses venv Python with all dependencies
- **Python Script Installation** - Installer now copies all 21 Python scripts from tools/scripts/
  - Fixes pre-commit hook failures (check-invariants.py missing)
  - Ensures recording scripts (record-heuristic.py, etc.) are available
- **Watcher Module Installation** - Tiered watcher system now properly installed
  - src/watcher/ copied to ~/.claude/emergent-learning/watcher/
  - start-watcher.sh updated to use correct installed paths
  - Fixes "launcher.py not found" error when starting watcher

## [0.2.0] - 2025-12-16

### Added
- **Async Query Engine** - Complete migration to async architecture using peewee-aio
- **ELF MCP Server** - Native MCP integration for claude-flow
- **Step-file Workflows** - Resumable task architecture with frontmatter state
- **Party Definitions** - Agent team compositions for complex tasks
- **Golden Rule Categories** - Filter rules by domain/category
- **Customization Layer** - User-specific config overrides
- **Update System** - Simple update.sh/update.ps1 with database migrations

### Changed
- Cosmic view now default (persisted to localStorage)
- Modular query system architecture (Phase 1-6 refactor)
- Zustand store with persistence middleware

### Fixed
- Windows compatibility (ASCII-only CLI output)
- Clean exit when dashboard servers already running
- Workflow engine import handling
- Hook directory structure

## [0.1.2] - 2025-12-14

### Added
- Dashboard UI overhaul with cosmic theme
- Learning pipeline automation
- File operations tracking for hotspot analysis

## [0.1.1] - 2025-12-13

### Added
- Initial dashboard application
- Golden rules and heuristics system
- CEO escalation workflow

## [0.1.0] - 2025-12-12

### Added
- Initial release
- Core ELF framework
- Installation scripts
- Basic query system

---

## Versioning Policy

- **Major (X.0.0)**: Breaking changes to database schema or configuration
- **Minor (0.X.0)**: New features, backward-compatible
- **Patch (0.0.X)**: Bug fixes, documentation updates
