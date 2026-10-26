# Coding Agent Document Format

Use these reusable structures inside the selected output directory. User-selected source paths, destination and prose language take priority. Keep the stable task section labels when using the bundled validator.

| Document | Template | Required information |
|---|---|---|
| `overview.md` | [overview](../assets/overview_template.md) | Purpose, Integration Functions, Key Constraints, related documents and source gaps |
| `architecture.md` | [architecture](../assets/architecture_template.md) | Nonempty Mermaid dependency graph, ordering/interface notes and sources/gaps |
| `tasks/<UF_ID>.md` | [task](../assets/task_template.md) | UF title/ID, Parent IF, status, Goal, Signature, Input / Output Contract, Edge Cases, Verification |

## Contract details

- One task corresponds to one concrete UF declaration. The title starts with that UF ID and the filename is `<UF_ID>.md`. Preserve the parent's IF identifier.
- Signature and I/O retain the design's exact language, types, shape, units and ranges. Each Input/Output row needs a description, type/shape and applicable constraints. Use `None` for a deliberate absence of constraints.
- Edge cases include observable expected behavior. Verification states acceptance outcomes or links to the design's actual tests; implementation status `TODO` is a valid status and is separate from a missing acceptance criterion.
- Architecture arrows and labels come from the source design. No-dependency designs can use isolated nodes and explain that fact. Missing design information is an explicit partial draft, not an invented graph.
- Source locations and missing information remain visible. Existing progress states and user edits are preserved during a design sync. Generated links such as `architecture.md` and `tasks/` are relative to the output documents, not to the skill resources.

## Validation

Run `scripts/validate_docs.py` against generated documents, not the templates. Pass the selected `--docs-dir` and `--uf` source to check every declared UF has one nonempty task. The source parser recognizes UF-ID declarations or UF headings and ignores incidental prose references and fenced template examples.

Strict validation fails missing/empty documents, uncovered or duplicate tasks, broken IDs, unfilled template values and missing contracts. With `--allow-partial`, unresolved content is a warning and `complete=false`; missing tasks for known UF declarations still fail. Without a selected/discovered UF source, the report explicitly says coverage was not checked.
