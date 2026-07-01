# 我把多个 AI Coding CLI 组织成了可闭环的小团队：Multi-CLI Orchestrator v5.0

> Multi-CLI Orchestrator 是一个本地优先的多 AI Coding CLI 协作控制平面。它不替代 Codex、Claude Code、Kimi Code、Mimo Code 或 CodeWhale，而是把这些 CLI 当成“工位”，用任务状态、门禁、证据、回放和控制台把它们组织起来。

GitHub：

https://github.com/god0618-cloud/multi-cli-orchestrator

v5.0 Release：

https://github.com/god0618-cloud/multi-cli-orchestrator/releases/tag/v5.0.0

---

## 为什么要做这个项目

过去一段时间，我同时使用多个 AI Coding CLI：Codex、Claude Code、Kimi Code、Mimo Code、DeepSeek/CodeWhale 等。

它们各有优势：

- 有的适合项目总控和长上下文推理；
- 有的适合前端实现；
- 有的适合调研和素材收集；
- 有的适合红队审查；
- 有的适合本地工程执行和验证。

但问题也很明显：当任务变复杂，协作很容易变成“我在不同窗口里复制粘贴 prompt”。

真正让我不放心的不是“能不能让 agent 干活”，而是：

- 谁现在在干什么？
- 哪个 CLI 具备自动执行能力，哪个只能手动参与？
- 失败后会不会继续往下跑？
- 额度、成本、权限、写入边界有没有被管住？
- 产物有没有证据？
- 以后能不能 replay 这次过程？
- 什么时候必须找人拍板？

所以我做了 Multi-CLI Orchestrator。

它的目标不是制造一个“无所不能的 AI 大脑”，而是把多个已经存在的 AI CLI 组织成一个可监管、可审计、可回放、可停止的小团队。

---

## v5.0 的关键变化：从“派棒”到“严格门禁自闭环”

v4.0 做到了有界多 worker dispatch wave：

```bash
mco dispatch wave <task_id> --spec wave.json --require-ready
```

也就是一次可以派发多个 worker，但每个 worker 都要经过 adapter gate。

v5.0 往前走了一步：不只是派出去，而是让任务能够在严格门禁下自己判断下一步。

新增核心命令：

```bash
mco workflow observe <task_id>
mco workflow loop <task_id> --max-steps 1
```

`observe` 会给出机器可读的下一步建议：

| 状态 | 含义 |
| --- | --- |
| `advance` | 当前阶段证据满足，可以推进 |
| `wait` | 证据不足或 worker 还没结束，等待 |
| `escalate` | 出现失败、阻塞或用户决策门，需要人工介入 |
| `complete` | 工作流已经闭环完成 |

`loop` 则是一个有硬上限的 observe/advance 循环。它不是 daemon，不会无限跑。默认思路是：每次只推进一个已经满足门禁的阶段。

---

## strict-self-closing：v5.0 的自闭环模板

v5.0 新增了一个模板：

```bash
mco orchestrate-start "Strict product task" \
  --template strict-self-closing \
  --workspace .mco-workspace
```

这个模板把复杂任务拆成四段：

```text
plan -> execute -> verify -> close
```

每一段都有明确门禁：

| 阶段 | 必要证据 |
| --- | --- |
| plan | `LOOP_SPEC.json` 存在 |
| execute | `implementation-report.md` 已登记；dispatch 全部 terminal；无 failed/blocked |
| verify | `verification-report.md` 已登记；有 verification ledger event；dashboard 存在 |
| close | `close-report.md` 已登记；无 failed/blocked |

这意味着任务不是靠 prompt 里一句“请自检通过后继续”来推进，而是靠本地文件、ledger、artifact、dispatch 状态和 gate 结果来推进。

---

## 老板视角：我能看见它为什么继续或停下

v5.0 的 dashboard 增加了 `Workflow Loop Control`。

它会显示：

- 当前 workflow；
- 当前 phase；
- 推荐动作；
- 推荐原因；
- gate 明细；
- adapter 状态；
- usage snapshot；
- dispatch gate；
- artifacts；
- timeline。

对我来说，这个变化很关键。

因为多 agent 协作最危险的不是“不够自动”，而是“自动之后看不见”。v5.0 的重点就是让自动化有边界、有解释、有证据。

