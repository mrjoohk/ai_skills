# Reference: Mutation Runner (`scripts/mutation_runner.py`)

A mutant is one or more exact-text edits. For every mutant the runner copies the `copy` paths to a fresh temporary
directory, applies the edits there, runs the test command in that copy and records whether the tests caught it.
The working tree is never modified. Generalizes drmHWP P-041 `mutate_writer6.py` + `static_checks.py mut` (P-043).

---

## Spec — JSON

```json
{
  "copy": ["tools"],
  "test": "python -m unittest discover -s tools/doc-writer/tests",
  "timeout": 60,
  "env": {},
  "mutants": [
    {"id": "R02", "name": "reclaim off",
     "edits": [{"file": "tools/doc-writer/table_style.py", "func": "refine_lines",
                "old": "        if w[c] < need[c]:\n", "new": "        if False:\n"}]}
  ]
}
```

| Field | Meaning |
|---|---|
| `copy` | Paths (dirs or files, relative to `--root`) copied for each mutant. Must include the tests and any data they read. Normalized and de-duplicated; a path inside another listed path is dropped. |
| `test` | Command string or argv list, run in the copy's root. A leading `python`/`python3` becomes the running interpreter (`py` is left alone — the launcher takes its own arguments). |
| `timeout` | Seconds per mutant (default 60): an int or float > 0 and ≤ 1e6, as `--timeout`; bool, a string (`"30"`), NaN, Infinity or a number too large for a float → exit 2. On expiry the whole process tree is killed. |
| `env` | Extra environment variables; `{tmp}` = the copy's root. `PYTHONPATH` from the outer environment is always dropped (it would import the real, unmutated code) — set it here if the tests need it. Part of the mutant fingerprint. |
| `mutants[].id` | Unique short ID — used by `--only` and as the results key. |
| `mutants[].name` | One-line description. |
| `mutants[].test` | Optional per-mutant test command (e.g., the tests that cover this behavior). It gets its own baseline (below). |
| `edits[].file` | Path relative to `--root`; normalized (`./a/../b.py` → `b.py`, backslashes → `/`). Absolute paths and paths leaving `--root` are refused. Must be under a `copy` path. |
| `edits[].old` / `new` | Exact text and its replacement. `old` must occur exactly `count` times (default 1) in the file — or inside `func` when given. |
| `edits[].func` | Optional anchor: qualified name (`Class.method`, `outer.inner`) or a unique simple name. The search covers the def/class including its decorators. |
| `edits[].count` | Optional expected number of occurrences (all are replaced). |

Line endings do not matter: files are read with universal newlines, so `"\n"` in a pattern matches CRLF files too.
A file that is not UTF-8 gives `pattern` ("cannot read … as UTF-8").

## Spec — legacy `.py`

```python
W = "tools/doc-writer/write_doc.py"
M = [
 ("M01 re-apply off", [(W, "    if not new and clean:", "    if False:")]),
 ("F14 table width = body width", [(W, CREATE, CREATE.replace("sum(want)", 'fmt["total"]'))]),
]
M += [("N08 ...", [(W, "...", "...")])]
```

- The file is **never executed**; it is parsed as Python reads it (bytes: a BOM or a PEP 263 `coding` line, e.g. a
  cp949 file). Its top-level statements are read in order and carried out **exactly as Python would, on real
  objects**, so aliases and shared elements behave as in Python (`A = M; A.append(x)`; `S = M[:]` then
  `M[0]["test"] = ...` changes `S[0]` too):
  - values: constants, names read so far, tuple/list/dict/set displays, indexing/slicing, `+ - * / // % **`, unary
    `-`/`+`, f-strings (`!s`/`!r`/`!a`, format specs), `str.replace/strip/lstrip/rstrip/join/format/upper/lower/split`,
    `dict.get`, `len()`;
  - `T = v` (chained `MUTANTS = M = [...]`, unpacking, item targets `M[0]["edits"][0]["new"] = ...`, `T: ann = v`;
    targets are assigned left to right, as in Python: `i, M[i] = 1, x`), `T op= v` (in place on a list), `del name` (unbinds that name only), `del X[k]`, and calls on its
    lists/dicts/sets of `append extend insert pop remove clear reverse sort update setdefault popitem add discard`;
  - `import`, plain `def` (no decorator, readable defaults) bind names it does not know; docstrings, `pass` and
    `print(...)` of readable values, with `sep`/`end`/`file`/`flush` (`print(f"{len(M)} mutants", file=sys.stderr)`),
    are skipped; any other `print` follows the rule below (`print(", ".join(m[0] for m in M))` is an error).
