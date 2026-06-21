# Skill Platform Prototype UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next frontend prototype for the dual-entry Skill platform, covering the user-facing Skill Center and the operations-facing AI development and release workspace.

**Architecture:** Extend the existing Vite React prototype instead of replacing it. Reuse the current Skill marketplace visual language for user pages, upgrade the admin prototype into a task-driven operations console, and keep all prototype interactions in local frontend state backed by richer `managementData` records.

**Tech Stack:** React 18, TypeScript, Vite, existing CSS system, Python contract tests, npm build verification.

---

### Task 1: Lock the prototype contract

**Files:**
- Modify: `tests/test_web_frontend_contract.py`

- [ ] Add contract assertions for the new user-side information architecture, including `我的 Skill`, `Skill 商店`, `更新`, `启用`, usage metrics, and detail-page capability copy.
- [ ] Add contract assertions for the new operations-side workbench, AI development studio, review center, release management, MCP dependency blocking, and parent-child task copy.
- [ ] Run: `python3 -m pytest tests/test_web_frontend_contract.py -q`
- [ ] Confirm the new assertions fail for the intended missing UI strings or structures before implementation starts.

### Task 2: Expand prototype data and route-level state

**Files:**
- Modify: `web_frontend/src/managementData.ts`
- Modify: `web_frontend/src/App.tsx`

- [ ] Extend Skill and MCP data models with the extra fields needed by the approved spec, including enablement, update availability, usage metrics, store copy, task metadata, review state, release state, and dependency blockers.
- [ ] Add typed operations task records for Skill and MCP generation, testing, review, and release status.
- [ ] Keep routing lightweight, but add enough app state to switch between user routes and the operations workbench without backend dependencies.
- [ ] Preserve existing chat behavior and current Skill store entry points.

### Task 3: Upgrade the user-side Skill Center pages

**Files:**
- Modify: `web_frontend/src/pages/SkillCenterPage.tsx`
- Modify: `web_frontend/src/pages/SkillLibraryPage.tsx`
- Modify: `web_frontend/src/pages/SkillShowcasePage.tsx`
- Modify: `web_frontend/src/components/SkillCard.tsx`

- [ ] Refresh `我的 Skill` so it shows enable state, update state, and usage visibility in a more app-like management layout.
- [ ] Refresh `Skill 商店` so installed Skills can surface an `更新` action when a newer published version exists.
- [ ] Expand the Skill detail/showcase experience to include expected output, scenes, dependency summary, example input and output, and post-install usage context.
- [ ] Keep the visual tone aligned with the current approved Skill pages instead of introducing a new design language.

### Task 4: Build the operations workspace experience

**Files:**
- Modify: `web_frontend/src/components/AdminNav.tsx`
- Modify: `web_frontend/src/pages/SkillsPage.tsx`
- Modify: `web_frontend/src/pages/SkillDetailPage.tsx`
- Modify: `web_frontend/src/pages/McpsPage.tsx`
- Modify: `web_frontend/src/pages/McpDetailPage.tsx`
- Create: `web_frontend/src/pages/AdminWorkbenchPage.tsx`

- [ ] Add a workbench landing page that foregrounds pending tasks, failed tests, blocked-by-MCP items, pending review, and pending publish versions.
- [ ] Turn the Skill-side admin detail page into an AI Development Studio + Task Detail hybrid, with hybrid input fields, generation log, dependency graph, automated tests, editable critical docs, review readiness, and version status.
- [ ] Upgrade MCP management pages to better reflect draft vs published state, dependency impact, and release readiness.
- [ ] Expand admin navigation so the workbench sits above raw Skill/MCP catalogs.

### Task 5: Finish shared visual system and verify

**Files:**
- Modify: `web_frontend/src/styles/app.css`

- [ ] Add the new marketplace and operations-console sections needed for the approved prototype, reusing the existing red-accent, white-card aesthetic where possible.
- [ ] Ensure layouts remain readable at desktop and collapse acceptably on narrower widths used in local browser QA.
- [ ] Run: `python3 -m pytest tests/test_web_frontend_contract.py -q`
- [ ] Run: `npm run build` in `web_frontend/`
- [ ] Verify any failing assertions or build issues are fixed before completion.
