# Emergent Learning Framework - Project Status

**Last Updated:** 2026-01-07 01:00

## Current Status

**Current Focus:** v0.3.14 release - merged v0.3.13 with Python 3.11+ fixes

**Branch:** main

## Change Log

**2026-01-07 01:00** - Fixed dashboard venv Python usage - [apps/dashboard/run-dashboard.sh](apps/dashboard/run-dashboard.sh) - Backend was using system Python 3.9 instead of venv
**2026-01-07 00:55** - Fixed setup_security.py syntax errors - [apps/dashboard/backend/setup_security.py](apps/dashboard/backend/setup_security.py) - Multiline print statements broke Python parsing
**2026-01-07 00:45** - Added dashboard deps to install-2.0.sh - [tools/setup/install-2.0.sh](tools/setup/install-2.0.sh) - slowapi and other backend deps weren't being installed
**2026-01-07 00:35** - Added TalkinHead, head_overlay, migrations to install - [tools/setup/install-2.0.sh](tools/setup/install-2.0.sh) - New v0.3.13 components weren't being copied
**2026-01-07 00:15** - Added node_modules to gitignore - [.gitignore](.gitignore) - VSCode showed untracked files
**2026-01-07 00:10** - Merged v0.3.13 with Python 3.11+ fixes - Multiple files - Combined upstream features with my compatibility fixes

## Active Issues

- [ ] `/checkpoint` command not showing in available skills (needs Claude Code restart)
- [ ] Dashboard needs `.env` with SESSION_ENCRYPTION_KEY (manual setup required)

## Key Decisions

- **Python 3.11+ Required** - Code uses 3.10+ syntax (`Path | None`), changed minimum from 3.8 to 3.11
- **Data Protection in Install** - install-2.0.sh preserves memory/, failure-analysis/, ceo-inbox/, .venv/
- **Venv for Dashboard** - run-dashboard.sh now uses ELF venv instead of system Python

## Next Steps

- [ ] Test dashboard with `elf-dashboard`
- [ ] Verify all slash commands work after restart
- [ ] Consider adding `/project-init` command to create project.md
