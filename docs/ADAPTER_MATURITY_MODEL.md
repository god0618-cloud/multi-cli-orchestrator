# Adapter Maturity Model

Adapters move through maturity levels. Do not skip levels.

## Levels

| Level | Name | Meaning | Auto-dispatch |
| --- | --- | --- | --- |
| L0 | Idea | Someone requested support for a CLI | No |
| L1 | Disabled manifest | A manifest documents desired capabilities but execution is disabled | No |
| L2 | Scaffolded kit | Fake CLI fixture, sandbox, and contract test exist | No |
| L3 | Doctor-ready | Local doctor can identify whether host CLI/auth/config are usable | No |
| L4 | Dry-run supervised | Adapter gates validate without calling a provider | No |
| L5 | Smoke-ready | Explicit opt-in smoke produces task-local evidence and fixed sentinel | No by default |
| L6 | Ready supervised | Non-interactive execution has timeout, output cap, sandbox, transcript, quota semantics, and failure reporting | Yes, only with `--require-ready` |
| L7 | Proven production workflow | Multiple dogfood workflows and real-user reports show stable behavior | Policy-dependent |

## Promotion Gates

An adapter cannot move to `READY_SUPERVISED` unless it has:

- command contract documentation,
- sandbox contract,
- doctor check,
- bounded non-interactive execution,
- timeout and output limits,
- quota or explicit unknown-quota semantics,
- task-local transcript or execution report,
- deterministic failure behavior,
- opt-in smoke command,
- tests and audit pass.

## Current v5.0 Posture

| Adapter | Level | Notes |
| --- | --- | --- |
| `generic-cli` | L6 for narrow safe commands | Not arbitrary shell execution |
| `claude-code` | L6 | Uses supervised non-interactive prompt path |
| `kimi-code` | L6 | Uses supervised non-interactive prompt path; quota remains explicit unknown |
| `mimo-code` | L1 | Manual-only until non-interactive command, evidence, and smoke gates exist |
| `codewhale` | L1 | Manual-only until non-interactive command, evidence, and smoke gates exist |

See [`adapter-extension-roadmap-v5.6.md`](adapter-extension-roadmap-v5.6.md) for the current Mimo Code and CodeWhale promotion plan.

## Rejection Reasons

Maintainers should reject or hold adapter promotion when:

- the CLI only works interactively,
- quota/cost behavior is unknown and unbounded,
- output cannot be captured reliably,
- prompt files or reports leave the task workspace,
- native memory/profile files are modified silently,
- smoke tests require credentials in CI,
- failure behavior cannot be observed.
