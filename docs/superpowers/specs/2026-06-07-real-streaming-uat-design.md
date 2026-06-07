# Real Streaming UAT Design

## Goal

Make the ChatBI UAT experience visibly progressive: workflow nodes complete one by one, data results appear before analysis, analysis streams with a smooth typewriter effect, and the workflow collapses only when user-facing answer output begins.

## Event Flow

The streaming API emits:

1. `message_created` for the persisted user message.
2. `step_started` for the active workflow placeholder.
3. `step_completed` whenever the engine callback completes a workflow node.
4. `result_ready` with the data/table-first portion of the answer.
5. `answer_delta` chunks for the remaining analysis.
6. `answer_completed` with the persisted complete assistant message.

The frontend replaces the active running placeholder as each node completes, appends a new running placeholder while the engine continues, and keeps the thought process expanded. On the first `result_ready` or `answer_delta`, it collapses the thought process and progressively renders the answer.

## Rendering

`ResultRenderer` receives partial content throughout streaming. Markdown tables and their charts render as soon as the table-first content arrives. Remaining analysis text is appended by a requestAnimationFrame-driven typewriter queue so network chunk boundaries do not create jerky updates.

The header action order becomes history toggle, new conversation, online status.

## Compatibility

The final assistant message and all completed steps remain persisted exactly as before. Existing non-streaming API behavior remains unchanged.

## Verification

- API test asserts event order and answer reconstruction.
- Frontend contract tests assert all new event handlers, automatic collapse trigger, typewriter component, and header action order.
- Full pytest suite and frontend production build.
- Browser UAT verifies progressive workflow state, table-first rendering, typewriter analysis, auto-collapse, and header order.