- An item store or `del` on known data -- any name bound to a value it read, not only the spec's -- whose container
  or key cannot be read is an error (the closed side: `D = {}` then `D[os.name] = "x"` is refused too), as in Python
  (`M[0]["edit"][0]["new"] = ...` → KeyError, `M[5]["name"] = ...`); one on something unknown stops reading
  (`os.environ["X"] = "1"`, `del os.environ["X"]`).
- A value it cannot evaluate makes the assigned names unknown only when it is **inert** — it reads no name holding a
  list/dict/set and uses no `:=`, `lambda`, `yield`, `await` or reflection (`globals`, `vars`, `locals`, `exec`, `eval`,
  `compile`, `getattr`, `setattr`, `delattr`, `__import__`, `__builtins__`, `__dict__`, `sys.modules`, frames,
  `gc.get_objects` … — read, not assigned: `modules = [...]` is plain data): `ROOT = Path(sys.argv[1])`. An inert call
  statement is skipped (`print("x", file=sys.stderr)`, `sys.path.insert(0, "..")`). Everything else is a **SpecError
  naming the line**: `x = M.pop()`, `MUTANTS = [m for m in M if ...]`, `str(M)`, `M[0]["test"] = os.environ["T"]`,
  `M.append(ROOT)`, `L += os.sep` on a list, `global`, `:=`, `from x import *`, `import __main__`, or Python's own
  error (`M.remove(x)`, x missing).
- **Runtime code stops reading**: the first `if` (also `if __name__ == "__main__":` — the file is a script, it runs
  then), `for`, `while`, `with`, `try`, `match`, `class`, decorated `def`, `assert`/`raise`, use of a function defined
  in the file (`f()`, `X = f()`, `g = f`), an assignment to an attribute or item of something unknown, or a starred
  target (`a, *b = ...`, kind `starred assignment`). That statement and every later line are not read; the runner
  prints the note (also kept in the results as `meta.spec_notes`): `<file> line N: reading stops at 'for' -- lines N-L
  are runtime code: not read, and not checked except for direct changes to MUTANTS, M, COPY, TEST, TIMEOUT, ENV`.
