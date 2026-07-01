# Multi-CLI Orchestrator v5.0 可复制宣传文案

## 一句话

Multi-CLI Orchestrator v5.0 是一个本地优先的多 AI Coding CLI 协作控制平面，把 Codex、Claude Code、Kimi Code、Mimo Code、CodeWhale 等 CLI 组织成可监管、可审计、可回放、可停止的小团队。

## 短摘要

我发布了 Multi-CLI Orchestrator v5.0。它不是新的 AI Coding CLI，而是一个本地控制平面：把多个 CLI 当成“工位”，用 workflow gate、artifact evidence、run ledger、adapter matrix 和 dashboard 管住复杂任务协作。

v5.0 新增 `mco workflow observe` 和 `mco workflow loop`，支持严格门禁下的 `plan -> execute -> verify -> close` 自闭环。它不会无限跑：缺证据就 wait，失败或需要用户决策就 escalate，完成才 complete。

## Release 摘要

v5.0.0 adds strict-gate self-closing loops:

```bash
mco workflow observe <task_id>
mco workflow loop <task_id> --max-steps 1
```

The new `strict-self-closing` template models:

```text
plan -> execute -> verify -> close
```

Each phase advances only after durable evidence exists. Missing evidence waits. Failed or blocked dispatches escalate. Completed workflows return `recommended_action=complete`.

## 适合发群的一段

分享一个我最近开源的小项目：Multi-CLI Orchestrator v5.0。它不是新的 AI Coding CLI，而是一个本地优先的多 CLI 协作控制平面，用来把 Codex、Claude Code、Kimi Code 等工具组织成可监管、可审计、可回放的“工位”。v5.0 已经支持严格门禁下的自闭环工作流：系统会判断下一步是继续、等待、升级还是完成，不会无限跑。项目已发布到 GitHub，并通过 CI、release check、audit 和 strict-self-closing smoke。

## Links

- GitHub: https://github.com/god0618-cloud/multi-cli-orchestrator
- Release: https://github.com/god0618-cloud/multi-cli-orchestrator/releases/tag/v5.0.0
