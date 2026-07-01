# Multi-CLI Orchestrator v5.0 宣传短内容

## 中文长帖

我发布了 Multi-CLI Orchestrator v5.0。

它不是新的 AI Coding CLI，而是一个本地优先的多 CLI 协作控制平面。

过去我同时使用 Codex、Claude Code、Kimi Code、Mimo Code、DeepSeek/CodeWhale 等工具。问题不是它们能不能干活，而是复杂任务里很容易变成：我在多个窗口里复制粘贴 prompt，然后靠自己记住谁干了什么、谁卡住了、产物在哪。

Multi-CLI Orchestrator 做的是另一层事情：

- 把任务状态写进 task workspace；
- 把执行过程写进 RUN_LEDGER；
- 把产物登记成 artifact；
- 用 adapter matrix 标明每个 CLI 能不能自动执行；
- 用 workflow gate 管住推进条件；
- 用 dashboard 给出老板视角；
- 用 replay 还原过程。

v5.0 的关键变化是：从“派棒”进化到“严格门禁自闭环”。

新增：

```bash
mco workflow observe <task_id>
mco workflow loop <task_id> --max-steps 1
```

系统会判断下一步是：

- `advance`：证据满足，可以推进；
- `wait`：证据不足或 worker 未结束；
- `escalate`：失败、阻塞或需要用户决策；
- `complete`：闭环完成。

新模板：

```text
strict-self-closing: plan -> execute -> verify -> close
```

它不会无限跑，也不会默认真实并发消耗 provider 额度。v5.0 仍然保持保守：只有经过 adapter gate、workflow gate、artifact evidence 和 loop cap 的动作才会推进。

GitHub:
https://github.com/god0618-cloud/multi-cli-orchestrator

Release:
https://github.com/god0618-cloud/multi-cli-orchestrator/releases/tag/v5.0.0

## 中文短帖

Multi-CLI Orchestrator v5.0 发布了。

这是一个本地优先的多 AI Coding CLI 协作控制平面，不替代 Codex / Claude Code / Kimi Code，而是把它们组织成可监管、可审计、可回放的小团队。

v5.0 新增严格门禁自闭环：

```bash
mco workflow observe <task_id>
mco workflow loop <task_id> --max-steps 1
```

缺证据就 wait，失败就 escalate，完成才 complete。

GitHub:
https://github.com/god0618-cloud/multi-cli-orchestrator

## English Post

I just released Multi-CLI Orchestrator v5.0.

It is not another AI coding CLI. It is a local-first control plane for coordinating multiple AI coding CLIs as supervised workstations.

v5.0 adds strict-gate self-closing loops:

```bash
mco workflow observe <task_id>
mco workflow loop <task_id> --max-steps 1
```

The new `strict-self-closing` workflow models:

```text
plan -> execute -> verify -> close
```

Each phase advances only after durable evidence exists. Missing evidence waits. Failed or blocked dispatches escalate. Completed workflows return `recommended_action=complete`.

GitHub:
https://github.com/god0618-cloud/multi-cli-orchestrator

Release:
https://github.com/god0618-cloud/multi-cli-orchestrator/releases/tag/v5.0.0
