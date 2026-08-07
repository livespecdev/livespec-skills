# Bundled format reference

These files are a **vendored copy** of the LiveSpec format specification, shipped with the plugin so the skills and agents can resolve format rules at runtime with no network access and no separate clone.

| File | What it is |
|---|---|
| `SPEC.md` | The normative LiveSpec format spec, byte-identical to upstream. The `§N` citations throughout the skills and agents refer to its sections. |
| `CHEATSHEET.md` | A condensed reference, cheaper in tokens. Read this first; fall back to `SPEC.md` for edge cases. |

## Pinned version

`v0.1.0-draft`. The plugin targets this format version (see `.claude-plugin/plugin.json` and the project `CLAUDE.md`). The format is not frozen until `1.0.0`, so expect churn.

## How skills reference these files

Skills and agents point here with **relative paths** (`../../reference/SPEC.md` from a skill, `../reference/SPEC.md` from an agent) and the model reads them on demand. `${CLAUDE_PLUGIN_ROOT}` is not used: it does not expand inside skill or agent prose, only in hook, MCP, and LSP configuration.

## Re-vendoring

Upstream lives in the separate `livespec` repository. To refresh these copies, run the vendoring script from the plugin root:

```
./update-spec.sh            # vendor from livespec HEAD
./update-spec.sh <ref>      # vendor from a specific tag/commit (reproducible)
```

It pulls `SPEC.md` + `CHEATSHEET.md` from a **committed** ref of `livespec` (never its working tree) and re-pins the format version across this file, the top-level `README.md`, and `CLAUDE.md`. Set `LIVESPEC_SRC` if the `livespec` checkout is not at `~/Dev/livespec`. Commit the version change in `livespec` first: the script vendors committed content by design.
