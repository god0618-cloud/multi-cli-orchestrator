# Adapter Extension Roadmap v5.6

v5.6 prepares the project for more CLI adapters without increasing automation authority.

The important distinction:

- **manual participation** means a human can run a CLI window and register artifacts.
- **supervised execution** means MCO can dispatch bounded work to an adapter only after doctor, sandbox, smoke, and evidence gates pass.

Mimo Code and CodeWhale remain manual-only in this version.

## Current Adapter Posture

| Adapter | Current level | Intended role | Auto-dispatch |
| --- | --- | --- | --- |
| `generic-cli` | L6 for narrow safe commands | deterministic local commands | allowed only through safe command allowlists |
| `claude-code` | L6 | controller, reasoning, implementation | allowed with `--require-ready` after doctor |
| `kimi-code` | L6 | frontend and UI implementation | allowed with `--require-ready` after doctor |
| `mimo-code` | L1 | research and material collection | no |
| `codewhale` | L1 | red-team or DeepSeek-style review | no |

## Promotion Path

| Level | Gate | Required evidence |
| --- | --- | --- |
| L1 Disabled manifest | Adapter shape is documented | disabled manifest validates |
| L2 Scaffolded kit | Contract can be tested without provider access | fake fixture, sandbox draft, contract test |
| L3 Doctor-ready | Host can detect binary/auth/config safely | doctor report with no credential leakage |
| L4 Dry-run supervised | Dispatch path can be simulated | dry-run execution report |
| L5 Smoke-ready | Real CLI can be called only by explicit opt-in | smoke report with timeout, output cap, fixed sentinel |
| L6 Ready supervised | Bounded non-interactive execution is reliable | transcript, failure behavior, quota semantics, sandbox evidence |

No adapter should skip from L1 to L6.

## Mimo Code Plan

Intended use: research-ammo-worker, source collection, market material, UI references, non-authoritative synthesis.

Minimum evidence before promotion:

- CLI invocation contract for non-interactive prompt input.
- Output capture contract with timeout and max bytes.
- Task-local artifact writer that never edits stable KB directly.
- Quota semantics: known local usage command, explicit unknown state, or per-run budget stop.
- Doctor checks:
  - binary exists,
  - version can be read,
  - auth state can be checked without printing tokens,
  - configured workspace can be limited to the task directory.
- Smoke sentinel:
  - prompt requests the exact text `MCO_ADAPTER_SMOKE_OK`,
  - report records command shape, status, stdout excerpt, stderr excerpt, elapsed time, and artifact path.

Until then: use manual dispatch plus human artifact registration.

## CodeWhale Plan

Intended use: red-team review, DeepSeek-style critique, contract drift checks, risk classification.

Minimum evidence before promotion:

- Non-interactive command that can read a prompt file and write a report.
- Deterministic failure modes for missing auth, timeout, quota exhaustion, and malformed prompt.
- Sandbox that allows reading task artifacts but blocks stable KB/native memory writes.
- Doctor checks:
  - binary exists,
  - version can be read,
  - auth state can be checked safely,
  - output location can be constrained.
- Smoke sentinel with no code edits.

Until then: use manual red-team prompts and register reports as artifacts.

## Scaffold Commands

Use adapter kits to start extension work:

```bash
mco adapter scaffold mimo-code --output-dir /tmp/mco-adapters/mimo-code
cd /tmp/mco-adapters/mimo-code
python -m unittest test_mimo_code_adapter_contract.py
mco adapter validate-kit .

mco adapter scaffold codewhale --output-dir /tmp/mco-adapters/codewhale
cd /tmp/mco-adapters/codewhale
python -m unittest test_codewhale_adapter_contract.py
mco adapter validate-kit .
```

These commands prove fixture readiness only. They do not enable real provider execution.

## Maintainer Decision Gate

Adapter promotion needs a maintainer decision when any of these changes:

- real provider credentials are required,
- quota/cost exposure changes,
- workspace write scope expands,
- native CLI memory/profile files could be touched,
- stable KB write access is requested,
- browser or external network access is needed.

## Acceptance For v5.6

- Mimo Code and CodeWhale have explicit promotion plans.
- The adapter contributor path names L1 to L6 evidence gates.
- Scaffold validation can prove fixture readiness for both adapters.
- Public docs continue to say manual-only until evidence exists.
