# Skill Step 1 Wizard Design

## Goal

Replace the current `引导流程` overview-first Skill detail experience with a testable Step 1 prototype that validates one core interaction:

- the user starts with one sentence
- the system asks 2 to 3 focused follow-up questions
- the answers are condensed into a structured summary
- the user can confirm before moving to generation

This prototype is only meant to test whether the new interaction feels clearer and lighter than the current page.

## Confirmed Product Decisions

- Use a conversation-first flow instead of showing all four creation steps at once.
- Keep the first step lightweight and focused on requirement clarification only.
- Use dynamic follow-up questions rather than a fixed two-question script.
- Limit the prototype to Step 1 so we can test the interaction before changing generation, document review, or automated testing.

## Problem In The Current Page

The current page mixes several stages at the same time:

- page-level actions such as enable and submit for review
- a four-step guided-flow explainer
- generated artifacts and logs
- document editing
- testing
- side status cards

This creates two problems:

1. The page feels visually crowded before the user has started the task.
2. The flow does not match the real mental model of creating a Skill with AI, because “AI generation” is shown as a static result area rather than a collaborative clarification process.

## Prototype Scope

The testable prototype only changes the `引导流程` tab on the Skill detail page.

It will include:

- a compact Step 1 hero area with a single primary prompt input
- a staged conversation area that reveals one assistant question at a time
- user response chips or short text answers for each follow-up
- a structured summary card that updates after answers are collected
- a clear primary CTA such as `确认需求并生成草案`

It will not include:

- real model calls
- real Skill or MCP file generation
- real state persistence across refresh
- changes to the `工作流`, `Schema`, or `测试` tabs
- changes to backend APIs

## Interaction Design

### Initial state

The page should open with only the minimum needed to begin:

- a short title such as `先用一句话描述你想做的 Skill`
- one text area or input
- one primary button to start
- a small hint showing example requests

The current large four-step explainer should not be visible at this point.

### Clarification phase

After the user enters the first sentence, the page should transition into a guided conversation.

Rules:

- show one assistant question at a time
- ask only about missing information
- stop after enough information is gathered or after 3 rounds at most
- keep the wording operational and concise

Question themes can include:

- what business problem this Skill should solve
- which scenarios or inputs it should cover
- what output form is expected
- whether it depends on an existing MCP or internal data source

### Summary phase

Once enough information is gathered, the system should present a structured summary with editable fields:

- Skill intent
- target scenarios
- expected output
- likely dependencies

This makes the AI clarification visible and gives the user confidence before generation.

### Handoff to next step

The last action in this prototype is not real generation. It only needs to make the next step legible.

Recommended behavior:

- clicking `确认需求并生成草案` shows a success state or stubbed transition card
- the UI explains that the next step will generate the draft Skill, dependencies, and examples

## Prototype Data Strategy

Use frontend-only mocked branches for the follow-up questions.

Recommended first-pass branches:

- data query / business lookup
- diagnostic analysis
- external web comparison

The first sentence can be matched with a simple keyword heuristic so the experience feels adaptive without requiring a real model.

## Layout Changes

Inside `引导流程`:

- remove the all-at-once stacked Step 1 through Step 4 panels
- replace them with a single centered Step 1 card and a progressive conversation canvas
- reduce the right-side status density during clarification
- keep review and test status hidden until after confirmation

The page should feel more like a guided setup wizard than a technical dashboard.

## Verification Plan

We will consider the prototype successful if an internal tester can:

1. Start from the detail page without feeling overloaded.
2. Understand what to type as the first input without extra explanation.
3. Complete 2 to 3 rounds of clarification without confusion.
4. Understand what will happen after clicking the final Step 1 confirmation CTA.

## Risks And Controls

- If the fake branching is too rigid, the flow will feel scripted rather than intelligent.
  Control: keep questions broad and only cover 3 initial scenario families.

- If too much of the old status UI remains visible, the page will still feel crowded.
  Control: prioritize a clean initial state and defer nonessential cards.

- If the summary is not editable, users may not trust the generated interpretation.
  Control: let the summary fields remain user-adjustable before moving on.

## Implementation Boundary

This change is intentionally a UI prototype, not a production workflow rewrite.

The next implementation plan should therefore focus on:

- refactoring the `引导流程` tab only
- adding mocked conversation state
- keeping the rest of the Skill detail page intact
- preserving existing prototype actions outside the new Step 1 flow
