# Structured ECharts And Visual QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the remaining mock-mode production Web work by rendering reliable charts from tabular answers and visually verifying the result against the approved prototype.

**Architecture:** Keep the backend response contract unchanged. Parse Markdown tables in the React result renderer, render the table with the existing `DataTable`, and render an ECharts chart only when the table contains a category column plus numeric series.

**Tech Stack:** React, TypeScript, ECharts, Vite, pytest, in-app browser

---

### Task 1: Add The Chart Rendering Contract

**Files:**
- Modify: `tests/test_web_frontend_contract.py`

- [x] Add a failing contract test requiring `ResultRenderer` to use `DataTable` and `EChartsPanel`.
- [x] Require `EChartsPanel` to initialize and dispose an ECharts instance.
- [x] Run `pytest tests/test_web_frontend_contract.py -q` and confirm the new test fails for the missing implementation.

### Task 2: Implement Structured Chart Rendering

**Files:**
- Modify: `web_frontend/src/components/ResultRenderer.tsx`
- Modify: `web_frontend/src/components/EChartsPanel.tsx`
- Modify: `web_frontend/src/styles/app.css`

- [x] Parse Markdown table rows without changing the backend API.
- [x] Convert numeric table columns into ECharts series and skip charts for non-numeric tables.
- [x] Render the reusable `DataTable` and responsive chart panel.
- [x] Run the focused contract test and frontend build.

### Task 3: Verify The Production Web Experience

**Files:**
- Modify: `doc/codex_前端优化版本_20260605.md`
- Modify: `qa/UAT_20260605_前端优化生产Web入口验收报告.md`

- [x] Run the full pytest suite and frontend build.
- [x] Start mock API and Vite, then verify the approved desktop flow in the browser.
- [x] Check narrow-screen layout and confirm no horizontal page overflow.
- [x] Record verification results and remaining Real-mode dependency.
