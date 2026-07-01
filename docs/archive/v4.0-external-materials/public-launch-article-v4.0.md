# 我把多个 AI Coding CLI 组织成了一个可审计的小团队：Multi-CLI Orchestrator v4.0

过去一段时间，我同时在用很多 AI Coding CLI：Codex、Claude Code、Kimi Code、Mimo Code、CodeWhale、DeepSeek 相关 CLI……

它们各有长处。

有的更适合做架构判断，有的前端审美更好，有的适合搜集资料，有的适合做红队审查，有的在本地工程执行上更稳。

但真正做复杂项目时，我发现最大的麻烦不是“哪个模型更聪明”，而是：

- 任务状态散在多个聊天窗口里；
- 上下文靠我人工复制粘贴；
- 谁做了什么、做到哪一步、失败在哪里，很难回放；
- 每个 CLI 都有自己的记忆和成长机制，但多 CLI 组合起来之后，生态并不一定健康；
- 一旦想自动化，又很容易滑向“无限跑”“假装什么都能做”“不清楚谁在消耗额度”。

所以我做了一个开源项目：

**Multi-CLI Orchestrator**

GitHub：

https://github.com/god0618-cloud/multi-cli-orchestrator

它的目标不是再造一个“大一统 Agent”，而是做一个本地优先的多 CLI 协作控制平面，把不同 AI Coding CLI 组织成一个可监管、可审计、可回放的小团队。

---

## 一句话介绍

**Multi-CLI Orchestrator 把 Codex、Claude Code、Kimi Code 等 AI Coding CLI 抽象成受监管的“工位”：任务可以被拆分、派发、执行、审计、回放，而不是散落在多个聊天窗口里。**

它不是一个替代 Claude Code / Codex / Kimi Code 的工具。

相反，它承认这些 CLI 本身都有价值：

- 它们有不同模型；
- 有不同工具链；
- 有不同认证体系；
- 有不同上下文习惯；
- 也有不同额度和执行边界。

Multi-CLI Orchestrator 要做的是把它们组织起来。

我更愿意把它理解成一个 **Local-first Agent OS**：

- CLI 是工位；
- 任务目录是共享工作台；
- adapter 是接入规范；
- sandbox 是安全边界；
- dispatch 是派棒；
- artifact 是证据；
- ledger 是运行账本；
- dashboard 是老板视角；
- replay 是事后复盘。

---

## 为什么我不满足于“一个 CLI 里开 subagent”

现在很多工具都支持 subagent，这当然有用。

但 subagent 通常仍然在同一个 CLI、同一个模型供应商、同一个运行时边界里。它更像“同一个办公室里的多个分身”。

而我想要的是另一种结构：

> 让不同 CLI、不同模型、不同工具生态，作为真正独立的工位参与复杂任务。

比如一个真实产品迭代里，我可能会这样分工：

- Claude Code：负责 PRD、架构、任务拆解；
- Codex：负责后端实现、验证、审计、发布门禁；
- Kimi Code：负责前端页面精修；
- Mimo Code：负责搜集竞品、社区资料和素材弹药；
- DeepSeek / CodeWhale：负责红队审查和风险扫描。

如果这些工作全靠我在多个窗口之间复制粘贴 prompt，就很快会失控。

问题不是“能不能让它们干活”，而是：

- 谁派发任务？
- 谁知道当前状态？
- 谁判断某个 CLI 是否真的具备自动执行能力？
- 谁记录失败原因？
- 谁防止一个未准备好的 CLI 被误派？
- 谁保证产物可以审计？
- 谁决定哪些经验可以进入长期知识库？

这就是 Multi-CLI Orchestrator 要解决的问题。

---

## 核心设计：先控制平面，再自动化

我没有一上来做“全自动多 Agent 并发执行”。

因为这听起来很酷，但如果没有治理，很容易变成不可审计的黑箱。

Multi-CLI Orchestrator 的设计顺序是反过来的：

1. 先把任务状态从聊天窗口里抽出来；
2. 再把执行过程写进本地账本；
3. 再把每个 CLI 的能力声明清楚；
4. 再给每个工位加 sandbox 和 readiness gate；
5. 再允许派棒；
6. 最后才考虑更自动化的执行。

它默认保守：

- 不默认写稳定知识库；
- 不默认改 CLI 原生 memory / profile；
- 不默认任意 shell 执行；
- 新 adapter 默认 disabled；
- 未通过 readiness gate 的 CLI 不会收到任务；
- smoke test 必须显式 opt-in；
- 多 worker wave 有上限；
- 真实 provider 执行仍然有边界。

这套设计的目标不是让 AI “更疯”，而是让 AI 协作更可靠。

---

## v4.0 已经能做什么

当前版本是 `v4.0.0`。

这是一个可以公开 clone、运行、演示和二次开发的开源 MVP。

### 1. 创建本地任务工作区

```bash
mco init --workspace .mco-workspace
mco doctor --workspace .mco-workspace
```

