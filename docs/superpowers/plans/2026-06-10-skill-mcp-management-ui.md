# Skill MCP Management UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing ChatBI frontend into a unified three-page workspace with Chat, Skill management, and MCP management prototypes.

**Architecture:** Keep the existing React/Vite chat flow intact and add a lightweight browser-history router, a shared application shell, focused management page components, and local prototype data/state. Management writes and tests remain frontend-only while the chat page continues using the current API.

**Tech Stack:** React 18, TypeScript, Vite, existing CSS system, pytest contract tests, in-app browser QA.

---

### Task 1: Lock the frontend management contract

**Files:**
- Modify: `tests/test_web_frontend_contract.py`

- [ ] Add failing contract tests for global navigation, Skill/MCP pages, cross-page links, workflow editing, Schema views, health checks, and prototype-mode copy.
- [ ] Run `python3 -m pytest tests/test_web_frontend_contract.py -q` and confirm the new tests fail because the management files do not exist.

### Task 2: Add management domain data and lightweight routing

**Files:**
- Create: `web_frontend/src/managementData.ts`
- Create: `web_frontend/src/useWorkspaceRoute.ts`
- Create: `web_frontend/src/components/AppShell.tsx`
- Create: `web_frontend/src/components/GlobalNav.tsx`
- Modify: `web_frontend/src/App.tsx`

- [ ] Define typed prototype data for the current 6 Skills and 7 MCPs, including dependency relationships, statuses, schemas, and workflow steps.
- [ ] Implement browser-history navigation for `/chat`, `/skills`, `/skills/:name`, `/mcps`, and `/mcps/:name`.
- [ ] Wrap the existing chat page in the shared application shell without changing its API behavior.

### Task 3: Build Skill management

**Files:**
- Create: `web_frontend/src/components/ManagementUi.tsx`
- Create: `web_frontend/src/pages/SkillsPage.tsx`
- Create: `web_frontend/src/pages/SkillDetailPage.tsx`

- [ ] Build searchable/filterable Skill cards with metrics and status actions.
- [ ] Build Skill detail tabs for overview, workflow, Schema, and test console.
- [ ] Add prototype edit, step add/reorder, enable/disable, and test interactions.
- [ ] Link MCP dependencies to their MCP detail pages.

### Task 4: Build MCP management

**Files:**
- Create: `web_frontend/src/pages/McpsPage.tsx`
- Create: `web_frontend/src/pages/McpDetailPage.tsx`

- [ ] Build searchable/filterable MCP status table with bulk health-check interaction.
- [ ] Build MCP detail tabs for overview, configuration, Schema, and test/log console.
- [ ] Add prototype config masking, enable/disable confirmation, health test, and dependency links.

### Task 5: Finish the visual system and verify

**Files:**
- Modify: `web_frontend/src/styles/app.css`

- [ ] Add responsive application shell, management cards, tables, tabs, editors, dialogs, and status styles consistent with the current ChatBI page.
- [ ] Run `python3 -m pytest tests/test_web_frontend_contract.py -q`.
- [ ] Run `npm run build` in `web_frontend/`.
- [ ] Start the API and Vite frontend, then verify Chat, Skill, and MCP flows in the in-app browser at desktop width.
