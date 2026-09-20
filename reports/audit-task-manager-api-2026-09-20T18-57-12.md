# Audit Report — task-manager-api

**Date:** 2026-09-20T18-57-12
**Type:** Self-verification re-audit (fresh re-read, not relying on prior refactoring log)
**Skill version:** refactor-arch v3.1
**Scope:** All 27 source files (`.venv` and `.claude/skills` excluded), against the full 19-pattern catalog + functional authorization test (Padrão 19)

## Context

This project had already gone through Phases 1–3 in prior sessions, including two v3.1 self-verification cycles that fixed 2 CRITICAL privilege-escalation findings (`PUT /users/:id` missing ownership/role-field checks, `POST /users` accepting `role` from the public signup payload — commits `b264380`, `31f1e69`). This run is a fresh, from-scratch re-read requested via a new `/refactor-arch` invocation, to confirm nothing has regressed.

## Method

1. Read every source file from scratch (models, controllers, routes, middleware, auth, services, utils, config, seed).
2. Grepped for residual signatures of all structural anti-patterns (MD5/SHA1, `eval`/`exec`/`os.system`, hardcoded secret literals, raw SQL/`SELECT *`, `global` keyword).
3. Ran a functional authorization test (Flask test client, in-memory SQLite) simulating real requests from a low-privilege user against every sensitive write endpoint — required by v3.1 step 7.b2, since a decorator's presence is not proof the logic inside is correct.

## Findings: 0 confirmed CRITICAL/HIGH/MEDIUM/LOW

### Structural checklist (19 patterns) — all clean

| # | Pattern | Result |
|---|---|---|
| 1 | SQL Injection | Clean — all queries via ORM (`.filter_by`, `.like()` with bound params, `func`) |
| 2 | Hardcoded Secrets | Clean — all via `Config`/`os.getenv`, `.env` gitignored |
| 3 | Weak Password Hashing | Clean — `pbkdf2:sha256` via `generate_password_hash` |
| 4 | God Class/Module | Clean — largest file well under 300 lines, MVC separation intact |
| 5 | N+1 Queries | Clean — `joinedload` on tasks, `GROUP BY`/`func.count` on categories & reports |
| 6 | Code Duplication | Clean — serialization centralized in `to_dict()` / `_task_to_dict_with_relations` |
| 7 | Monolithic Architecture | Clean — `config/`, `models/`, `routes/`, `controllers/`, `middleware/`, `auth/`, `services/`, `utils/` |
| 8 | Secrets in Responses | Clean — `User.to_dict()` never includes `password` |
| 9 | Sensitive Logs (PII) | Clean — `notification_service._mask_email()` masks email before logging |
| 10 | Mutable Global State | Clean — no `global` usage found |
| 11 | Magic Strings/Numbers | Clean — statuses/roles centralized in `Config.VALID_TASK_STATUSES`/`VALID_ROLES` |
| 12 | Unnecessary Ternaries | Clean |
| 13 | Dangerous Admin Endpoint | Clean — no arbitrary SQL/code execution endpoint exists |
| 14 | Plaintext Password Storage | Clean — hash on write, `check_password_hash` on read, excluded from responses |
| 15 | Broken Access Control | Clean — every sensitive route has `@login_required`/`@role_required` |
| 16 | Exception Detail Leakage | Clean — routes return controlled `ValueError`/`PermissionError` messages, not raw `str(e)` from unexpected exceptions; `get_tasks` catches generic `Exception` → generic message |
| 17 | Regression: Setup Per-Request | Clean — `db.create_all()` runs once at module load in `app.py`, not per-request |
| 18 | Dead Config | Clean — grepped all `Config.*` attributes; all have real usage points |
| 19 | Privilege Escalation (structural) | Clean — `PUT /users/:id` checks ownership + admin-only allowlist for `role`/`active`; `POST /users` forces `role='user'` server-side regardless of payload |

### Functional authorization test (Padrão 19, v3.1 step 7.b2) — all 9 assertions passed

Simulated via Flask test client against an in-memory DB with a real admin, a real low-privilege user, and a bystander user:

| Scenario | Expected | Result |
|---|---|---|
| Anonymous signup sends `role: "admin"` in payload | Server ignores it, stores `role='user'` | ✅ Pass |
| Low-priv user tries to self-promote via `PUT /users/<self>` `{"role":"admin"}` | 403 | ✅ Pass |
| Low-priv user tries to edit another user's account | 403 | ✅ Pass |
| Low-priv user tries `DELETE /users/<other>` | 403 (admin-only route) | ✅ Pass |
| Admin changes another user's role | 200 (legitimate case still works) | ✅ Pass |
| Low-priv user tries `POST /categories` | 403 (admin/manager only) | ✅ Pass |
| User edits their own non-sensitive field (`name`) | 200 (legitimate case still works) | ✅ Pass |

(One test transiently reported an unexpected pass on the first run; investigated and confirmed it was test-order pollution in the harness itself — an earlier assertion had legitimately promoted that user to `manager` — not an application bug. Corrected and re-run clean.)

## Non-finding note (informational only, not a CRITICAL)

`TaskController.update`/`.delete` (via `PUT`/`DELETE /tasks/:id`) apply to **any** task regardless of `task.user_id`, with no ownership check — any authenticated user (`role='user'`) can edit or delete a task assigned to someone else. This technically matches the *shape* of Padrão 19 (IDOR), but is **not classified as a finding** here because:

- `Task.user_id` is nullable and tasks can be unassigned, unlike `User` records which are inherently personal.
- `CategoryController` write operations are already gated to `admin`/`manager`, showing the app's authors *do* apply role gates deliberately where they intend restriction — tasks were left open by apparent design (a shared/collaborative task board, not a personal-task-per-user model), not by oversight.
- The domain description (README, seed data) shows tasks distributed across multiple users' plates with no stated single-owner-only editing rule.

Flagged here for visibility, not as an actionable CRITICAL — worth a explicit product decision if the intended model is actually "my tasks only."

## Status

✅ **Clean** — 0 confirmed findings requiring action. No further self-verification cycle needed.
