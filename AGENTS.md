# AGENTS.md · agent 冷启动与复刻协议

> 任何 agent（Claude Code / ZCode / 其他）读到本文件即可冷启动操作本仓库；如果想**复刻同一个系统的产出过程**（研究→设计→重构→测试→汇报），走 §6 复刻协议。人类用户入口是 `README.md`。

## 1. 这个仓库是什么（30 秒）

ai-ops 是个人 AI 自进化系统的**适应度函数（子系统 A）**：把 AI 使用纠错变成可重跑案例（4 judged + 7 scripted）+ rubric 判分 + ledger 趋势，通过 `/benchmark`（周，测量+核销）与 `/evolve`（周/月，变异提案）两个命令闭环。v2 起，每笔批准的进化动作登记为实验卡（`benchmarks/experiments/`），下轮 benchmark 对分核销——进化可追责。设计全貌：`docs/superpowers/specs/2026-08-30-rsi-v2-design.md`（MMV 三递归环）。

## 2. 仓库地图

```
ai-ops/
├── AGENTS.md                        ← 本文件（agent 入口）
├── README.md                        ← 人类入口（冷启动手册）
├── benchmarks/
│   ├── cases/*.md                   ← 11 条案例（frontmatter: id/dimension/type/status[/rubric]）
│   ├── rubrics/*.md                 ← 4 张判分卡，各带 ## 校准锚
│   ├── lib/group_scores.py          ← 聚合脚本（纯标准库；聚合 + due 子命令）
│   ├── lib/install_commands.sh      ← 双宿主命令安装
│   ├── tests/test_group_scores.py   ← 全量测试（python3 直接跑）
│   ├── ledger/runs/*.jsonl          ← 每次 run 的原始分（按 case 一行 JSON）
│   ├── ledger/SCORES.md             ← 自动生成（报警/趋势Δ/校准/实验四节，勿手改）
│   └── experiments/                 ← 实验卡台账（README.md 是规范，_TEMPLATE.md 是模板）
├── pending-reviews/                 ← 纠错箱 + triage.log 决策流水
├── retrospectives/                  ← 长任务复盘卡（judged 样例源）
├── .claude/commands/{benchmark,evolve}.md   ← 协议单一事实源（Claude Code 宿主）
├── .zcode/skills/{benchmark,evolve}/SKILL.md ← ZCode 宿主镜像（指针型）
├── docs/superpowers/specs/          ← v1/v2 设计 spec
└── Clippings/                       ← 方法论剪藏（Cognition 多agent / Kimi agent db）
```

## 3. 铁律（任何操作不得违反）

1. **只判滞后产物**：judged 判分只取日期早于本周一的真实产物；判分必带 `evidence_ref`，无证据不判分。
2. **judged 上限 4 条/轮**；无合格产物记 `no-data`，不判负。
3. **judge 标签写实**：滞后自评 = `agent-selfgrade`，用户亲审 = `user`；不得把自评标成 user。
4. **用户是终局裁判**：草分、实验卡核销结论、进化动作，全部用户确认后才落盘。
5. **每条 judged 带可证伪 `prediction`**（下轮可核验的定量断言）。
6. **进化环单线程**：不做多 agent 并行进化（Cognition 原则 + 本机子代理并发=1）。
7. **采样门槛**：一次性错误不案例化；实验卡只给可验证的动作；`proposed` 卡 >3 先修剪。
8. **不手改 SCORES.md**（脚本生成物）；ledger 同日重跑整文件重写。
9. **git 纪律**：commit 前缀 `feat|spec|docs|chore|fix|refactor`（benchmark run 用 `benchmark:`）；每步一 commit；`.obsidian/` 不入库。

## 4. 两个命令怎么跑

- 说「跑 /benchmark」或「跑 /evolve」→ 按协议文件执行：`.claude/commands/benchmark.md` / `.claude/commands/evolve.md`（单一事实源；`.zcode/skills/` 是其指针镜像）。
- 聚合与核验队列：`python3 benchmarks/lib/group_scores.py`（聚合+重写 SCORES.md）；`python3 benchmarks/lib/group_scores.py due`（到期实验卡 + 上轮 prediction 清单）。
- 测试：`python3 benchmarks/tests/test_group_scores.py` → 期望 `ALL-PASS (6 tests)`。
- 宿主安装：`bash benchmarks/lib/install_commands.sh`（幂等，改协议后重跑）。

## 5. 冷启动清单（新环境 0 → 有分）

1. 适配硬编码路径：`grep -rn "Desktop/code" benchmarks/cases/`，把 `~/Desktop/code/document`（vault）等换成自己的。
2. `bash benchmarks/lib/install_commands.sh` 装双宿主命令。
3. 确认判分样例约定（每周从最近真实产物判分；没有约定会记 no-data）。
4. 跑首轮 `/benchmark` → 得基线 SCORES.md（scripted 有通过率；judged 有分或 no-data）。
5. 第一周后归纳第一条复发纠错进 `pending-reviews/`，周仪式滚动起来。

## 6. 复刻协议（复刻「这套系统的产出过程」，2026-08-30 实测可行）

本仓库 v2 由一次 agent 会话按以下七步产出，任何 agent 可在同类项目上重放：

1. **吃透现状**：读 README/spec/账本/复盘卡，列出「系统做对了什么（不许丢）」与「断点清单」（证据指向具体文件与 ledger 行）。
2. **前沿研究**：检索 RSI / 自进化 agent / AI4S 的论文与**开源实现**（推荐起点：Darwin Gödel Machine arXiv:2505.22954、AlphaEvolve arXiv:2506.13131、OpenEvolve、Absolute Zero arXiv:2505.03335、AI co-scientist（Nature 2026）、AgentEvolver arXiv:2511.10395、综述 arXiv:2507.21046、ExpeL、TextGrad），压缩成「可迁移原则 + 与本项目语境的纠偏声明」。
3. **终极思想**：把前沿原则与本项目的哲学融合成自己的架构隐喻（本项目 = MMV 三递归环 + 基因组隐喻，spec v2 §3），明确「以始为终」的 RSI 定义。
4. **理念设计**：组件变更清单 + 协议变更 + 产品逻辑（谁在哪个触点做什么、成本多少）+ YAGNI 否决项。
5. **打分门槛**：v2 vs v1 按维度打分（判据先写死再打分），**全方位 ≥ v1 才动手重构**；每维打分依据指向 spec 可查证条目，防自评膨胀。
6. **重构**：TDD（先测试后实现）；逐 task commit（分支 `refactor/rsi-v2` 模式）；实验卡 exp-001 把重构自身登记为第一张可核销实验。
7. **验证与汇报**：全量测试 + scripted 断言套跑 + 聚合产物检查；汇报测试效果与遗留风险；更新 README / AGENTS.md / 记忆。

## 7. 已知边界（诚实声明）

- cross-domain-generalization 连续 3 期 no-data：报警已挂，等 /evolve 出题或退休。
- 2026-08-29 起三份 prediction 未核验：下轮 benchmark 步骤 2 处理。
- exp-001（本次重构）status=executed，核销期限 2026-09-06，等下一轮 /benchmark 用户确认。
- v1 命令协议留在 git 历史可回溯；本文件描述以 v2 为准。
