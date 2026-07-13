# Feature Manifest

| File | Purpose | Writer | Read when |
| --- | --- | --- | --- |
| TASK.md | Current route | Feature owner | Always first |
| FEATURE.json | Machine identity | Linx | Index generation |
| spec/CONTRACT.md | Acceptance | Linx/owner | Scope or proof decision |
| spec/PLAN.md | Current plan | Worker | Planning/execution |
| spec/TASKS.md | Task states | Worker | Choosing next task |
| refs/ARTIFACTS.md | Proof/artifact index | Worker | Verifying a claim |
| subfeatures/ | Independent child lifecycle | Linx | Exact child only |

Add hashes only for mechanically split source documents or immutable inputs.
