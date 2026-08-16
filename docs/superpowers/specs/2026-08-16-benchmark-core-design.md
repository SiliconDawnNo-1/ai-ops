# 能力评测内核（Subsystem A）设计规格

- 日期：2026-08-16
- 系统：AI&Company 自进化系统 · 第一个落地子系统 = 能力评测内核
- 状态：已评审通过（用户逐节确认 A/B/C/D/E + D+ 增量）

---

## 0. 定位与约束

### 系统目标（顶层，本 spec 只实现子系统 A）
把使用 AI 的残差（纠错、成功、数据）重新投进底座，让下一次循环更快、更准、更便宜。整体方法论六支柱 → 系统角色映射见附录 A。

### 子系统 A 的定位
**全系统的适应度函数**——把"纠错→散文记忆"升级为"纠错→可重跑、可测量的能力资产"，为后续子系统（B 工作流下发 / C ROI 遥测 / D AI4S 接管）提供测量地基。没有评测标准就没有进化，只会堆积。

### 四大约束（用户拍板）
1. **ROI 第一，不共产主义**：每个组件必须过采样门槛（P[会再被用] × Δ质量 > 固定成本）。一次性任务不案例化。
2. **评分混合**：脚本级为主（零 token、可高频跑）+ 裁判级 rubric（当前 4 条：洞察链 / 诊断归因 / 长任务元复盘 / 跨领域成功范式提炼）。
3. **执行路径：轻量 git + skill/命令**，不建基础设施（否决 Python+cron 自动化、否决 MySQL 账本）。
4. **终局裁判是人**：agent 起草分数，用户审批，用户意见永远覆盖草分。

---

## 1. 系统架构与组件

```
        ┌──────────────── 周仪式 ────────────────┐
        │                                        │
  [/benchmark]──► 0)三选pending箱 ─► 1)遍历cases  │
        │    scripted: Bash断言 pass/fail        │
        │    judged: 取真实产物→对rubric打分→你审批│
        │   2)写ledger/runs/日期.jsonl           │
        │   3)重生SCORES.md趋势  ► git commit     │
        ▼                                        │
  [/evolve]──► 读趋势 ─► 修剪/升级/补漏/实验提案/  │
        │        更高价值问题(你审批)              │
        │        落回 CLAUDE.md/skills/memory     │
        └────────────────────────────────────────┘
```

### 组件表

| 组件 | 内容 | 位置 |
|---|---|---|
| cases | 每条案例 = md + frontmatter（维度/类型/门槛/来源/优先级） | `~/Desktop/code/ai-ops/benchmarks/cases/` |
| rubrics | 4 张判分卡（带锚权重） | `~/Desktop/code/ai-ops/benchmarks/rubrics/` |
| ledger | 每次运行的原始评分 jsonl + 趋势表 SCORES.md | `~/Desktop/code/ai-ops/benchmarks/ledger/` |
| pending 箱 | 纠错备选案例（周复盘三选：转正/丢弃/退回） | `~/Desktop/code/ai-ops/pending-reviews/` |
| retrospectives | 长任务复盘卡片 | `~/Desktop/code/ai-ops/retrospectives/` |
| 命令 | `/benchmark`（跑分）`/evolve`（进化） | `~/.claude/commands/`（全局可跑，仓库内 `.claude/commands/` 版本共存） |

复用既有的三条纪律做底座：**git 检查点**（每轮 commit）、**命令复用**（已有 audit-memory 先例）、**产物不落 vault**（操作系统与知识库分离）。

---

## 2. 能力域（维度）清单

| 维度 id | 覆盖的活动区 | 检查方式 |
|---|---|---|
| `reasoning-depth` | 判断 / 推理（洞察链质量） | judged（rubric: insight-chain） |
| `diagnosis-root-cause` | 排查 / 归因 | judged（rubric: diagnosis-root-cause） |
| `long-task-meta` | 长任务元复盘（D+ 增量） | judged（rubric: long-task-meta） |
| `cross-domain-generalization` | 跨领域成功范式提炼（高精尖领域的问题设定/长周期调测/归因/泛化） | judged（rubric: cross-domain-generalization）+ scripted（范式卡存在性） |
| `execution-discipline` | 执行纪律（checkpoint/拆解） | scripted |
| `validation` | 验证纪律（交付前证据） | scripted |
| `infra-health` | 底库健康（vault/memory/CLAUDE.md） | scripted |
| `retro-fit` | 复盘沉淀纪律（纠错入箱率） | scripted |

