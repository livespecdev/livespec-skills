---
name: frame-ux
description: |
  Frames the user experience for a LiveSpec feature and records it in the feature's `## UX` section:
  user flow, key decisions, patterns used, states, content, and accessibility, optionally with mockup
  assets. Reads ux/ concepts for the design system. Use when framing UX for a feature before
  implementation. Not for the core spec (/specify-feature) or technical approach (/frame-tech).
argument-hint: [feature-slug]
---

# UX Framing

> **Format reference.** The `§N` citations point to the bundled LiveSpec spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft.2`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Frame the user experience for a feature and write it into the feature's `## UX` section (`SPEC.md` §7.3). LiveSpec does not yet define a `UX_DIRECTION` spec-item type (deferred, §15 #005), so UX decisions live as free-form notes under `## UX`, written declaratively as target state.

## Identify the feature

If `$ARGUMENTS` names a feature, `Read` `features/**/{slug}.md`. Otherwise `Glob features/**/*.md` and ask the user which one. Locate the project root (nearest `livespec.yaml`, §3.1) and read its `mode` (§12).

## Gather context

1. **The feature**: its summary, REQs, ACs, and any existing `## UX` section.
2. **Personas** (`product/persona/*.md`) linked in frontmatter: goals, pain points, tech-savviness, context of use.
3. **The design system** under `ux/` (§6.2): `ui_component` (components and their usage rules), `design_principle` (UX beliefs), `ux_pattern` (reusable interaction/layout patterns). Reuse these rather than inventing.
4. **Related features** for flow consistency.

## Analyze and propose

### Step 1: Quick direction check

Present your high-level approach briefly: the key user flow (2-3 steps), the main patterns you will reuse from `ux/`, and any obvious concern. Use `AskUserQuestion` to confirm the direction before detailed work, folding clarifying questions into the same checkpoint.

### Step 2: Gap analysis (internal checklist)

Work these through internally to ensure completeness; you do not present each one:

- **User flow**: happy path, entry/exit points, error states, edge cases (empty, loading, partial).
- **Information architecture**: where it lives, hierarchy, progressive disclosure, navigation.
- **Interactions**: input methods, feedback, affordances, confirmation/undo for destructive actions.
- **Content**: labels, help text, error messages, empty states.
- **Accessibility**: keyboard navigation, screen reader support, contrast, focus management.

### Step 3: Synthesize

Pull it into a coherent approach: flow summary (entry → steps → completion), key screens/states, patterns used from the design system, deviations with rationale, content strategy. Surface remaining decisions that affect implementation with `AskUserQuestion` (batch up to 4, 2-3 options with the recommended first, plus "Leave open"); defer minor polish.

## Mockups (optional, §11)

If the feature involves substantial UI (new screens, a new major component, a significant multi-state flow), offer to create mockup assets. Skip for minor UI (a label change, one button on an existing screen).

On acceptance, store each asset on disk and declare it in the feature frontmatter (§11):

- File path: `assets/{feature-slug}/{filename}`, in the `assets/` directory **next to the feature file** (same level whether the feature sits under an area or directly in `features/`, §11.1).
- Declare it in frontmatter `assets:` with `id` (a stable identifier), `type` (`wireframe` | `mockup` | `diagram` | `screenshot` | `reference`), `title`, optional `description`, and `path` (project-root-relative):

```yaml
assets:
  - id: 019c5325-d453-760e-a970-396b261743b2
    type: mockup
    title: One-tap check-in, default and offline states
    description: Habit row showing today's toggle and the offline-pending badge
    path: assets/log-completion/check-in.svg
```

Create one asset per key screen or state; do not over-produce. Reference them from the `## UX` notes.

## Review before writing

Before touching the file, present the full proposed `## UX` section for review: the user flow, key decisions, patterns, states, content, and accessibility notes, plus any assets you plan to create. Ask the user to approve, adjust, or rethink. Iterate until approved.

## Write the `## UX` section

**Describe target state, not work to do.** A feature is an enduring description of what the software is (§1, §7). Write declaratively.

- "The area selector uses the combobox pattern with async search."
- "The first input in the modal receives focus on open."
- Avoid: "Replace the dropdown with a combobox", "Add auto-focus" (imperative, work-shaped, belongs in a PR description).

`Edit` the feature to add or update the `## UX` section (§7.3). In `loose` mode it MAY sit anywhere; in `strict` mode it follows the canonical order (Requirements → Assumptions → Questions → Issues → UX → Tech, §7.3, §12). Preserve everything else in the file (losslessness, §14); never rewrite REQs or renumber IDs here.

```markdown
## UX

The check-in is a single tap on the habit row, with an optimistic toggle so it feels instant even offline. Reuses the existing list-row and toast patterns; the only new element is the offline-pending badge.

### User flow

Habit list → tap habit row → today's completion toggles on (streak updates immediately) → tap again to undo.

### Key decisions

- Optimistic toggle: the row reflects the new state before the write confirms, reusing [[ux_pattern:optimistic-update]].
- Offline-pending badge: a logged-but-unsynced completion shows a small badge, cleared on sync.

### States

- Empty: no habits yet shows the create-habit call to action.
- Offline: completions log normally; the pending badge communicates sync status.
- Error: a sync conflict resolves silently to a single completion (see AC-2.3); no user-facing error.

### Content

- Row affordance: the whole row is tappable, not just an icon.
- Pending badge label: "Not synced yet".

### Accessibility

- The toggle is reachable by keyboard and exposes its checked state to screen readers.
- The pending badge is announced, not conveyed by color alone.

### Assets

- Mockup: one-tap check-in, default and offline states (`assets/log-completion/check-in.svg`).
```

If you reused a `ux/` concept that is not yet linked, propose adding it to the feature's `links` (e.g. `ux_pattern: [optimistic-update]`, §9.2).

## Propose new concepts, do not impose

If framing established a reusable interaction or component rule that would apply to other features, that is a concept (a `ux_pattern`, `ui_component`, or `design_principle`, §6.5), not a feature note. Propose it as a new file under `ux/{type}/{slug}.md` and let the user confirm via the diff before writing; product-level UX decisions are reviewed, not silently committed.

## Wrap up

Summarize the key decisions and any open items. Then offer one next step: if `## Tech` is missing, offer `/frame-tech`; if tech framing is already done, the feature is fully framed, so offer to start `/implement-feature`. There is no status to flip (§10): readiness is simply that both `## UX` and `## Tech` are present and the spec items are ready to implement.

---

For complex features (new interaction patterns, multi-step flows, significant design-system work), delegate to the `ux-framer` subagent, which writes the `## UX` section and assets directly, operating only on the local files.