- **The code after the stop must not change the spec directly.** Roots are the six names `MUTANTS`, `M`, `COPY`,
  `TEST`, `TIMEOUT`, `ENV` and the variables of a `for` over a root chain (`for m in M:`, then `for e in m["edits"]:`).
  A SpecError names the line for (a) a top-level assignment, `op=`, annotated assignment or `del` of a spec name, and
  (b) anywhere after the stop or in the body of any `def` of the file: an item or attribute store, `op=` or `del`
  through a root, a list/dict/set method call on one (`M.append`, `M[0].get("edits").append`, `ENV.update`,
  `list.append(M, x)`, `dict.update(ENV, ...)`) or `global` of a spec name:
  `line N: changes M after reading stopped at line S ('for') -- move it above line S or write the list out`, or for a
  def body `line N (function f, defined at line D): changes M -- it may be called after reading stopped at line S;
  move the change above line S or write the list out`. Nothing else is analysed: copies and other names are not
  followed (`A = M; A.append(x)`, `e = M[0]`, `S = M[:1]`, `cmd = TEST.split(); cmd[0] = ...`, `env = ENV.copy()`,
  `for i, m in enumerate(M)`, `for m in sorted(M)`, a parameter of a function of the file: a note only, so such a
  tail runs a different spec than the script would). `op=` on a plain name is a change for a spec name and for a `for`
  variable whose values in the read data -- the iterable read as above, the target unpacked onto every element,
  nested loops through the same values -- include a list, dict or set (`for name, edits in M: edits += [...]`); when
  the values are immutable (`name += "x"`, `for f, a, b in edits: a += "!"`) or cannot be read, it is not. A
  top-level walrus on a spec name (`(M := [])`) counts as an assignment under (a). A plain rebinding inside a block (P-041's `M = M[a:b]` under its argv check) is only named in the note:
  `... (the tail rebinds M inside a block at line 182: ignored)`. Code nested too deeply to check adds
  `(tail not checked (nested too deeply))`.
- The list is `MUTANTS` if that name was ever assigned (unknown or deleted → error, never a fall-back to `M`), else
  `M`; items are `("ID description", [(file, old, new[, func]), ...])` (the ID is the first word) or JSON-style dicts.
  Optional `COPY`, `TEST`, `TIMEOUT`, `ENV`: assigned but unknown → error, never a silent "not given". A mutant
  holding a value that is not plain data (a list containing itself) → error.
- Assumption: imported modules do not reach into the spec's globals or data (only the reflection above is refused).
- Convert to JSON: `--dump-spec FILE` (the timeouts are checked first; NaN/Infinity are never written).

---

## Baselines — the negative control of the setup

Before the mutants, **every distinct test command** (the global one and each per-mutant `test`) runs once on an
unmutated copy. It must pass and must actually run tests (`Ran 0 tests`, `no tests ran`, a bare `collected 0 items`
→ setup error, exit 2). Otherwise a broken command would make every mutant look "killed".

A passing baseline is stored in `--out` per command (saved at once), with the code fingerprint and an environment key
(interpreter, Python version, platform, host, spec `env`, copy set). It is reused only when all of them match — a
different interpreter or host runs it again. With `--budget`, a call also stops between baselines (exit 3).
Each result records whether its command's baseline passed in that call (`verified`); results made with
`--skip-baseline` stay unverified, whichever host or interpreter produced them.

## Statuses and the gate

| Status | Meaning | Gate |
|---|---|---|
| `killed` | Tests failed (exit ≠ 0); failing test names in `failing` (`load error: name` = the test module did not import) | pass |
| `timeout` | No result within `--timeout` (process tree killed) or a CPU-time limit was reached (SIGXCPU) | warn — **fail with `--strict`** |
| `survived` | Tests passed with the mutant applied | **fail** |
| `pattern` | Edit does not apply: `PATTERN xN`, func not found/ambiguous, file not found or not UTF-8, no-op | **fail** — fix the spec |
| `invalid` | A mutated `.py` file does not compile (tests not run) | **fail** — fix the mutant |
| `error` | Runner-side problem (copy failed, edited file outside `copy`), the test command ran no tests with the mutant, or the test was killed by SIGKILL from outside (out of memory, an outside limit) | **fail** — fix, then rerun with `--only` |
| *stale* (summary) | Result recorded for other code (`fp`) or another mutant definition / spec env (`mfp`) | warn — **fail with `--strict`** |
| *not run* (summary) | No result yet | warn — **fail with `--strict`** |
| *unverified* | The result was made without a passing baseline of its test command in that call (`--skip-baseline`, an older runner) | warn — **fail with `--strict`** |

Exit codes: `0` gate pass · `1` gate fail · `2` setup/usage error (bad spec, baseline fails, `--only` matched nothing,
another runner holds the results file, interrupted, unexpected error) · `3` incomplete (`--budget` reached — run the
same command again). With `--out` the gate is computed on the merged results of all mutants (or the `--only` set);
without it, on this run. When nothing is selected the runner prints "nothing to run" (exit 0, or 1 with `--strict`).

---

## CLI

| Option | Effect |
|---|---|
| `SPEC` | JSON spec, or legacy `.py` (read without executing) |
| `--root DIR` | Repository root the spec paths are relative to (default `.`) |
| `--copy PATH` | Path copied per mutant; repeatable; overrides spec `copy` |
| `--test CMD` / `--timeout S` | Override spec `test` / `timeout` (0 < S ≤ 1e6 — anything else is refused, exit 2; 1e6 s keeps cores × S within `rlim_t` and under the Windows wait limit of a DWORD of ms ≈ 4.29e6 s) |
| `--jobs N` | Mutants run in parallel — use the core count (default 1). Keep 1 for tests that drive a single-instance application (COM, Hangul) |
| `--only IDS` | Comma list of IDs, globs (`R0*,F05`) or full `"ID name"` strings; a token matching nothing is an error |
| `--changed BASE` | Only mutants whose enclosing def/class differs from BASE (a `--snapshot` dir or a git ref) — for every occurrence of the pattern; module-level edits count as changed when the file changed; a file missing in BASE counts as changed. With `--out`, mutants without any result are added |
| `--slice A:B` | Python slice over the `--only`/`--changed` selection (manual chunks); applied **before** `--resume`, so chunks cover the same list |
| `--out FILE` | Results JSON, merged across calls — a mutant's entry is replaced when it runs; written after every mutant (atomic, retried while Windows has it open). Must not be inside a `--copy` path (it would change the code fingerprint); `--summary` and later calls take the run's `test`/`copy` from it when they are not given |
| `--resume` | Skip mutants with a fresh result in `--out` (same `fp` and `mfp`). `error` results count as fresh (not retried in a loop); a `timeout` recorded under a smaller `--timeout` is retried |
| `--budget S` | Stop starting new mutants after about S seconds (0 < S ≤ 1e6); implies `--resume`; needs `--out`; exit 3 while some remain |
| `--check` | Apply every selected mutant in memory and report `pattern`/`invalid` only — no tests, seconds |
| `--list` | Index, ID, name and targets of the selected mutants (after `--only`/`--changed`/`--slice`/`--resume`) |
| `--summary` | Gate from the merged `--out` (no runs) |
| `--strict` | Gate also fails on timeout, stale, not-run and unverified |
| `--skip-baseline` | Do not run the baselines (results are then `unverified` for `--strict`) |
| `--keep` | Keep the copies of survived mutants (paths printed) for inspection |
| `--tmp DIR` | Where temporary copies go (default: system temp; not inside a `--copy` path). Copies of a call that was killed outright stay there |
| `--snapshot DIR` | Copy the `copy` paths to DIR as a later `--changed` baseline, then exit |
| `--dump-spec FILE` | Write the normalized spec as JSON, then exit |

---

## Processes

- Each test command runs in its own process group / session; on timeout the whole tree is killed
  (POSIX `killpg`, Windows `taskkill /T /F`).
- POSIX: the test command runs under a small supervisor in its group. The supervisor kills the group as soon as the
  runner (whose pid it is given, so even a runner that died before the supervisor started counts) disappears —
  killed outright by SIGKILL, or by a host ending the call — busy or blocked hangs alike — with a
  wall-clock backstop of 2 × timeout + 30 s. It also sets a CPU-time limit of cores × timeout + 60 s (below any
  outside hard limit, so SIGXCPU comes before the kernel's SIGKILL); a test can only reach it after outliving its runner.
- SIGTERM / SIGINT / SIGHUP (Windows: Ctrl+C / Ctrl+Break): running test processes are killed, results so far are
  already saved, exit 2.
- One runner per results file: a second runner on the same `--out` stops with exit 2. The lock lives in the system
  temp directory (so it covers one host — use one host per results file at a time) and is released by the OS when
  the process ends, even when it is killed.
- Windows has neither the supervisor nor the CPU limit: a runner killed outright can leave a hung test running.

## Results file (`--out`)

```json
{"meta": {"tool": "mutation_runner", "version": 2, "runner": "<sha of mutation_runner.py>", "spec": "...",
          "root": "...", "copy": ["tools"], "test": "...", "timeout": 60, "env": {}, "total": 106,
          "fp": "224b8aa1bd46", "updated": "2026-10-13T15:17:43+09:00", "spec_notes": ["<legacy stop note>"],
          "baselines": {"python -m unittest discover -s tools/doc-writer/tests":
                        {"fp": "224b8aa1bd46", "env": "<interpreter/host key>", "ok": true, "secs": 5.9, "at": "..."}},
          "runs": [{"at": "...", "selected": 106, "ran": 106, "secs": 396.5, "jobs": 2, "notes": [],
                    "runner": "...", "python": "3.10.12", "platform": "linux", "host": "...", "skip_baseline": false}]},
 "results": {"R02": {"name": "reclaim off", "status": "killed", "timeout": 60.0,
                     "failing": ["test_fit_table_refines_rows", "test_refine_lines"],
                     "detail": "killed by test_fit_table_refines_rows, test_refine_lines",
                     "secs": 7.9, "at": "...", "fp": "224b8aa1bd46", "mfp": "..."}}}
```

- `fp` = SHA-256 (12 hex) of every file under the `copy` paths, sorted by relative POSIX path, line endings
  normalized — "which code was tested" (the same on every host and for any `--copy` order).
- `mfp` = SHA-256 of the mutant's edits + test command + spec `env` — "which mutant was run".
- `runner` / `runs[]` record which runner version, interpreter and host produced the results.
- Results are kept in spec order; results of IDs no longer in the spec are dropped on the next save (a note is printed).
- Timestamps (`at`, `updated`) are local time with the UTC offset, so results merged from hosts in different time zones stay comparable.

---

## Workflow for one request (P-xxx)

1. Write the spec beside the evidence (`logs/<P>_evidence/mutants.json`); `--check`.
2. Iterate: `--changed <snapshot | git ref>` and `--only`; `--check` after every code edit.
3. Finish: one full run `--jobs <cores> --out logs/<P>_evidence/mutation.json`; on a time-limited host add `--budget`
   and repeat while exit = 3; then `--summary --strict`; cite the results file (and the strict output) in the review document.
4. Take `--snapshot` (no git) so the next request can start with `--changed`.

| Host | Settings |
|---|---|
| Remote shell, 180 s per call, background processes killed at call end | `--budget 100 --timeout 60` (budget ≈ limit − timeout − 20 s), one call at a time |
| 2-core container | `--jobs 2` |
| Tests that can hang | subprocess + timeout inside the test (fail fast), runner `--timeout` as the backstop |
| Slowest mutant close to the timeout | the runner warns when a mutant used over 60 % of `--timeout`; keep the timeout ≥ 1.5 × the slowest |

## Limits

- `--changed` compares functions; test-file changes and effects through other functions are not traced — the final full run is required.
- Each mutant copies the `copy` paths — keep them to what the tests need.
- Windows: no supervisor or CPU-time limit (only `taskkill /T` on timeout); the runner's tests were run on Linux
  (container Python 3.13, device Python 3.10). The first Windows run is `tools\deploy_skills.bat` [S0]; it checks
  the tree kill and the lock through marker files, but not the signal and orphan paths (POSIX-only tests are skipped).
- Validated in drmHWP P-043: runner tests (Linux), the runner's own mutants all killed, and the P-041 legacy spec
  (106 mutants) gave the same statuses and the same killing tests as the legacy runner — numbers in
  `review_docs/261013_1540_skill_process_improvements_applied.md`.
