# Model State

Updated: YYYY-MM-DDTHH:MM:SSZ

| Role | Baseline | Current | Escalation scope | Return profile | Confirmed |
| --- | --- | --- | --- | --- | --- |
| Linx | gpt-5.6 high | gpt-5.6 high | NONE | same | yes |
| Thinx | gpt-5.6 xhigh | gpt-5.6 xhigh | NONE | gpt-5.6 xhigh | yes |
| Worker | gpt-5.6 high | gpt-5.6 high | OWNER_EXTRA_HIGH_ONLY | same | yes |

Rules:

- Linx never lowers its own profile.
- Linx routes `JUDGMENT_REQUIRED` to locked Thinx; it never answers by guess.
- Thinx Ultra is one pass only.
- Every Ultra request records RETURN_PROFILE: gpt-5.6 xhigh.
- Worker xhigh requires an explicit owner request for extra high/xhigh.
- Do not send the next normal Thinx request until return is confirmed.
- Never create a second Thinx merely for another thinking level.
- If the tool cannot confirm a profile, record MODEL_PROFILE_NOT_TOOL_ENFORCED
  and block judgment until xhigh is enforceable.
