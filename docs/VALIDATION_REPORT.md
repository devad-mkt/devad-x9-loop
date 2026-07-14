# Validation Report - 2026-07-14

| Gate | Result |
| --- | --- |
| Full unittest discovery | PASS, 151 tests in 109.814 seconds |
| Retained v3/v5 behavior | PASS inside the same 151-test run |
| Official skill validator | PASS, 6/6 skills |
| Python AST | PASS, 41 active Python files |
| PowerShell AST | PASS, 5 active scripts |
| Package validator | PASS, manifest, registry, compact template, JSON, and links |
| Source manifest | PASS, 231 public files before C1 |
| Secret scan | PASS, 232 text files and 0 findings |
| Public privacy tests | PASS, 6/6; no personal paths or private backup remote |
| Private evidence exclusion | PASS; no archives, commit evidence, security evidence, or local benchmark results |
| Temporary installation | PASS, exact hashes for all 6 skills |
| Git whitespace check | PASS |
| Generated cache check | PASS; no cache remains in the package |
| OpenCode sidecars | Advisory and nonblocking; unavailable models produce `TOOL_UNAVAILABLE` without retry loops |

`loop.db` is disposable. `SNAPSHOT.json`, Worker receipts, and current Git are the recovery inputs. Markdown status and handoff files are generated human views only.

No product code, deployment, provider request, or model-sidecar execution is part of this package release.