设计依据：用户活动区为"提问 / 判断 / 排查 / 复盘整理"；judged 抓最痛的主观域（判断、排查）+ 进化工序源头（长任务元复盘）+ 泛化能力（跨领域范式提炼），scripted 抓可断言的纪律域。

---

## 3. 案例 schema 规范

### frontmatter 字段

```yaml
---
id: rs-001                # 必填，形如 <dimension 前缀>-<三位序号>
dimension: reasoning-depth
title: 洞察链质量·调研输出
type: judged              # judged | scripted
status: active            # active | paused | retired
source: deep-reasoning-data-value   # 源自哪次纠错（memory id / 复盘卡 / 会话）
created: 2026-08-16
usage: 周频               # 采样门槛证据：命中频率
priority: P0              # P0 必须保 / P1 重要 / P2 锦上添花
rubric: rubrics/insight-chain.md    # 仅 judged 必填
---

## 场景
（触发该判定的任务形态，可判分样例的选取标准）

## 质量门槛
（满足即通过的定性表述）

## 判分依据
（judged：指回 rubric；scripted：指 check 断言）
```

### 脚本级案例
- `check` 字段内嵌可执行断言说明（Bash/python 均可，指向可重跑检查：git log、文件行数、lint 输出等）。
- 环境性失败标记 `skip-reason`，不计负分。

### 生命周期与采样门槛
- `active → paused → retired`。仅保留"大概率再现 + 判分能防回归 + 固定成本小于复用价值"的案例。
- 三问门槛：① 这场景还会再现吗？② 判分能拦住回归吗？③ 固定成本 vs 复用价值，值不值？

### 范式卡通道（跨领域成功范式）
从数学/物理/AI 前沿实验室、高端芯片设计、医疗、华尔街金融、奥运体育冠军训练等领域，提炼"成功问题提出 → 数据采集 → 长时间段调测 → 结果归因 → 泛化推理"的范式，形成**范式卡**（产出入 vault 知识资产，ai-ops 不新增组件）。
- 范式卡提炼质量用 `cross-domain-generalization` rubric 判分，产物同样受 `reasoning-depth`（调研）与 `long-task-meta`（长任务）管辖。
- 范式卡是 case 与方法结的**下游来源流**：反复出现、可迁移的原则 → 升级成方法（skill/memory）；可测的失败/成功样例 → 转正为 case。采样门槛照常，不许范式卡无脑堆量。

---

## 4. 评分模型

判分卡 = **带权重的数字表**（不是印象分）。每锚 0–5 分，加权求总分，设通过线。分数跨周可比 → 才能量迭代速率。

### Rubric 1 · 洞察链质量 `insight-chain.md`

| 锚 | 描述 | 权重 |
|---|---|---|
| 链数 | 非显然洞察条数（≥3 达标） | 30% |
| so-what 深度 | 平均链层数（数据→意义→后果 ≥2 层） | 25% |
| 交叉拧链 | 数据与机制是否拧成一条因果链 | 20% |
| 反事实/情景 | 有反事实推理或情景推演 | 15% |
| 口径质疑 | 对来源假设/利益偏向有推理性筛选 | 10% |

通过线：总分 ≥ 3.5/5 **且** 链数 ≥ 3。

### Rubric 2 · 诊断归因质量 `diagnosis-root-cause.md`

| 锚 | 描述 | 权重 |
|---|---|---|
| 根因 vs 表象 | 归因到机制层而非事件顺序 | 30% |
| 假设-验证 | 有显式假设 + 证据闭环 | 25% |
| 证据强度 | 关键结论有锚定证据，不空谈 | 20% |
| 停止纪律 | 不陷细节、不无限铺开，有 stopping | 15% |
| 结论可交付 | 一句话可说清 | 10% |