每个任务都有自己的目录结构：

```text
task.json
LOOP_SPEC.json
RUN_LEDGER.json
dispatch/
artifacts/
dashboard.html
```

这意味着任务状态不再只存在聊天窗口里。

### 2. 创建任务

```bash
mco task create "Build a mobile-first project page" --workspace .mco-workspace
```

任务会生成独立的 task workspace，后续所有 dispatch、artifact、replay 都围绕这个任务展开。

### 3. 查看 CLI 工位是否准备好

```bash
mco adapter matrix --doctor --output adapter-matrix.json --html adapter-matrix.html
```

这个命令会生成一个 adapter matrix，回答几个关键问题：

- 这个 CLI 是否已经实现 adapter？
- 是否支持非交互式执行？
- 是否有 sandbox contract？
- 是否可以读写任务 inbox / artifacts？
- quota 语义是否明确？
- 是否通过 smoke gate？

这一步很重要。

因为我不想让系统假装“所有 CLI 都能自动执行”。

如果某个 CLI 还没准备好，它就应该明确显示为 disabled / blocked，而不是被悄悄派活。

### 4. 单 worker 派棒

```bash
mco dispatch queue <task_id> \
  --agent kimi-code \
  --title "Frontend pass" \
  --instructions "Polish mobile UI" \
  --require-ready \
  --workspace .mco-workspace
```

如果 `kimi-code` 没有达到 `READY_SUPERVISED`，这条 dispatch 不会进入它的 inbox，而是会被记录为 blocked evidence。

### 5. v4.0 新增：多 worker dispatch wave

v4.0 的核心新增能力是：

```bash
mco dispatch wave <task_id> --spec wave.json --require-ready --workspace .mco-workspace
```

`wave.json` 示例：

```json
{
  "title": "Sprint review wave",
  "workers": [
    {
      "agent": "generic-cli",
      "title": "API drift review",
      "instructions": "Check API contract drift and report evidence."
    },
    {
      "agent": "kimi-code",
      "title": "Frontend polish review",
      "instructions": "Review mobile UI fit and report findings."
    }
  ]
}
```

这就是“多 CLI 协作”的关键一步：

- 一次派发多个 worker；
- 每个 worker 都有明确任务；
- 最多 6 个 worker，避免失控；
- 每个 worker 仍然经过 adapter gate；
- 未准备好的 worker 会被阻断；
- 阻断原因会写入证据；
- wave manifest 会写入 `dispatch/waves/`；
- 后续可以 audit 和 replay。

注意，这不是无约束真实并发执行。

我刻意把 v4.0 收在“有监督多工位派棒”这一层。

因为我认为多 Agent / 多 CLI 系统真正难的不是“并发跑起来”，而是“跑起来之后还能看得懂、停得住、审得清”。

### 6. Dashboard：老板视角

```bash
mco dashboard <task_id> --workspace .mco-workspace
```

Dashboard 会展示：

- 当前任务状态；
- dispatch 状态；
- adapter readiness；
- usage snapshot；
- artifact 列表；
- timeline；
- blocked / failed escalation。

也就是说，你不需要翻一堆聊天窗口，就能知道这轮协作发生了什么。

### 7. Replay：事后回放

```bash
mco run replay <path-to-RUN_LEDGER.json>
mco run replay <path-to-RUN_LEDGER.json> --html replay.html
```

这是我很看重的能力。

因为复杂任务结束后，真正有价值的不只是最终代码，还有过程：

- 哪一步做了什么？
- 哪个 CLI 接了哪一棒？
- 哪个门禁阻断了？
- 哪个 artifact 证明任务完成？
- 哪些经验可以沉淀？

Replay 让这些东西变成可回看的事实，而不是模糊记忆。

---

## 这个项目和普通自动化脚本有什么区别

普通脚本解决的是“把命令跑起来”。

Multi-CLI Orchestrator 解决的是“把多个 AI CLI 组织成可治理的协作系统”。

它关心的是：

| 问题 | MCO 的回答 |
| --- | --- |
| 任务状态在哪里？ | task workspace |
| 过程怎么记录？ | RUN_LEDGER.json |
| 产物怎么沉淀？ | artifacts |
| 谁可以被派活？ | adapter matrix + readiness gate |
| 未准备好的 CLI 怎么处理？ | blocked dispatch evidence |
| 多 worker 怎么控制？ | dispatch wave，最多 6 个 worker |
| 用户怎么看状态？ | dashboard |
| 事后怎么复盘？ | replay |
| 新 CLI 怎么接入？ | disabled-by-default adapter kit |

这也是为什么我把它叫做 Orchestrator，而不是 Runner。

---

## 新 CLI 接入：默认禁用，证据晋升

项目提供 adapter scaffold：

```bash
mco adapter scaffold kimi-code --output-dir adapter-kits/kimi-code
mco adapter validate-kit adapter-kits/kimi-code
```

新 adapter 不会一创建就可执行。

它必须先提供：

