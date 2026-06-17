# Bundled format reference

These files are a **vendored copy** of the LiveSpec format specification, shipped with the plugin so the skills and agents can resolve format rules at runtime with no network access and no separate clone.

| File | What it is |
|---|---|
| `SPEC.md` | The normative LiveSpec format spec, byte-identical to upstream. The `§N` citations throughout the skills and agents refer to its sections. |
| `CHEATSHEET.md` | A condensed reference, cheaper in tokens. Read this first; fall back to `SPEC.md` for edge cases. |

## Pinned version

`v1.0.0-draft.2`. The plugin targets this format version (see `.claude-plugin/plugin.json` and the project `CLAUDE.md`). The format is not frozen until `1.0.0`, so expect churn.

## How skills reference these files

Skills and agents point here with **relative paths** (`../../reference/SPEC.md` from a skill, `../reference/SPEC.md` from an agent) and the model reads them on demand. `${CLAUDE_PLUGIN_ROOT}` is not used: it does not expand inside skill or agent prose, only in hook, MCP, and LSP configuration.

## Re-vendoring

Upstream lives in the separate `livespec` repository. When the format version bumps, refresh these copies and update the pinned version above and in `plugin.json`:

```
cp /path/to/livespec/SPEC.md       reference/SPEC.md
cp /path/to/livespec/CHEATSHEET.md reference/CHEATSHEET.md
```
