# Concepts

## CLI Workstation

A CLI workstation is an external AI coding CLI that can receive a bounded task, produce artifacts, and report completion evidence.

## Loop Spec

`LOOP_SPEC.json` defines the objective and stop rules for an orchestrated task. It prevents vague autonomous loops.

## Sandbox Contract

`SANDBOX_CONTRACT.json` defines write scope, read scope, port allocation, data boundary, credential policy, merge owner, and expected evidence for a worker.

## Run Ledger

`RUN_LEDGER.json` is the replayable record of a run: request, workflow, dispatches, evidence, decisions, rejected branches, and final verdict.

