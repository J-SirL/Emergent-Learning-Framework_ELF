# My Fixes vs ELF v0.3.13

This document tracks improvements made in my fork that are NOT in the upstream v0.3.13 release.

## 1. Python 3.11+ Requirement (CRITICAL)

**Files:** `pyproject.toml`, `src/query/setup.py`

**Problem in v0.3.13:** Claims Python 3.8+ support but code uses Python 3.10+ syntax (`Path | None`).

**My Fix:**
- Changed `requires-python = ">=3.8"` to `requires-python = ">=3.11"`
- Added `from __future__ import annotations` to setup.py
- Changed `Path | None` to `Optional[Path]` for backwards compatibility
- Updated classifiers to only list 3.11, 3.12, 3.13
- Updated mypy python_version to "3.11"

**Status:** KEEP MY VERSION

---

## 2. npm --legacy-peer-deps Fix (CRITICAL)

**File:** `apps/dashboard/run-dashboard.sh`

**Problem in v0.3.13:** Uses `$PKG_MGR install` which fails with npm due to peer dependency conflicts.

**My Fix:**
```bash
if [ "$PKG_MGR" = "bun" ]; then
    bun install
else
    npm install --legacy-peer-deps
fi
```

**Status:** KEEP MY VERSION

---

## 3. Query Building Hook in PreToolUse

**File:** `tools/setup/install.sh`

**Problem in v0.3.13:** Missing automatic query of building before tool use.

**My Fix:** Added hook to query building first:
```python
{
    # 🔑 KRITISK: QUERY BYGGNADEN FÖRST
    "command": f'cd "{elf_dir}" && {python_cmd} -m query.query --context',
    "type": "command"
},
```

**Status:** KEEP MY VERSION

---

## 4. install-2.0.sh (NEW)

**File:** `tools/setup/install-2.0.sh`

**Not in v0.3.13:** Completely new installation script with:
- Python 3.11+ enforcement
- Data protection (won't overwrite memory/, failure-analysis/, etc.)
- `--python PATH` flag
- `--verbose` flag
- Colored output
- Better error messages

**Status:** NEW FILE - ADD TO MERGE

---

## 5. TalkinHead Removed

**File:** `apps/dashboard/run-dashboard.sh`

**In v0.3.13:** Has TalkinHead overlay startup code (Windows only)

**My Version:** TalkinHead code removed (moved to separate app `apps/head_overlay/`)

**Status:** Keep both - my structure is cleaner (separation of concerns)

---

## Summary: Files to Preserve My Fixes

| File | Action |
|------|--------|
| `pyproject.toml` | Use MINE (Python 3.11+) |
| `src/query/setup.py` | Use MINE (Optional[Path] fix) |
| `apps/dashboard/run-dashboard.sh` | Use MINE (--legacy-peer-deps) |
| `tools/setup/install.sh` | Use MINE (query hook) |
| `tools/setup/install-2.0.sh` | Keep (new file) |
| `.gitignore` | Merge both (add their patterns + keep mine) |

## Files to Take from v0.3.13

- All new documentation (`docs/api/`, `docs/guides/`, etc.)
- Security fixes in backend (`main.py`, `admin.py`)
- Test infrastructure
- CI/CD workflows
- New features (Leaderboard, migrations, etc.)
