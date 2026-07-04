# Permission Center Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace in-memory organization/account permission prototypes with a SQLite-backed permission center that returns real effective permissions.

**Architecture:** Add a dedicated SQLite permission repository alongside the chat repository, seed it with current prototype organizations/roles/accounts, and have FastAPI auth/account/organization endpoints read and mutate persisted records. Effective skills, data domains, action permissions, and admin visibility stay computed on the server so the frontend can continue consuming the existing contract.

**Tech Stack:** Python, FastAPI, SQLite, pytest, React TypeScript frontend consuming existing REST contracts

---

### Task 1: Lock the backend behavior with failing tests

**Files:**
- Modify: `tests/test_api_server.py`
- Test: `tests/test_api_server.py`

- [x] Add tests that prove organization permission updates and account permission overrides survive app restarts against the same SQLite file.
- [x] Add a test that proves effective permissions are computed from organization policy + role policy + account allow/deny overrides.
- [x] Run: `python3 -m pytest tests/test_api_server.py -q`
Expected: FAIL on the new persistence/effective-permission assertions before implementation.

### Task 2: Introduce a SQLite-backed permission repository

**Files:**
- Create: `permission_repository.py`
- Modify: `api_server.py`

- [x] Add a focused repository for organizations, roles, accounts, bindings, and override policies with schema initialization and seed data.
- [x] Implement service-style helpers that compute `effectiveSkills`, `effectiveDataDomains`, `effectiveActionPermissions`, and `canAccessAdmin`.
- [x] Wire `/api/auth/login`, `/api/auth/me`, `/api/admin/accounts`, `/api/admin/accounts/{accountId}/permissions`, `/api/organizations`, and `/api/organizations/{orgId}/permissions` to the new repository instead of process memory.

### Task 3: Verify contracts and frontend compatibility

**Files:**
- Modify: `tests/test_api_server.py`
- Modify: `tests/test_web_frontend_contract.py` (only if contract text needs to shift)
- Modify: `web_frontend/src/App.tsx` (only if compatibility adjustments are needed)

- [x] Run: `python3 -m pytest tests/test_api_server.py tests/test_web_frontend_contract.py -q`
Expected: PASS.
- [x] Run: `cd /Users/leo/work/ai_model/Cot_research/web_frontend && node ./node_modules/typescript/bin/tsc -b && node ./node_modules/vite/bin/vite.js build`
Expected: successful production build.
- [x] If either check fails, make the smallest contract-preserving fix and rerun the exact command.