通过线：总分 ≥ 3.5/5。

### Rubric 3 · 长任务元复盘质量 `long-task-meta.md`（D+ 增量）

| 锚 | 描述 | 权重 |
|---|---|---|
| 归因正确性 | 根因 vs 表象，控混淆（不甩锅后端模型/effort） | 30% |
| 结构拆解正确性 | 子结论真实独立、依赖正确 | 25% |
| 最佳实践可迁移性 | 泛化方法 + 命名 + 可用条件 | 20% |
| 实验建议可测性 | 有成功标准 + 栓进哪条 case | 15% |
| 执行闭环 | 复盘卡结论是否进下一个任务真正用上 | 10% |

通过线：总分 ≥ 3.5/5。

### Rubric 4 · 跨领域成功范式提炼质量 `cross-domain-generalization.md`（D+2）

| 锚 | 描述 | 权重 |
|---|---|---|
| 问题设定提炼 | 提炼出该领域"为什么这样框定问题"的机制（而非照抄名词） | 25% |
| 长周期调测方法 | 数据采集 + 长时间段 tuning 的循环结构讲得清 | 20% |
| 归因严谨性 | 高噪声/不可复现下如何归因（金融/体育/临床样例） | 20% |
| 泛化可迁移性 | 提炼原则有可操作边界（什么条件下适用、失效），非口号 | 20% |
| 表征迁移 | 能否映射到另一领域的等价问题（对照 RL 思考） | 15% |

通过线：总分 ≥ 3.5/5。

### 运行规则
- judged 每轮默认上限 **4 条**（从 4 张卡中按周排程挑选，周轮换；本轮仅 3 张卡的 era 上限为 3），超出需用户显式扩。
- **评分必须引用产物片段**（evidence_ref），无证据不给分。
- 脚本级案例不计分，记 pass/fail/skip。

---

## 5. 数据流

每次 `/benchmark` 运行：

```
0) 三选 pending 箱（案例转正 / 丢弃 / 退回）
1) 遍历 status=active 的 cases
   - scripted：跑断言 → pass / fail / skip(+原因)
   - judged：取"最近一次真实产物"（该维度；无则金样回退）→ 按 rubric 打分 → 用户审批
2) 写 ledger/runs/YYYY-MM-DD.jsonl，
   每 case 一条 {case_id, dimension, score|pass, evidence_ref, judge}
3) 重生成 SCORES.md（按维度周粒度趋势）
→ git commit（checkpoint 纪律）
```

judged 判分样例优先级：最近真实产物 > 分维度金样。判真实产物更诚实（防金样 Goodhart），周频足够。

---

## 6. 复盘产物规范（D+ 增量）

### 触发器（长/复杂任务启发式）
满足任一：多独立子结论 / 有交付物 / 跨天。不满足不强制复盘（防这套机制自身变成无 ROI 仪式）。

### 前置结构拆解卡（2–3 行）
独立子结论 / 依赖 / 风险 / checkpoint 粒度 / 一句话预期结论。
（来源：`reasoning-driven-execution` 的"以终为始"）

### 复盘卡格式 `retrospectives/YYYY-MM-DD-<task>.md`
1. 四段：已完成 / 进行中 / 下一步 / 阻塞
2. **归因**：成败根因，控混淆（只归自身执行层，不甩锅后端模型/effort——这是本维度第 0 条真案例，源 `deep-reasoning-data-value`/`reasoning-driven-execution`）
3. **可迁移最佳实践**：泛化方法 + 命名 + 可用条件
4. **实验建议**：下一条可测假设（有成功标准，栓进具体 case）

### 自我驱动
长/复杂任务 agent 在拆解与交复盘卡时主动执行，不等用户提醒。

---

## 7. 错误处理

