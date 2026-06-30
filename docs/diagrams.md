# Diagrams

## Control Plane

Source asset: `docs/assets/control-plane.mmd`

```mermaid
flowchart LR
  User["Human owner"] --> MCO["Multi-CLI Orchestrator"]
  MCO --> Task["Task workspace"]
  Task --> Loop["LOOP_SPEC.json"]
  Task --> Ledger["RUN_LEDGER.json"]
  Task --> Dispatch["Dispatch queue"]
  Task --> Sandbox["SANDBOX_CONTRACT.json"]
  Dispatch --> Adapter["Adapter manifest"]
  Adapter --> Worker["CLI workstation"]
  Worker --> Evidence["Artifacts"]
  Evidence --> Ledger
  Ledger --> Replay["Run replay"]
  Ledger --> Dashboard["Boss dashboard"]
```

## Execution Gate

Source asset: `docs/assets/execution-gate.mmd`

```mermaid
flowchart TD
  Queue["Queued dispatch"] --> SandboxCheck["Sandbox contract check"]
  SandboxCheck -->|fail| Blocked["Fail closed"]
  SandboxCheck -->|pass| CommandCheck["Command allowlist check"]
  CommandCheck -->|unsafe| Rejected["Reject before claim"]
  CommandCheck -->|safe| Execute["Execute with shell=false"]
  Execute --> Report["Execution report artifact"]
  Report -->|exit 0| Complete["Dispatch complete"]
  Report -->|non-zero or timeout| Failed["Dispatch failed"]
```

## Adapter Maturity

Source asset: `docs/assets/adapter-maturity.mmd`

```mermaid
flowchart LR
  Disabled["Disabled template"] --> Doctor["Adapter doctor"]
  Doctor --> Sandbox["Sandbox contract"]
  Sandbox --> Quota["Quota preflight"]
  Quota --> Evidence["Evidence reporter"]
  Evidence --> Supervised["Supervised execution"]
```
