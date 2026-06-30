# Why Multi-CLI Orchestration

Many teams already use several AI coding CLIs because each one has different model access, UX, tool integrations, context habits, and cost limits. A single parent agent with subagents can be convenient, but it keeps the whole team inside one runtime boundary.

Multi-CLI Orchestrator treats each CLI as a supervised workstation:

- the task state is shared
- the workflow gates are explicit
- each worker writes durable evidence
- replay records what happened
- the human sees a boss dashboard instead of scattered chat transcripts

## What This Project Is

This project is a local-first coordination layer.

It provides:

- task workspace creation
- loop specs
- dispatch queues
- sandbox contracts
- adapter manifests
- evidence artifacts
- run ledger replay
- a local dashboard seed
- safe command execution for the generic adapter

## What This Project Is Not

It is not:

- an all-powerful autonomous agent
- an arbitrary shell runner
- a replacement for model-specific CLIs
- a hidden memory writer
- a production secrets manager

## Core Bet

Agent quality improves when capability, memory, execution authority, and evidence are separated.

The CLI can be a workstation. The orchestrator can be the control plane. The human can intervene only at real decision gates.