| 情形 | 处理 |
|---|---|
| judged 无近期真实产物且无金样 | 记 `no-data` 不判负，提示补样 |
| scripted 环境性失败（env 差异） | 记 `skip` + 原因，不判负 |
| judged 超 token 预算 | 本轮上限 4 条，超出要求用户显式扩 |
| 用户与草分分歧 | 用户审批永远覆盖 claude 草分（终局裁判是人） |
| ledger git 冲突 | 按既有 checkpoint/回滚纪律处理（commit 前先 diff） |

---

## 8. 进化回路（/evolve）

读 ledger 趋势，输出**五类**动作（全部用户审批后生效）：

1. **修剪**——维度持续低分且真实错误未减 → 退休/降级该案例，或升级对应方法（不能共产主义）
2. **升级**——绿分且复现稳定 → 把方法论沉淀进 CLAUDE.md / skill / memory（纠错→组织能力）
3. **补漏**——分数与真实体感背离 → 调 rubric / 补 case（防 Goodhart 内置审计）
4. **实验提案**——假设 · 动作 · 成功标准 · 时限，用户挑跑不跑
5. **下一个更高价值的问题**——抛给用户做方向补盲（双向变异源：agent 出变异，用户出变异，共享同一适应度函数）

### 防 Goodhart
- 分数是先行指标，真实错误率是滞后指标；`补漏`动作持续校准两者关系。
- **季度重校准**：拿两年份金样重判分，确认分数仍与用户真实体验挂钩。

---

## 9. 落地节奏与成功标准

### Build 会话 1（本 spec 通过后，一次实现）
建 repo 骨架 + 案例格式 + **从 history.jsonl 挖 10 条真案例** + 4 张 rubric（用户用过去产物校准阈值）+ `/benchmark` `/evolve` 命令 + dry-run → **基线 SCORES.md**。第一次运行即自证 ROI。

### 周仪式（~30min）
三选 pending → `/benchmark` → `/evolve` → commit

### 6 周成功标准
1. 重复纠错案例开始变少
2. 系统真的执行过修剪/升级动作
3. 用户花在"评价 agent"上的注意力下降
4. 用户能回答"我的 agent 现在哪强哪弱、分数依据是什么"

---

## 10. 已否决（范围外，YAGNI）

- 多用户 / 团队版本
- MySQL 账本 + 看板（路 3 否决）
- 全自动无人值守 judge（路 2 否决）
- 一次性任务的案例化
- 长/复杂任务之外的强制复盘（启发式门控）

---

## 附录 A：方法论六支柱 → 系统角色映射

| 支柱 | 本质 | 系统角色 |
|---|---|---|
| P1 沉底工作流+harness | 基础设施 | 运行时底座（已建 ~60%） |
| P6 信息/物质/能量 Loop + ROI | 守恒律 + 经济约束 | 演化适应度函数（本子系统实现） |
| P6 整体注意力机制 | 稀缺资源分配 | 进料漏斗（topics 打分） |
| P4 Project Topic | 选题评分器 | 注意力漏斗打分规则（后续子系统） |
| P3 Agent loop（假设→数据→归因→迭代→交付） | 执行协议 | 任务通用执行循环 |
| P5 科学家 research（定义→建模→表征→验证→模拟/实验） | 单任务质量规范 | 让迭代速率与 ROI 可度量（judged rubric 即表征） |
| P2 AI4S 接管 CEO & 销冠 | 应用方向 | 系统远期输出目标 |

## 附录 B：决策记录

| 决策点 | 选项 | 结论 |
|---|---|---|
| 锚定起始子系统 | A 评测内核 / B 工作流 / C 遥测 / D 接管 | **A**（适应度函数是地基） |
| 评分构成 | 全脚本 / 全裁判 / 单维度 / 混合 | **混合**：脚本为主 + 3 条裁判 rubric |
| 执行路径 | git+skill / Python+cron / MySQL | **git+skill**（周频仪式不建基建） |
| D+ 元复盘 | 用户补充维度 | **并入**：`long-task-meta` judged + retro 卡规范 + /evolve 五类 |
| D+2 跨领域范式提炼 | 用户补充维度 | **并入**：`cross-domain-generalization` judged + 范式卡通道 |

---

*本 spec 由 brainstorming 流程产出；下一环节 = writing-plans 制定实施计划。*