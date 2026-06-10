# Workflow Step Colors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved clean blue-green palette to all workflow node states.

**Architecture:** Keep the existing React markup and state classes unchanged. Implement the visual update entirely through scoped selectors in the existing frontend stylesheet, protected by a focused CSS contract test.

**Tech Stack:** React, TypeScript, CSS, pytest

---

### Task 1: Lock the workflow state palette

**Files:**
- Modify: `tests/test_web_frontend_contract.py`
- Modify: `web_frontend/src/styles/app.css`

- [ ] Add a CSS contract test that checks completed, running, and failed node surfaces and text colors.
- [ ] Run the focused test and confirm it fails before the new palette exists.
- [ ] Add scoped state selectors for node background, border, icon, title, description, and status colors.
- [ ] Run the focused test and the complete frontend contract suite.
- [ ] Run the frontend production build.
- [ ] Verify the result in the real ChatBI page.
