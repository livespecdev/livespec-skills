#!/usr/bin/env python3
"""check-drift: coherence between spec intent and codebase reality.

Cross-references the checkbox state of spec items (§8.1) with the `implements:` / `see-spec:`
markers found in source code (§9.4). Answers: does the code say the same thing
as the spec?

The format defines the marker syntax and explicitly leaves coverage rules and
drift detection to tooling (§9.4, "Scope of this section"). This script is one
such tool. It reports, it never writes: the fixes belong to /sync-spec (spec
side) or /implement-feature (code side).

Usage:
  python3 check_drift.py [PROJECT_ROOT] [--code-root DIR] [--feature SLUG] [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from livespec import (  # noqa: E402
    CONCEPT_ROOTS,
    Project,
    Report,
    emit,
    repo_root,
    resolve_project,
    scan_markers,
)

CHECKS = [
    "marker-unknown-feature",
    "marker-unknown-id",
    "marker-on-cancelled",
    "marker-on-open",
    "marker-on-closed",
    "marker-legacy-verb",
    "marker-verb-fit",
    "done-unmarked",
    "open-unmarked",
    "feature-unmarked",
]


# §9.4: the verb writers SHOULD use for each item type. Readers accept any pairing.
REALIZABLE = ("REQ", "AC", "UX", "TECH")
REFERENCE_ONLY = ("AS", "Q", "LIM")


def anchor_targets(project: Project, features):
    """Spec items whose marker coverage is reported: REQ and AC only.

    UX and TECH directions MAY carry markers too (§9.4) and those markers are
    resolved, but a direction with no marker is not a gap: many directions
    (a layout, a wording choice) have no single code site to point at.
    """
    for feature in features:
        for item in feature.items:
            if item.type in ("REQ", "AC"):
                yield feature, item


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check spec intent against codebase reality.")
    parser.add_argument("project", nargs="?", help="project root (defaults to discovery from CWD)")
    parser.add_argument("--code-root", help="directory to scan for code markers (defaults to the git repo root)")
    parser.add_argument("--feature", help="restrict the report to one feature slug")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--only", help="comma-separated checks to run")
    parser.add_argument("--skip", help="comma-separated checks to skip")
    parser.add_argument("--list-checks", action="store_true", help="print available checks and exit")
    args = parser.parse_args(argv)

    if args.list_checks:
        for name in CHECKS:
            print(name)
        return 0

    enabled = set(CHECKS)
    if args.only:
        requested = {c.strip() for c in args.only.split(",") if c.strip()}
        unknown = requested - set(CHECKS)
        if unknown:
            print(f"error: unknown check(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        enabled = requested
    if args.skip:
        enabled -= {c.strip() for c in args.skip.split(",") if c.strip()}

    project = resolve_project(args.project, Path.cwd())

    if args.code_root:
        code_root = Path(args.code_root).expanduser().resolve()
        if not code_root.is_dir():
            print(f"error: --code-root {code_root} is not a directory", file=sys.stderr)
            return 2
    else:
        code_root = repo_root(project.root)
        if code_root == project.root and not any(
            (project.root / d).is_dir() for d in ("src", "lib", "app")
        ):
            # Spec-only repo: the code most likely lives beside it, not under it.
            code_root = project.root

    # Markers inside the spec tree itself are prose, not anchors.
    exclude = [project.root / d for d in (*CONCEPT_ROOTS, "features")]
    markers = scan_markers(code_root, exclude=exclude)

    report = Report("check-drift", project, scope=args.feature)

    features = project.features
    if args.feature:
        features = [f for f in features if f.slug == args.feature]
        if not features:
            print(f"error: no feature '{args.feature}' in {project.root}", file=sys.stderr)
            return 2
    in_scope = {f.slug for f in features}

    # ---- marker side: every marker must resolve (§9.4)
    # Coverage counts only markers that claim the code realizes the item
    # (`implements:`, or the legacy `livespec:`); `see-spec:` markers resolve
    # and are checked, but never cover an item.
    direct: dict = {}   # (feature_slug, item_id) -> [Marker]
    legacy_by_file: dict = {}   # file -> count of `livespec:` markers
    misfit_by_file: dict = {}   # file -> [(line, verb, item_id)]
    for marker in markers:
        if marker.legacy:
            legacy_by_file[marker.file] = legacy_by_file.get(marker.file, 0) + 1
        feature = project.feature(marker.slug)
        if feature is None:
            if "marker-unknown-feature" in enabled and not args.feature:
                report.add(
                    check="marker-unknown-feature", severity="error", spec_ref="§9.4",
                    file=marker.file, line=marker.line, feature=marker.slug,
                    message=f"marker points at feature '{marker.slug}': no features/**/{marker.slug}.md. Renamed or deleted?",
                )
            continue
        if args.feature and marker.slug != args.feature:
            continue
        for item_id in marker.ids:
            item = feature.item(item_id)
            if item is None:
                if "marker-unknown-id" in enabled:
                    report.add(
                        check="marker-unknown-id", severity="error", spec_ref="§9.4",
                        file=marker.file, line=marker.line,
                        feature=marker.slug, item=item_id,
                        message=f"marker points at {marker.slug}#{item_id}, absent from the feature file. IDs are immutable (§8.3): the item was deleted instead of cancelled, or the ID is a typo.",
                    )
                continue
            if marker.realizes:
                direct.setdefault((marker.slug, item_id), []).append(marker)
            fits = REALIZABLE if marker.realizes else REFERENCE_ONLY
            if item.type not in fits:
                misfit_by_file.setdefault(marker.file, []).append((marker.line, marker.verb, item_id))
            if item.cancelled and "marker-on-cancelled" in enabled:
                if item.type == "AS":
                    message = f"code relies on {item_id}, an assumption dropped [-]: revisit this code. {item.body[:80]}"
                else:
                    message = f"code is anchored to {item_id}, marked [-] cancelled: {item.body[:80]}"
                report.add(
                    check="marker-on-cancelled", severity="warning", spec_ref="§8.1",
                    file=marker.file, line=marker.line,
                    feature=marker.slug, item=item_id, message=message,
                )
            elif item.done and item.type in ("Q", "LIM") and "marker-on-closed" in enabled:
                # The code was written around an open question or a known
                # limitation; now that it is answered or lifted, the code may
                # carry a workaround or a guess that no longer holds.
                what = "a question now answered" if item.type == "Q" else "a limitation now lifted"
                report.add(
                    check="marker-on-closed", severity="info", spec_ref="§9.4",
                    file=marker.file, line=marker.line,
                    feature=marker.slug, item=item_id,
                    message=f"code points at {item_id}, {what}: check whether it still needs its workaround. {item.body[:80]}",
                )
            elif item.open and marker.realizes and item.type in REALIZABLE and "marker-on-open" in enabled:
                # Only markers that claim to realize the item: a see-spec marker on
                # an open item is a plain reference. An open direction means
                # "decided, not yet applied", so code realizing it disagrees with
                # the spec, as for REQ/AC.
                report.add(
                    check="marker-on-open", severity="warning", spec_ref="§8.1",
                    file=marker.file, line=marker.line,
                    feature=marker.slug, item=item_id,
                    message=f"code is anchored to {item_id}, still [ ] open: {item.body[:80]}",
                )

    if "marker-legacy-verb" in enabled:
        # One finding per file: a codebase written before the rename carries
        # hundreds of them, and the fix is one search-and-replace.
        for file, count in sorted(legacy_by_file.items()):
            report.add(
                check="marker-legacy-verb", severity="info", spec_ref="§9.4",
                file=file, line=1,
                message=f"{count} marker(s) use the legacy `livespec:` verb, still read as `implements:`. Rewrite them as `implements:` (or `see-spec:` for AS, Q, LIM).",
            )
    if "marker-verb-fit" in enabled:
        for file, misfits in sorted(misfit_by_file.items()):
            line, verb, item_id = misfits[0]
            report.add(
                check="marker-verb-fit", severity="info", spec_ref="§9.4",
                file=file, line=line,
                message=f"{len(misfits)} marker(s) pair a verb with an item type it does not fit ({verb}: ...#{item_id} first). "
                        f"They resolve anyway; writers use `implements:` for REQ, AC, UX, TECH and `see-spec:` for AS, Q, LIM.",
            )

    # ---- spec side: coverage of each anchorable item
    def covered(feature, item) -> bool:
        if (feature.slug, item.id) in direct:
            return True
        if item.type == "AC" and item.parent_id:
            # A marker on a REQ implicitly covers its nested ACs (§9.4).
            return (feature.slug, item.parent_id) in direct
        if item.type == "REQ":
            acs = [
                i for i in feature.items
                if i.type == "AC" and i.parent_id == item.id and not i.cancelled
            ]
            return bool(acs) and all((feature.slug, a.id) in direct for a in acs)
        return False

    done_total = done_covered = 0
    for feature, item in anchor_targets(project, features):
        if item.cancelled:
            continue
        is_covered = covered(feature, item)
        if item.done:
            done_total += 1
            if is_covered:
                done_covered += 1
            elif "done-unmarked" in enabled:
                report.add(
                    check="done-unmarked", severity="warning", spec_ref="§9.4",
                    file=feature.rel, line=item.line,
                    feature=feature.slug, item=item.id,
                    message=f"{item.id} is [x] but no implements: marker anchors it: {item.body[:80]}",
                )
        elif item.open and not is_covered and "open-unmarked" in enabled:
            report.add(
                check="open-unmarked", severity="info", spec_ref="§8.1",
                file=feature.rel, line=item.line,
                feature=feature.slug, item=item.id,
                message=f"{item.id} is [ ] with no code anchored to it: {item.body[:80]}",
            )

    if "feature-unmarked" in enabled:
        for feature in features:
            anchorable = [i for i in feature.items if i.type in ("REQ", "AC") and not i.cancelled]
            if not anchorable:
                continue
            if not any((feature.slug, i.id) in direct for i in anchorable):
                state = "some items are [x]" if any(i.done for i in anchorable) else "all items are [ ]"
                report.add(
                    check="feature-unmarked", severity="info", spec_ref="§9.4",
                    file=feature.rel, line=1, feature=feature.slug,
                    message=f"no implements: marker anywhere in the code for this feature ({state}).",
                )

    resolved = sum(len(v) for v in direct.values())
    report.stats = {
        "code root": str(code_root),
        "markers found": len(markers),
        "marker->item links resolved": resolved,
        "features in scope": len(features),
        "anchored [x] items": f"{done_covered}/{done_total}" if done_total else "0/0",
    }
    if not markers:
        report.notes.append(
            "no code marker (implements:, see-spec:) found in the scanned tree. Either the code is elsewhere "
            "(pass --code-root) or nothing has been anchored yet (§9.4)."
        )
    if code_root == project.root:
        report.notes.append(
            "code root equals the project root; if this repo holds specs only, "
            "point --code-root at the application repo."
        )

    return emit(report, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
