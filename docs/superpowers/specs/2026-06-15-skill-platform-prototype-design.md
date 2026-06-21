# Skill Platform Prototype Design

## Goal

Define the next prototype for a dual-entry Skill platform:

- a user-facing Skill Center for discovery, installation, and use
- an operations-facing AI development and publishing platform for Skill and MCP lifecycle management

This prototype should let operations staff complete the full authoring, testing, review, and release flow inside the system without leaving to manually test Skill or MCP assets elsewhere.

## Product Decision

Use two separate entrances with permission-based menu isolation:

- **User entry**: only exposes the Skill Center experience
- **Operations entry**: exposes the AI development, review, release, Skill management, and MCP management experience

Do not merge user and operations tasks into one navigation tree with role switching inside the same page shell. The information density, terminology, and actions are too different.

## Users

### End user

Needs to:

- see installed Skills
- browse Skills available in the store
- install Skills
- enable installed Skills before use
- view usage frequency and usage status for installed Skills and related MCP usage

Does not need to:

- see the system management entrance
- see unpublished versions
- review or edit Skill and MCP internals
- rate, favorite, or leave public feedback in v1

### Operations user

Needs to:

- describe a desired Skill or MCP in natural language
- provide a few structured fields to guide generation
- let AI generate draft Skill and MCP assets according to project standards
- run automated tests inside the system
- inspect key documents and examples
- edit generated content when needed
- review and approve versions
- manually publish approved versions
- manage MCP dependencies required by Skills

## Source Constraints

The prototype must align with the repository standards described in:

- [mcp_and_skill_standard_specs.md](/Users/leo/work/ai_model/Cot_research/doc/mcp_and_skill_standard_specs.md:1)
- [skills](/Users/leo/work/ai_model/Cot_research/skills:1)
- [mcps](/Users/leo/work/ai_model/Cot_research/mcps:1)

That means:

- MCPs are real Python modules under `mcps/`
- Skills are real Python modules under `skills/`
- both follow standard config contracts such as `inputSchema`, `mcpTools`, and flow step definitions
- AI-generated output is not just a mock card; it should represent actual repository-ready assets

## Approaches Considered

### Approach A: One unified management page

Put My Skills, Store, Skill authoring, MCP authoring, and release into one large workspace with tabs.

**Pros**

- fewer top-level routes
- quick to prototype at low fidelity

**Cons**

- user and operations mental models collide
- review and release become buried behind store terminology
- permission isolation becomes harder to reason about

### Approach B: Two independent products in the same system

Split the user-facing Skill Center from the operations-facing authoring and release platform.

**Pros**

- clean role separation
- easier menu permission control
- easier to scale review, release, and dependency workflows
- clearer terminology for each audience

**Cons**

- more routes and templates to design
- requires stronger cross-product consistency

### Approach C: User center + admin list pages only

Keep the user side clean, but make the operations side a thin CRUD console for Skill and MCP records.

**Pros**

- fast to implement
- familiar to internal users

**Cons**

- does not fit the actual desired workflow
- ignores AI-first generation and automated testing as the core value
- forces complex work into generic forms

## Recommendation

Choose **Approach B**.

The operations side is not a traditional configuration backend. It is an **AI-assisted production workbench** plus a **review and release console**. That distinction should be visible in the information architecture and the landing page hierarchy.

## Information Architecture

### User entry

- `Skill Center`
- `My Skills`
- `Skill Store`
- `Skill Detail`

### Operations entry

- `Workbench`
- `AI Development Studio`
- `Task Detail`
- `Review Center`
- `Release Management`
- `Skill Management`
- `MCP Management`

## User Experience Design

### Skill Center

The Skill Center is the user-facing shell. It should prioritize outcome language over technical implementation detail.

Primary areas:

- **My Skills**: installed, update available, enable status, recent usage, usage trends
- **Skill Store**: browse, search, filter, install, preview

### My Skills

The My Skills page should answer:

1. Which Skills do I already have?
2. Which ones are enabled and ready?
3. Which ones need updates?
4. Which ones do I use often?

Core modules:

- installed Skill list
- status chips: enabled, disabled, update available
- usage metrics: frequency, recent calls, success/failure summary
- actions: enable, disable, update, uninstall, open detail

### Skill Store

The store should feel closer to an app marketplace than a technical registry.

Core modules:

- search
- category filters
- curated recommendations
- newest updates
- Skill cards with clear value proposition

Rules:

- no visible history of multiple versions with the same Skill name
- if installed and a newer published version exists, show an iOS-style `Update` action
- installation alone does not make a Skill active; enablement is a second action or step

### Skill Detail

The detail page should help the user decide whether to install and enable a Skill.

Sections:

- purpose and business value
- scenes where it should be used
- expected output shape
- dependency summary
- example input and output
- install state and update state
- usage stats after installation

Do not expose full prompt internals or workflow DSL by default on the user side.

## Operations Experience Design

### Workbench

The operations home should be task-driven, not asset-list-driven.

Top modules:

- tasks needing input
- auto-test failures
- pending review
- approved but not published
- blocked by unpublished MCP dependencies
- recent releases

This page is the control tower for throughput and blockers.

### AI Development Studio

Use a **hybrid input model**:

