# Multi-CLI Orchestrator v4.0 宣传短内容

## 版本 A：小红书 / 即刻 / Twitter 长帖

我开源了一个自己最近一直在打磨的小项目：

**Multi-CLI Orchestrator**

GitHub：
https://github.com/god0618-cloud/multi-cli-orchestrator

它的目标不是再造一个“大一统 Agent”，而是把 Codex、Claude Code、Kimi Code、Mimo Code、CodeWhale 这些 AI Coding CLI 组织成一个可监管、可审计、可回放的小团队。

我为什么做它？

因为同时使用多个 AI CLI 后，真正麻烦的不是“模型够不够聪明”，而是：

- 任务状态散在多个聊天窗口里；
- 上下文靠人工复制粘贴；
- 谁做了什么很难追踪；
- 失败和阻断没有统一记录；
- 多 CLI 的记忆和成长机制容易互相污染；
- 一旦自动化，又容易无限跑、乱消耗额度。

Multi-CLI Orchestrator 的思路是：

- CLI 是工位，不是子进程；
- 任务状态放在本地 workspace；
- 每个任务有 `LOOP_SPEC.json` 和 `RUN_LEDGER.json`；
- 每次派棒都进入 dispatch；
- 每个 CLI 通过 adapter 接入；
- 新 adapter 默认 disabled；
- 未通过 readiness gate 不会自动派活；
- 所有产物进入 artifacts；
- dashboard 给老板视角；
- replay 支持事后回放。

v4.0 新增了我觉得很关键的一步：

```bash
mco dispatch wave <task_id> --spec wave.json --require-ready
```

也就是有界多 worker 派棒。

一个 wave 最多 6 个 workers，每个 worker 仍然走 adapter gate。准备好的 CLI 会收到任务，没准备好的 CLI 会被阻断并留下证据。

这不是无约束真实并发执行。

我刻意先把它做到“可监管的多工位派发”，因为我觉得多 Agent 系统真正难的不是跑起来，而是跑起来之后还能看得懂、停得住、审得清。

当前 v4.0 已经通过：

- 36 条单元测试；
- release check；
- 本地 audit；
- GitHub CI；
- public clone smoke；
- GitHub Release。

如果你也在同时使用多个 AI Coding CLI，或者也在思考“多个 AI 工具怎么组成一个真实协作系统”，欢迎试试。

GitHub：
https://github.com/god0618-cloud/multi-cli-orchestrator

---

## 版本 B：更短的发布帖

开源了一个小项目：Multi-CLI Orchestrator。

它不是新的 AI Coding CLI，而是一个本地优先的多 CLI 协作控制平面。

我想解决的问题是：当你同时使用 Codex、Claude Code、Kimi Code、Mimo、CodeWhale 等工具时，任务状态、上下文、证据、失败、额度和协作流程会散在不同窗口里。

MCO 把这些 CLI 抽象成受监管的“工位”：

- task workspace 管任务；
- dispatch 负责派棒；
- adapter matrix 判断哪个 CLI 真能干活；
- sandbox contract 定义边界；
- artifact 保存证据；
- RUN_LEDGER 支持 replay；
- dashboard 提供老板视角。

v4.0 新增：

```bash
mco dispatch wave <task_id> --spec wave.json --require-ready
```

支持有界多 worker 派棒。准备好的 CLI 进 inbox，没准备好的 CLI 被阻断并留下证据。

我没有直接做无约束并发执行，因为多 CLI 协作最重要的是先可见、可控、可审计。

GitHub：
https://github.com/god0618-cloud/multi-cli-orchestrator

---

## 版本 C：GitHub Discussion / Reddit 风格

Hi everyone, I just released v4.0.0 of Multi-CLI Orchestrator.

Repo:
https://github.com/god0618-cloud/multi-cli-orchestrator

The project is a local-first control plane for coordinating multiple AI coding CLIs as supervised workstations.

The motivation is simple: many developers already use several AI coding CLIs because each has different model access, UX, tool integrations, context behavior, and cost limits. But once a task spans multiple tools, the process quickly becomes scattered across chat windows.

MCO keeps the coordination state outside any single CLI:

- local task workspace
- `LOOP_SPEC.json`
- `RUN_LEDGER.json`
- dispatch inboxes
- adapter manifests
- sandbox contracts
- evidence artifacts
- static dashboard
- replay timeline

v4.0.0 adds bounded multi-worker dispatch waves:

```bash
mco dispatch wave <task_id> --spec wave.json --require-ready
```

A wave can queue up to six worker dispatches. Each worker still passes through the adapter readiness gate. Non-ready adapters become blocked evidence and do not receive inbox files.

This is intentionally not unconstrained concurrent provider execution. The goal is to make multi-CLI collaboration observable and auditable first, then expand execution policies carefully.

Verification for v4.0.0:

- unit tests passing
- compile check passing
- release check passing
- local audit passing
- GitHub CI passing
- public clone smoke passing

Feedback and adapter contributions are welcome.

---

## 版本 D：一句话 / 简介

Multi-CLI Orchestrator 是一个本地优先的多 AI Coding CLI 协作控制平面，把 Codex、Claude Code、Kimi Code 等 CLI 组织成可监管、可审计、可回放的“工位”，支持任务派发、adapter gate、sandbox contract、artifact evidence、dashboard、replay，以及 v4.0 的有界多 worker dispatch wave。

