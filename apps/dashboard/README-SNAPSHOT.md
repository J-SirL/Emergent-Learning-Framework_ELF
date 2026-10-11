# Dashboard snapshot, 2026-10-11

This branch, `dashboard-snapshot-2026-10-11`, holds the ELF dashboard exactly as it ran on the development server on 11 October 2026. It is a restore point, not a release. `main` is unchanged.

## Why this branch exists

ELF is being retired: its learning store moves into the ARCHE Hub, and the ELF directory on the development server will be removed afterwards. The dashboard is not being thrown away. ARCHE will first record every view and idea in it, then rebuild the ones it keeps inside ARCHE after the MVP.

That plan relies on this repository as the restore source for the code. When we checked on 11 October, `main` was not that source: it was last pushed on 17 February, while the dashboard on the server had changed until 21 March. Restoring from `main` would have lost a month of work, including the extended cosmic views. This branch closes that gap before anything on the server is removed.

## What changed against `main`

Besides this file and the `.gitignore` line, 57 files: 19 added, 35 changed, 3 removed. All of it is work done on the server after the last push.

- **Live view (new):** `components/live/` — a live panel, a task board (`TaskKanban`), a trail feed and a signal input, with the backend router `routers/live.py`.
- **Semantic search (new backend):** `routers/semantic.py`.
- **Cosmic view (extended):** `CosmicAnalyticsView` grew by about 320 lines; `CosmicRunsView` and `CosmicTimelineView` are new.
- **Drill-downs (reworked):** `components/analytics/AnalyticsDrillDown` and `components/stats/StatsDrillDownView` replace the older drill-down modal used by `StatsBar`.
- **Navigation:** `NavigationTabs` is new; the layout, stores and types changed with it.
- **Game view:** enemy visuals (`game/enemies/EnemyVisualBase`, `game/systems/useEnemyVisualController`).
- **Heuristics:** a detail modal (`heuristics/HeuristicDetailModal`).
- **Tests:** `vitest.config.ts` is new. Three backend security tests that exist on `main` were not present on the server and are therefore absent here: `backend/tests/integration/test_auth_flow.py`, `backend/tests/test_security.py` and `backend/tests/unit/test_token_validation.py`. They are still on `main`.

`git diff main..dashboard-snapshot-2026-10-11 -- apps/dashboard` shows every line.

## What was left out, and why

- **Secrets:** the two `.env` files (they hold `SESSION_ENCRYPTION_KEY`). `.gitignore` now excludes `.env` files, so they cannot be committed by accident. Create your own from `backend/.env.example` when restoring.
- **Dependencies and build output:** `node_modules/`, Python virtual environments, `frontend/dist/`, caches.
- **Run logs:** `tests/test-results.txt` and other logs.
- **TalkinHead:** the server copy is disabled (`TalkinHead.disabled`, 879 MB). The version on `main` is kept as it is.

## Restoring

```bash
git checkout dashboard-snapshot-2026-10-11
cd apps/dashboard/backend && cp .env.example .env   # then set SESSION_ENCRYPTION_KEY
pip install -r requirements.txt && python -m uvicorn main:app --port 8888
cd ../frontend && bun install && bun run dev
```

Keep this branch until ARCHE has recorded every view and idea in the dashboard and the ELF directory on the server is gone. Merging it into `main` is a separate decision.
