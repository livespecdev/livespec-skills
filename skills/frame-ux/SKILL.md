---
name: frame-ux
description: |
  Frames the user experience for a spec feature and records it in the feature's `## UX` section:
  user flow, key decisions, patterns used, states, content, and accessibility, optionally with mockup
  assets. Reads ux/ concepts for the design system. Use when framing UX for a feature before
  implementation. Not for the core spec (/specify-feature) or technical approach (/frame-tech).
argument-hint: [feature-slug]
---

# UX Framing

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v0.1.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Frame the user experience for a feature and write it into the feature's `## UX` section (`SPEC.md` §7.3). Each durable UX decision is a `UX` spec item (§8.2): a checkbox line `- [ ] UX-N: ...`, written declaratively as target state. Free-form prose under `## UX` carries what items cannot: the user flow, the rationale, references to assets.

## Identify the feature

If `$ARGUMENTS` names a feature, `Read` `features/**/{slug}.md`. Otherwise `Glob features/**/*.md` and ask the user which one. Locate the project root (nearest manifest, `product-spec.yaml` or `livespec.yaml`, §3.1) and read its `mode` (§12).

## Gather context

1. **The feature**: its summary, REQs, ACs, and any existing `## UX` section.
2. **Personas** (`product/persona/*.md`) linked in frontmatter: goals, pain points, tech-savviness, context of use.
3. **The UX context** under `ux/`. List the actual type directories (`ux/*/`) rather than assuming a fixed set: the core taxonomy (§6.2) is `ui_component` (components and their usage rules), `design_principle` (UX beliefs), `ux_pattern` (reusable interaction/layout patterns), and `screen` (durable interface surfaces: what the surface is, how it is reached, how it connects to the rest), but a project may define extension types (§6.2) that carry axes the core set does not: form or navigation patterns, design tokens, layouts. An extension type you do not recognize is a valid part of this project's UX context, not noise: read the ones relevant to the feature. Reuse what you find rather than inventing.
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

Create one asset per key screen or state; do not over-produce. Reference them from the `## UX` prose.

## Review before writing

Before touching the file, present the full proposed `## UX` section for review: the `UX` items (patterns, states, content, accessibility), the user flow and rationale, plus any assets you plan to create. Ask the user to approve, adjust, or rethink. Iterate until approved.

## Write the `## UX` section

**Describe target state, not work to do.** A feature is an enduring description of what the software is (§1, §7). Write declaratively.

- "The area selector uses the combobox pattern with async search."
- "The first input in the modal receives focus on open."
- Avoid: "Replace the dropdown with a combobox", "Add auto-focus" (imperative, work-shaped, belongs in a PR description).

`Edit` the feature to add or update the `## UX` section (§7.3). In `loose` mode it MAY sit anywhere; in `strict` mode it follows the canonical order (Requirements → Assumptions → Questions → Limitations → UX → Tech, §7.3, §12). Preserve everything else in the file (losslessness, §14); never rewrite REQs or renumber IDs here.

```markdown
## UX

- [ ] UX-1: Today's completion toggles with a single tap anywhere on the habit row, not only on an icon.
- [ ] UX-2: The toggle is optimistic: the row shows the new state before the write confirms, per [[ux_pattern:optimistic-update]].
- [ ] UX-3: A logged-but-unsynced completion shows an offline-pending badge labelled "Not synced yet", cleared on sync.
- [ ] UX-4: With no habits yet, the list shows the create-habit call to action in place of rows.
- [ ] UX-5: The toggle is reachable by keyboard and exposes its checked state to screen readers; the pending badge is announced, not conveyed by color alone.

The check-in has to feel instant even offline, so nothing waits on the network. It reuses the existing list-row and toast patterns; the pending badge is the only new element.

### User flow

Habit list → tap habit row → today's completion toggles on (streak updates immediately) → tap again to undo.

### Assets

- Mockup: one-tap check-in, default and offline states (`assets/log-completion/check-in.svg`).
```

**What becomes an item.** Each choice the implementation must follow is a `UX` item: a component or pattern, a layout, how a state is shown, a label, an accessibility treatment. Apply the substitution test (§6.5, *Requirement vs. direction*): if a different interface could satisfy every REQ and AC while contradicting the statement, it is a direction and belongs here. If contradicting it would make an observable behavior wrong, it is an AC: note it for `/specify-feature` instead of writing it under `## UX` (a sync conflict that "resolves silently to one completion" is AC-2.3, not a UX choice).

**Items and IDs.** One decision per item, top-level only (no nested children, §8.1), no block constructs in the body. Extend the existing `UX-N` sequence; never renumber (§8.3). New items start `[ ]`: they turn `[x]` when the implementation applies them (`/implement-feature`, `/sync-spec`). To change an existing direction, do not rewrite it: mark it `[-]` with a resolution note (`→ Superseded by [UX-6]: ...`) and add the new direction as a new item (§8.1).

**What stays prose.** The summary of the approach and why, the user flow, sketches and asset references. Prose explains the items; it does not carry decisions of its own. A decision that only exists in prose cannot be referenced, anchored, or closed.

If you reused a `ux/` concept that is not yet linked, propose adding it to the feature's `links` (e.g. `ux_pattern: [optimistic-update]`, §9.2).

## Screens

When the project keeps `ux/screen/` files, treat them as the surfaces the feature lands on (§6.2):

- **Read before framing.** The screen file is where the surface is already described: how it is reached, who reaches it, what it is made of, and where it leads. Frame inside that, and name the part of the surface the feature touches instead of redescribing the page.
- **Link the feature.** Every screen the feature acts on belongs in the feature's `links.screen` (§9.2). That link is what makes "which features live on this screen" readable in reverse (§9.3); never write a list of features into a screen file.
- **New surface = new screen concept.** If framing introduces a page or a full-screen flow that did not exist, propose `ux/screen/{slug}.md` alongside the `## UX` section, and let the user confirm it via the diff. A concept body is free-form (§6.4): follow the sections the project's existing screen files already use rather than imposing a template, and where there is none yet, cover what the surface is, how it is reached, and how it connects to the rest.
- **Screen change = proposed edit.** If framing changes a surface durably (a new region, a new state, a new navigation edge), propose the edit to the screen file. Feature-specific behavior stays in the feature: a screen file carries no acceptance criteria (§6.5).

## Propose new concepts, do not impose

If framing established a reusable interaction or component rule that would apply to other features, that is a concept (a `ux_pattern`, `ui_component`, `design_principle`, or `screen`, §6.5), not a feature note. Propose it as a new file under `ux/{type}/{slug}.md` and let the user confirm via the diff before writing; product-level UX decisions are reviewed, not silently committed.

## Wrap up

Summarize the key decisions and any open items. Then offer one next step: if `## Tech` is missing, offer `/frame-tech`; if tech framing is already done, the feature is fully framed, so offer to start `/implement-feature`. There is no status to flip (§10): readiness is simply that both `## UX` and `## Tech` are present and the spec items are ready to implement.

---

For complex features (new interaction patterns, multi-step flows, significant design-system work), delegate to the `ux-framer` subagent, which writes the `## UX` section and assets directly, operating only on the local files.
