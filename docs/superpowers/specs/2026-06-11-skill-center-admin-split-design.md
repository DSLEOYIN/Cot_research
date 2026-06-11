# Skill Center And Admin Split Design

## Decision

Split the current technical Skill management experience into two products inside the same ChatBI workspace:

- **Skill Center (`/skills`)**: user-facing discovery, value explanation, examples, animated outcome demo, installation, and immediate trial.
- **System Management (`/admin/skills`, `/admin/mcps`)**: operations-facing workflow, Schema, dependency, configuration, health-check, and enable/disable controls.

The first version is an internal curated Skill store. Installing a Skill means enabling it for the current user in frontend prototype state.

## User Experience

The Skill Center list leads with outcomes rather than technical structure. Users can search by goal, browse categories, see installed and recommended Skills, and understand the value of each Skill from its card.

The Skill showcase page answers, in order:

1. What can this Skill do for me?
2. What will the result look like?
3. Which real scenarios does it support?
4. What does it need access to?
5. How do I install or try it?

An animated demo shows a representative question moving through understandable business stages and ending in a result preview. It does not expose MCP, Schema, or parameter mappings.

## Operations Experience

The existing technical Skill and MCP pages remain available under System Management. Their routes change to `/admin/skills`, `/admin/skills/:name`, `/admin/mcps`, and `/admin/mcps/:name`. Cross-links between technical Skill and MCP pages use the admin routes.

## Navigation

Primary navigation becomes:

- 智能问答
- Skill 中心
- 系统管理

System Management opens the Skill administration page and provides visible tabs for Skill 管理 and MCP 管理.

## Prototype Boundaries

- Installation state is local frontend state.
- “立即体验” navigates to Chat and pre-fills the input with a representative example.
- Existing Chat API behavior remains unchanged.
- Admin write operations remain prototype-only.
