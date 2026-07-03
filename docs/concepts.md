# Concepts

## CLI Workstation

A CLI workstation is an external AI coding CLI that can receive a bounded task, produce artifacts, and report completion evidence.

## Loop Spec

`LOOP_SPEC.json` defines the objective and stop rules for an orchestrated task. It prevents vague autonomous loops.

## Workflow Manifest

A workflow manifest explains when a reusable workflow should run, what evidence it needs, how it verifies completion, and when it should stop. Public templates can also declare `stack`, `evidence_level`, and token budget so one-agent workflows stay usable by default.

## Sandbox Contract

`SANDBOX_CONTRACT.json` defines write scope, read scope, port allocation, data boundary, credential policy, merge owner, and expected evidence for a worker.

## Run Ledger

`RUN_LEDGER.json` is the replayable record of a run: request, workflow, dispatches, evidence, decisions, rejected branches, and final verdict.

## Evidence Level

Evidence levels keep routine work light and audit-heavy work explicit:

- `L1`: final-state screenshot or compact evidence manifest.
- `L2`: actions log plus screenshots or state notes.
- `L3`: actions log, screenshots or recording, and final-state assertions.