---

## Adapter Matrix：哪些 CLI 能自动，哪些只能手动

v5.0 进一步显性化了 adapter 能力矩阵。

每个 CLI 都会标注：

- `execution_mode`
- `automation_posture`
- `recommended_use`
- quota 状态
- smoke gate
- promotion blockers

当前口径很保守：

| CLI | 当前姿态 |
| --- | --- |
| generic-cli | 已实现，但自动派发前仍建议 probe |
| Claude Code | 已实现 supervised non-interactive adapter |
| Kimi Code | 已实现 supervised non-interactive adapter |
| Mimo Code | manual only，不自动派发 |
| CodeWhale / DeepSeek | manual only，不自动派发 |

这不是能力不足，而是有意设计。

如果一个 CLI 的非交互式执行、quota、证据输出、sandbox、失败处理没有被证明，就不能因为“它看起来能干活”而进入自动派发链路。

---

## 它和普通 subagent 有什么区别

普通 subagent 更像是在同一个框架里拆任务。

Multi-CLI Orchestrator 更像是一个本地控制平面：

| 维度 | 普通 subagent | Multi-CLI Orchestrator |
| --- | --- | --- |
| 执行主体 | 同一框架内的子代理 | 多个真实 CLI 工位 |
| 状态 | 多在上下文里 | 写入 task workspace |
| 证据 | 常靠回答描述 | artifact / ledger / replay |
| 门禁 | prompt 约束为主 | workflow gate |
| 可视化 | 通常弱 | dashboard |
| 失败处理 | 依赖主 agent 判断 | wait / escalate / blocked evidence |

它不是为了否定 subagent，而是解决另一个问题：当你真的想让不同模型、不同 CLI、不同能力栈一起参与复杂任务时，需要一个外部的控制面。

---

## v5.0 做到什么程度了

已经完成：

- 本地任务空间：`LOOP_SPEC.json`、`RUN_LEDGER.json`、`plan.json`
- dispatch inbox
- artifact evidence
- adapter doctor / matrix / smoke
- sandbox contract
- usage snapshot
- dashboard
- replay
- bounded monitor
- dispatch wave
- workflow status / advance
- workflow observe / loop
- dynamic gates
- strict-self-closing template
- GitHub CI
- release check
- audit
- v5.0.0 GitHub Release

验证结果：

```text
41 tests OK
compileall OK
release check PASS=27 WARN=0 FAIL=0
audit PASS=101 WARN=0 FAIL=0
strict-self-closing CLI smoke -> recommended_action=complete
GitHub CI main -> success
GitHub CI v5.0.0 tag -> success
```

---

## 仍然没有做什么

v5.0 仍然不做无约束真实并发 provider execution。

原因很简单：这件事需要更强的 quota、cancel、timeout、conflict merge、rollback、credential boundary 和 cost guard。

当前版本选择先把控制面、证据面和停止条件做扎实。

我宁愿它保守一点，也不想开源一个“看起来很聪明、实际上可能乱跑”的东西。

---

## 快速体验

```bash
git clone https://github.com/god0618-cloud/multi-cli-orchestrator.git
cd multi-cli-orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -e .

mco init --workspace .mco-workspace
mco orchestrate-start "Strict product task" \
  --template strict-self-closing \
  --workspace .mco-workspace

mco workflow observe <task_id> --workspace .mco-workspace
mco dashboard <task_id> --workspace .mco-workspace
```

---

## 我希望它成为怎样的开源项目

我希望 Multi-CLI Orchestrator 能成为一个“AI Coding CLI 协作控制面”的基础项目。

不是又一个 all-in-one agent。

而是一个本地优先、证据优先、安全优先的编排层：

- CLI 继续做自己擅长的事；
- Orchestrator 负责状态、门禁、证据、审计、回放和升级；
- 人保留关键决策权；
- 自动化只在证明过的边界里运行。

如果你也同时使用多个 AI Coding CLI，或者正在思考 Agent OS、multi-agent workflow、本地知识库治理、可审计 AI 工程流程，欢迎试用、提 issue 或一起讨论。

GitHub：

https://github.com/god0618-cloud/multi-cli-orchestrator

Release：

https://github.com/god0618-cloud/multi-cli-orchestrator/releases/tag/v5.0.0