- structured fields for minimum required metadata
- a large natural-language command area for intent and constraints

Required fields for v1:

- name
- goal
- applicable scenes or when to use
- expected output

Recommended optional fields for v1:

- example user input
- example expected output
- whether this likely requires a new MCP
- dependency notes

The studio should then let AI generate:

- draft Skill spec or MCP spec
- repository-ready file structure preview
- key documentation summary
- example I/O
- test plan proposal

### Task Detail

Task Detail is the main execution page for generated work.

Sections:

- request summary
- AI generation log
- generated assets list
- dependency graph
- automated test results
- editable key documents
- version metadata
- review readiness status

The user should be able to inspect and edit critical material without leaving the system.

### Review Center

Review focuses on whether the version is understandable, safe, and useful.

Required review content:

- function and business purpose
- execution flow
- dependent MCP tools
- example input and output

The review page should support:

- approve
- reject with reason
- send back for edits
- compare current draft with previous published version

### Release Management

Publishing is manual even after approval.

Rules:

- multiple versions may pass review
- only one version of a Skill is store-visible at a time
- the same rule applies to MCP release state where relevant
- release, rollback, and unpublish should be explicit operations

The release page should make “approved but not published” highly visible.

### Skill Management

Skill Management is the catalog of all Skills known to operations, across states.

It should support:

- search and filter by status
- inspect dependency status
- inspect current published version
- inspect pending draft versions
- jump into task, review, or release views

### MCP Management

MCP Management should surface:

- published and draft MCPs
- Skills depending on each MCP
- health status
- test results
- release readiness

This page is especially important because MCPs are dependency infrastructure, not just store items.

## Dependency Workflow

When a new Skill depends on an MCP that is not yet published, the system should use a **parent-child task model**:

1. operations user creates a Skill task
2. AI detects missing MCP dependency
3. system creates one or more MCP child tasks
4. MCP child tasks go through generate, test, review, and publish
5. after required MCP versions are published, the Skill task resumes integration testing
6. the Skill version can then move to review and manual publish

This is the preferred v1 behavior because it preserves clean release boundaries while reducing manual coordination work.

## State Model

Recommended shared lifecycle states:

- draft
- generating
- generated
- testing
- test_failed
- ready_for_review
- review_rejected
- review_approved
- ready_to_publish
- published
- unpublished
- rolled_back
- blocked_by_dependency

The UI should visually differentiate:

- currently actionable
- waiting on someone
- waiting on dependency
- failed and needs intervention

## Automated Testing Model

The system promise is that operations users do not leave the platform to manually validate generated Skill or MCP assets.

### Testing principles

- every generated Skill and MCP must pass automated tests before submission for review
- testing should be initiated and orchestrated by the platform
- the system may allow AI to retry fixes after test failure before requiring human intervention
- failed tests should surface actionable summaries, not raw logs alone

### MCP testing baseline

Minimum expectations:

- module imports successfully
- registration metadata is structurally valid
- `inputSchema` matches expected contract shape
- representative mock or safe test calls return valid result format
- failure path returns clear structured errors

### Skill testing baseline

Minimum expectations:

- module imports successfully
- `SKILL_CONFIG` is structurally valid
- required `mcpTools` references are resolvable
- flow step references and template variables are valid
- representative input runs through a safe validation path
- expected output contract can be produced or simulated

### Test UX

The prototype should show:

- overall pass/fail banner
- per-test case results
- retry button
- AI auto-fix attempt status
- evidence that review submission is locked until test pass

## Analytics And Usage Visibility

User side should show usage visibility for both Skills and related MCP activity in a simplified way.

Recommended v1 metrics:

- install count for the current user
- enabled vs disabled state
- use frequency
- last used time
- success/failure ratio
- top dependent MCPs used by this Skill

Operations side can expose more detail, but the user-facing version should stay lightweight.

## Navigation Principles

- user and operations navigation should never appear mixed in the same menu for unauthorized users
- store language should be value-oriented and friendly
- operations language should be action-oriented and workflow-oriented
- tasks and blockers should be visible from the first screen on the operations side

## Visual Direction

### User side

Use a marketplace visual language:

- strong card hierarchy
- clear install and update affordances
- approachable value messaging
- personal activity summaries

### Operations side

Use a production-console visual language:

- dense but readable task tables
- dependency and status emphasis
- side-by-side diff and test evidence areas
- clear primary actions around generate, retest, review, and publish

The two sides should feel related, but not identical.

## Prototype Boundaries

For the next prototype:

- user install and enable state may be frontend or lightweight app state
- task generation, testing, review, and release can be simulated at the interaction layer if backend orchestration is not complete
- UI should still model the real repository concepts and real release states

Avoid in this phase:

- organization-level installs
- ratings, favorites, and public comments
- exposing store users to version history complexity
- mixing unpublished drafts into the user store

## Open Design Questions

- whether enabling happens inline on install success or as a separate explicit action in My Skills
- how much editable generated source should appear directly in Task Detail before it becomes too IDE-like
- whether user-facing MCP usage is shown directly or only summarized through Skill usage detail

## Recommended Next Deliverables

1. low-fidelity wireframe spec for the six core pages
2. page-level component inventory
3. clickable prototype for user and operations entry
4. implementation plan for frontend routes, state, and prototype data contracts