- manifest；
- sandbox contract；
- fake CLI fixture；
- contract test；
- README；
- smoke checklist。

然后通过：

```bash
mco adapter validate-kit adapter-kits/kimi-code
```

这套流程是为了避免开源项目里最常见的问题：

> 文档里写“支持 XXX”，但其实只是占了个坑。

在 Multi-CLI Orchestrator 里，默认态是诚实的：

- 没实现就是 disabled；
- 没证据就是 unknown；
- 没 readiness 就不能自动派发。

---

## 当前支持情况

| 能力 | 状态 |
| --- | --- |
| 本地 workspace | 已实现 |
| task / ledger / artifact | 已实现 |
| dashboard | 已实现，静态 HTML |
| replay | 已实现，文本 / JSON / HTML |
| adapter matrix | 已实现 |
| generic-cli safe command | 已实现，严格 allowlist |
| Claude Code adapter | 已实现，受限执行 |
| Kimi Code adapter | 已实现，受限执行 |
| adapter contributor kit | 已实现 |
| dispatch wave | v4.0 已实现 |
| Mimo / CodeWhale | 模板或待接入，不默认启用 |
| 真实并发 provider 执行 | 尚未开放 |
| Web 控制台 | 当前是静态 dashboard，不是 SaaS |

---

## v4.0 发布前的验证

这不是只写了 README 的项目。

v4.0 发布前已经做过：

- 本地单元测试：36 tests PASS；
- Python compileall：PASS；
- release check：PASS=27 WARN=0 FAIL=0；
- 本地 audit：PASS=92 WARN=0 FAIL=0；
- GitHub CI：PASS；
- public clone smoke：PASS；
- GitHub Release：`v4.0.0`。

Release 地址：

https://github.com/god0618-cloud/multi-cli-orchestrator/releases/tag/v4.0.0

---

## 后续我想继续做什么

我希望它最终能变成一个真正好用的开源 Multi-CLI Agent OS。

后续路线大概是：

### v4.1：Wave execution policy

从“有界派棒”进一步走向“有界执行”，加入：

- quota gate；
- timeout gate；
- cancel gate；
- execution policy；
- worker failure handling。

### v4.2：更好的 Replay / Dashboard

现在 dashboard 是静态页面，够演示，但还不够好用。

后续希望能做：

- dispatch drill-down；
- wave timeline；
- artifact preview；
- blocker queue；
- usage / quota 可视化。

### v4.3：Adapter marketplace seed

让更多 CLI 可以被社区贡献进来，但仍保持 disabled-by-default 和 validate-kit。

### v4.4：Workflow template library

沉淀常见流程模板：

- 前端评审；
- 后端实现；
- 红队审查；
- 开源发布；
- 深度研究；
- 产品 Sprint。

### v5.0：更完整的多 CLI 自闭环

在严格门禁下，支持更完整的：

- 自动分工；
- 执行；
- 回收；
- 审计；
- 复盘；
- 经验沉淀。

---

## 我最想强调的一点

Multi-CLI Orchestrator 不是为了证明“AI 可以全自动替你工作”。

我更关心的是另一个方向：

> 当我们真的开始让多个 AI 工具参与复杂任务时，怎样让它们变得可组织、可监管、可回放、可持续升级？

这件事比“多跑几个 agent”更底层。

因为一旦你同时使用多个 AI CLI，就会自然遇到这些问题：

- 能力怎么描述？
- 边界怎么定义？
- 任务怎么派发？
- 状态怎么同步？
- 失败怎么处理？
- 证据怎么留下？
- 经验怎么沉淀？
- 用户什么时候需要拍板？

Multi-CLI Orchestrator 是我对这些问题的一个开源回答。

它还早，但已经不是玩具形态。

它已经可以被 clone、运行、测试、审计、发布，也已经有 v4.0 的多 worker dispatch wave。

如果你也在同时使用多个 AI Coding CLI，或者你也在思考“多个 AI 工具如何组成一个真实协作系统”，欢迎试试这个项目，也欢迎提 issue / PR。

GitHub：

https://github.com/god0618-cloud/multi-cli-orchestrator

---

## 附：最小体验命令

```bash
git clone https://github.com/god0618-cloud/multi-cli-orchestrator.git
cd multi-cli-orchestrator

python -m venv .venv
source .venv/bin/activate
pip install -e .

mco init --workspace .mco-workspace
mco doctor --workspace .mco-workspace
mco demo walkthrough --workspace .mco-walkthrough --output-dir .mco-walkthrough-output
```

如果想体验 v4.0 的 dispatch wave：

```bash
mco task create "Demo multi-worker wave" --json --workspace .mco-workspace
mco dispatch wave <task_id> --spec wave.json --require-ready --workspace .mco-workspace
```

这一步你会看到：准备好的工位会进入队列，没准备好的工位会被阻断并留下证据。

这正是这个项目的核心精神：

**让多 CLI 协作先变得诚实、可见、可审计，再谈更强的自动化。**

