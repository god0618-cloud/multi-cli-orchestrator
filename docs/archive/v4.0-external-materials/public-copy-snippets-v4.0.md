# Multi-CLI Orchestrator v4.0 可复制宣传文案

## GitHub About

Local-first control plane for coordinating multiple AI coding CLIs as supervised workstations.

## 项目一句话

Multi-CLI Orchestrator 把 Codex、Claude Code、Kimi Code 等 AI Coding CLI 组织成可监管、可审计、可回放的本地协作小团队。

## 项目短介绍

Multi-CLI Orchestrator 是一个本地优先的多 CLI 协作控制平面。它不替代任何 AI Coding CLI，而是把不同 CLI 抽象成受监管的“工位”，通过 task workspace、dispatch inbox、adapter gate、sandbox contract、artifact evidence、RUN_LEDGER replay 和 boss dashboard，让复杂 AI 协作从复制粘贴 prompt 变成可追踪、可审计、可扩展的工程流程。

## v4.0 Release 摘要

v4.0.0 adds bounded multi-worker dispatch waves:

```bash
mco dispatch wave <task_id> --spec wave.json --require-ready
```

每个 wave 最多 6 个 workers。每个 worker 仍然经过 adapter readiness gate。准备好的 CLI 会收到 dispatch；未准备好的 CLI 会被阻断并留下 evidence。v4.0 暂不开放无约束真实并发执行，目标是先让多 CLI 协作变得可见、可控、可审计。

## 适合放在文章开头的 Hook

我最近一直在同时使用多个 AI Coding CLI：Codex、Claude Code、Kimi Code、Mimo、CodeWhale。它们各有长处，但真正做复杂项目时，最大的问题不是“模型够不够聪明”，而是任务状态、上下文、证据和失败记录散在不同窗口里。于是我做了 Multi-CLI Orchestrator：一个本地优先的控制平面，把这些 CLI 当作受监管的工位来组织。

## 适合放在文章结尾的 CTA

如果你也在同时使用多个 AI Coding CLI，或者也在思考“多个 AI 工具如何组成一个真实协作系统”，欢迎试试 Multi-CLI Orchestrator，也欢迎提 issue / PR。

GitHub:
https://github.com/god0618-cloud/multi-cli-orchestrator

