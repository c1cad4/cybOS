# Repository guide for coding agents

Applies to the whole cybOS repository. Read any more specific AGENTS.md before editing a subtree.

## Purpose and sources of truth

- This repository owns the ecosystem catalog, pinned revisions, bootstrap tooling and static project map.
- Native desktop implementation belongs to c1cad4/CybOS-demo; agent HTTP API belongs to c1cad4/CybCore.
- Read ecosystem.json for component roles, test commands and dependencies; ecosystem.lock.json for exact sibling revisions.
- Read docs/ARCHITECTURE.md and docs/DEVELOPMENT.md before changing integration behavior.
- docs/VISION.md is historical vision, not evidence of implemented capabilities or current releases.

## Setup and checks

- Python 3.12+ and Git are sufficient for this repository's tooling. There is no Python dependency installation step here.
- Run from repository root: python3 -m unittest discover -s tests -v.
- Preview the catalog: python3 -m http.server 8004 --bind 127.0.0.1.
- Bootstrap siblings when required: python3 tools/bootstrap.py. This uses the network and creates sibling directories.
- Verify pinned sibling HEADs: python3 tools/bootstrap.py --verify. This is not a working-tree cleanliness check.
- Use each component's own instructions and test command for changes outside this repository.

## Change discipline

- Preserve local edits and existing checkout directories; do not reset them to satisfy a pin check.
- Keep catalog names unique, dependencies resolvable and acyclic, and sibling pins complete.
- Publish a component revision before updating its integration pin; never invent commit SHAs.
- Keep proposed dependencies and planned components distinguishable from working implementations.
- For static UI changes use safe DOM APIs for catalog text, and check search, filters, empty and error states.
- Keep setup commands reproducible and links relative for files within this repository.
- Preserve upstream attribution and license obligations when reusing third-party code.
- Keep unrelated changes in separate PRs. Do not change release workflows while polishing documentation.

## Reporting

- Explain the user-visible result, validation commands and material limitations in the PR.
- Report checks actually run, including failed or unavailable checks; do not infer success from documentation.
- Keep human-facing explanations concise; update documentation when behavior changes.
