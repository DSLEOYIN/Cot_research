# Real Streaming UAT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver progressive workflow and answer streaming for UAT.

**Architecture:** Extend the existing FastAPI SSE endpoint with workflow-start, result-first, and answer-delta events. Keep persisted final messages unchanged while the React client maintains transient streaming state and renders it progressively.

**Tech Stack:** FastAPI, asyncio SSE, React, TypeScript, Vite, pytest.

---

### Task 1: Define Streaming Contracts

**Files:**
- Modify: `tests/test_api_server.py`
- Modify: `tests/test_web_frontend_contract.py`

- [x] Assert the API emits `step_started`, `result_ready`, and `answer_delta` in the required order.
- [x] Assert the frontend consumes the events, auto-collapses on answer output, uses a typewriter renderer, and places new conversation before online status.
- [x] Run focused tests and confirm they fail for missing behavior.

### Task 2: Implement API Streaming Phases

**Files:**
- Modify: `api_server.py`

- [x] Add answer splitting and chunking helpers.
- [x] Emit a running placeholder before execution and after completed nodes.
- [x] Emit table-first result content, then analysis chunks, then the persisted final message.
- [x] Run API tests.

### Task 3: Implement Progressive Frontend State

**Files:**
- Modify: `web_frontend/src/api/client.ts`
- Modify: `web_frontend/src/App.tsx`
- Modify: `web_frontend/src/components/MessageBubble.tsx`
- Modify: `web_frontend/src/components/ThoughtProcess.tsx`
- Create: `web_frontend/src/components/TypewriterResult.tsx`
- Modify: `web_frontend/src/components/ChatHeader.tsx`
- Modify: `web_frontend/src/styles/app.css`

- [x] Handle running steps, result-first content, answer deltas, and final persistence.
- [x] Keep workflow expanded until output begins, then auto-collapse.
- [x] Smoothly render answer deltas and reorder header actions.
- [x] Run frontend contract tests and production build.

### Task 4: Verify UAT

**Files:**
- No source changes expected.

- [x] Run full pytest suite.
- [x] Run frontend production build.
- [x] Exercise a real question in the in-app browser and verify all four UAT comments.
