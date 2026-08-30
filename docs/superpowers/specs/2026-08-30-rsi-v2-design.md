# ai-ops v2 · 测量驱动递归自改进（RSI）设计规格

- 日期：2026-08-30
- 前序：`2026-08-16-benchmark-core-design.md`（v1，全部实体内容保留，本 spec 只做增量与升级）
- 状态：研究 → 终极思想 → v2 设计 → 打分门槛 → 重构实施，一次会话闭环产出
- 方法论：以始为终——先回答「RSI 在个人系统里到底指什么」，再倒推每个组件该不该存在

---

## 0. TL;DR

v1 把「纠错」变成了「可测量的能力资产」，这是适应度函数的正确起点；但它**测量了 agent，却没测量自己**——进化决策（/evolve）开出决策单后没有实验级的闭环验证，判分器（judge）自身的漂移无人测量，题库静态（cross-domain 连续 3 期 no-data 而系统无动于衷），且宿主迁移到 ZCode 后 `/benchmark` `/evolve` 两个命令实际已失效（本次会话已验证）。

v2 吸收 2023–2026 前沿 RSI 研究（DGM、AlphaEvolve、Absolute Zero、AI co-scientist、AgentEvolver 等 11 个来源）的五条可迁移原则，提出**「测量–修改–验证」（MMV）三递归环**：

- **L1 任务环**：agent 干真实活（产出即判分样例）；
- **L2 进化环**：/benchmark 测量 → /evolve 提变异 → 你审批 → 落进基因组 → **每笔批准动作登记为实验卡（含假设/成功标准/期限）** → 下轮 /benchmark 自动核销——决策单变成实验，实验变成基因谱系；
- **L3 元进化环**：适应度函数自己也被测量（预测命中率、判分稳定性、人机分歧率），进化策略本身按实验命中率修正——**谁来看住看门人：用测量看**。

打分结论（§5）：8 个维度 v2 全部 ≥ v1，其中 4 个维度显著领先（闭环度、环境适配、前沿接轨、可校准性），ROI 维度持平略升（脚本接管手工核验，周仪式反而变短）。**触发重构。**

---

## 1. 起点：v1 系统审计

### 1.1 v1 做对了什么（不许丢的东西）

1. **把适应度函数变成了资产**：10 案例（4 judged + 6 scripted）+ 4 rubric + ledger/SCORES.md，判分可重跑、分数跨周可比——这正是 AlphaEvolve/DGM 的核心组件（automated evaluator）的个人版。
2. **防 Goodhart 写成硬规则**：judged 上限 4 条/轮、evidence_ref 强制、只判滞后产物、可证伪 prediction、judge 实话标签——与 DGM 论文里 agent 伪造基准分的真实事故（见 §2.1）对得上，v1 用规则提前防住了。
3. **采样门槛挡住了资产堆积**：转正三问（会再现？防回归？成本 < 复用价值？）对应前沿的 sample-efficiency 思想（ShinkaEvolve/OpenEvolve 的样本效率关切）。

### 1.2 六个断点（v2 全部要修）

| # | 断点 | 证据 | 前沿对照 |
|---|---|---|---|
| D1 | **进化不闭环**：/evolve 决策单批准后，动作是否真让分数动了，无人核销；"执行闭环"只存在于 lm-001 rubric 的 10% 权重锚里 | evolve.md 五类动作无状态跟踪 | DGM：每次自修改都要过基准验证才进 archive；不达标的修改被丢弃 |
| D2 | **判分器自身不被测量**：prediction 核验手写在 triage.log（现状只有 1 行），命中率永不聚合；agent-selfgrade vs user 的分歧无人看 | triage.log 仅 2 行；SCORES.md 无校准指标 | AI co-scientist 用 Elo 锦标赛给主观评分上校准；TextGrad 把"反馈质量"当作被优化的组件 |
| D3 | **回归是被动曝光**：ex-001 在 08-18 run fail 后，只靠下一周人眼看分数 | ledger 08-18 有 fail 记录，无后续自动动作 | OpenEvolve：cascade evaluation + artifact 回流，坏结果立刻反哺下一轮 |
| D4 | **题库静态、无自出题**：cg-001 连续 3 期 no-data，系统规则上只是"提示补样"，无强制出题机制 | SCORES.md + 3 期 ledger | Absolute Zero：自提任务 + learnability 奖励 → 自动课程；AgentEvolver：self-questioning |
| D5 | **进化元知识无处沉淀**：五类动作哪类有效、哪类失败，从无台账——进化策略本身不进化 | 无任何文件记录动作效果 | DGM archive 的父子谱系；实验驱动的自进化 agent（ICLR 2026）把经验结构化 |
| D6 | **宿主迁移断档**：命令躺在 `~/.claude/commands/`，ZCode 不读取（本会话可用技能列表实测无 benchmark/evolve） | 本会话实测 | Kimi/TiDB 剪藏：agent 基础设施要"最小摩擦"——仪式入口断了，一切归零 |

---

## 2. 前沿研究沉淀（论文阅读交付物）

### 2.1 来源图谱（2023-08 → 2026-08，按对 v2 的贡献排序）

| 来源 | 年份 | 核心机制 | 给 v2 的移植 |
|---|---|---|---|
| **Darwin Gödel Machine**（Sakana AI + UBC，arXiv:2505.22954，ICLR 2026 poster；开源 jennyzzt/dgm） | 2025-05 | agent 重写自身代码（工具/提示词/工作流，底座模型冻结），每笔修改在 SWE-bench/Polyglot 上**经验验证**后才进 archive；archive 是进化树，可从任意历史版本分叉出新路径 | 经验验证取代形式证明（Darwinian）；**实验卡 = 个人版 archive 条目**；冻结底座 → 只进化 harness（正是个人系统的处境） |
| **AlphaEvolve**（DeepMind，arXiv:2506.13131） | 2025-06 | 三件套：prompt sampler + **进化数据库**（MAP-Elites 式）+ **自动评估器**；成功程序成为下一代的构件 | 评估器先行（v1 已有）；**最好基因不丢**（/evolve 升级动作必须先落卡再动手） |
| **OpenEvolve**（开源 AlphaEvolve，7k+ stars） | 2025 | islands 防早熟收敛；**cascade 评估**（先便宜后贵）；**artifact 回流**（错误喂回下一代）；double selection；prompt 本身可进化 | 回归/错误必须**立刻回流**（修 D3）；人工判分前先跑 scripted 筛（已是现状，保留） |
| **Absolute Zero**（清华 LeapLab，arXiv:2505.03335，NeurIPS 2025） | 2025-05 | 自提任务 + learnability 奖励 + 代码执行器验证 → **自动课程**，零外部数据 | **自出题通道**：no-data ≥3 期的维度，/evolve 必须二选一——出样任务或退休案例（修 D4） |
| **AI co-scientist**（DeepMind，Nature 2026） | 2026-05 | generate→debate→**Elo 锦标赛**→rank→evolve 的假设进化环 | 主观判分的校准靠**成对比较思想**（rubric 锚样例 + 复判探针，不引入重型锦标赛，见 §2.4 纠偏） |
| **AgentEvolver**（阿里 ModelScope，arXiv:2511.10395，开源） | 2025-11 | self-questioning（从轨迹自提任务）+ self-navigating（经验导航探索）+ **self-attributing**（细粒度归因/学分分配） | 实验卡就是个人版 self-attributing：动作→结果逐条记账（修 D1/D5） |
| **Textual Backprop for multi-agent**（ACL 2026 Findings） | 2026 | 用文本反馈迭代精化全局+局部协作 | /evolve 的决策单 = 文本梯度：分数落差就是 loss，动作就是反传 |
| **ExpeL**（arXiv:2308.10144，994+ 引用） | 2023 | 经验采集→**洞察抽取**→洞察应用；成败轨迹都提炼成可迁移 insight | 复盘卡→pending→case 的管线照旧；实验卡的 result 字段 = 洞察抽取的落点 |
| **TextGrad**（arXiv:2406.07496，Stanford） | 2024 | 把 LLM 批评当作"文本梯度"反向传播优化组件 | 判分器/命令/协议本身也是可被反馈优化的组件（L3） |
| **自进化 agent 综述**（arXiv:2507.21046） | 2025-07 | 分类学：**what**（Model/Memory/Tools/Workflow）× **when**（推理内/跨生命周期）× **how**（反馈源/优化法） | v2 的可进化面明确为：memory（CLAUDE.md/skill）+ workflow（命令/协议）+ tools（脚本/rubric/case）——模型不进化（冻结底座，同 DGM） |
| **AI Scientist-v2**（Sakana，arXiv:2504.08066；Nature 2026）+ self-driving labs | 2025–2026 | 假设→实验→分析全环自动；实验失败自主纠偏重写 | 「实验失败→回流重写」的循环结构（不追求其自动化程度，见纠偏声明） |

工程侧两篇剪藏（已入库 Clippings/）：**Cognition《Don't Build Multi-Agents》**——共享上下文、行动携带隐含决策、单线程线性 agent 最可靠；**Kimi/TiDB agent database**——agent 基础设施三原则：最小摩擦、统一技术栈、极致低成本。→ v2 约束：**进化环单线程**（与 ZCode 子代理并发=1 的本机现实一致）、入口命令化、纯标准库零依赖。

### 2.2 五条可迁移核心原则（v2 的思想地基）

- **P1 经验验证取代形式证明**：Schmidhuber 的 Gödel Machine 只做可证明有益的自修改（不可实现）；DGM 改成「改完跑分，涨了才留」。→ 个人版：每笔进化动作过一次实验核销，不靠感觉断言有效。
- **P2 archive + 谱系**：不是单链贪心，而是可分叉的 archive；好基因永不删除。→ 实验卡记录 parent（哪个分数/痛点触发）与 child（改了哪个基因组文件），git 本身就是版本库。
- **P3 测量必须回流**：评估不是终点，误差要喂回下一轮。→ SCORES.md 报警 → pending 箱 / 实验卡，脚本自动搬，不靠人眼。
- **P4 自出题课程**：系统缺样就该自己造样（AZR 的 learnability）。→ no-data 连续 ≥3 期 = 硬触发，强制二选一。
- **P5 元层同样被测量**：judge 是组件不是神谕；评估器的校准状态要可见。→ 预测命中率、判分稳定性、人机分歧率进 SCORES.md。

### 2.3 纠偏声明（与前沿语义的刻意分歧）

1. **不追求全自动闭环**。DGM/AI Scientist-v2 是全自动 RSI；本系统**用户是终局裁判**（v1 四大约束之一，继续有效）。这不是能力不足，是个人系统的安全与 ROI 设计：变异合不合法由人拍板，但**核销由脚本代劳**——把人只放在「批准」与「裁决」两个真需要人的位置上。对应 self-driving labs 领域 2026 年仍在辩论的 human-in-the-loop 平衡，本系统站在 scientist-in-the-loop 一侧。
2. **不引入 Elo 锦标赛**。co-scientist 的 pairwise debate 在单判分者场景退化为自博弈，校准收益低、token 成本高；v2 用更便宜的「复判探针 + 锚样例」替代（见 §4.3）。
3. **不建 islands/种群**。个人系统一周只有一轮真实产物，样本量撑不起质量多样性搜索；用「案例库多样性 + 周轮换判分」近似，不造空转组件。

---

## 3. 终极思想：MMV 三递归环

### 3.1 RSI 在个人系统里的定义（以始为终）

RSI ≠ agent 改自己权重。个人系统里，可进化的只有 harness（综述的 what 分类：Memory/Tools/Workflow，模型冻结）。因此：

> **本系统的 RSI = 用测量驱动对自身 harness 的修改，并让「修改的有效性」本身成为被测量的对象。**

递归性的来源：L2 的输出（进化动作）改变 L1 的表现；L3 的输出（进化策略修正）改变 L2 的决策质量。环环相扣，测量是唯一的传递介质。

### 3.2 三环架构

```
L1 任务环（每周持续发生）
  wyf + agent 干真实活 ──产出──► 真实产物（调研/复盘/范式卡/纠错）
        ▲                              │
        │                        (滞后产物，防自评膨胀)
        │                              ▼
L2 进化环（周仪式，单线程）                │
  /benchmark ──► 判分+脚本断言 ──► ledger/runs/*.jsonl ──► SCORES.md(趋势+报警)
       │ ▲                                                  │
       │ └──── 实验核销（到期实验卡对分兑现）◄── 实验卡台账 ──┤
       │                                                    ▼
  /evolve ◄── 读趋势/报警/实验命中率 ── 五类动作决策单 + 起草实验卡
       │
       ▼
  wyf 审批（选择压力）──执行──► 基因组：CLAUDE.md / skills / memory / cases / rubrics
                                                    │
L3 元进化环（月/季）                                 │
  预测命中率 · 判分稳定性(复判探针) · 人机分歧率 · 实验命中率 ──┘
       │
       ▼
  修正评估器与进化策略本身（调 rubric 权重/通过线、调动作偏好、退休失效判分锚）
```

### 3.3 基因组隐喻映射表（v2 的本体论）

| 生物学 | ai-ops v2 | 载体 |
|---|---|---|
| 基因组 | 可进化的 harness | CLAUDE.md / skills / memory / cases / rubrics / 命令协议 |
| 适应度 | 维度分数 + 脚本通过率 | ledger + SCORES.md |
| 变异 | /evolve 五类动作 | 决策单 |
| 选择 | 用户审批（Darwinian 经验验证） | 你的勾选 |
| 基因谱系/archive | **实验卡**（新增） | `benchmarks/experiments/exp-*.md` |
| 表现型 | 真实任务产出 | vault / 各 repo 产物 |
| 遗传漂变防护 | 防 Goodhart 四道防线（v1 继承） | 命令硬规则 |

### 3.4 不变量（v1 全部继承，新增强化）

1. ROI 第一：实验卡本身也过采样门槛——一次性动作不建卡（口头升级不设卡，**可验证的方法升级才设卡**）。
2. 评分混合：scripted 主力 + judged 上限 4 条/轮。
3. git+skill 路径：不建基建，纯标准库。
4. 终局裁判是人。
5. **新增**：进化环单线程（Cognition 原则 + 本机并发=1）。
6. **新增**：每笔批准的进化动作必须可核销（要么是实验卡，要么显式标记为 one-shot 不跟踪）。

---

## 4. v2 理念设计与产品逻辑

### 4.1 组件变更清单

| 组件 | 动作 | 说明 |
|---|---|---|
| `benchmarks/experiments/` | **新增** | 实验卡台账（基因谱系）：exp-NNN.md，frontmatter 机器可解析 |
| `benchmarks/lib/group_scores.py` | **升级 v2** | 保持 v1 API 兼容；新增 `load_runs`/`load_experiments`/`due_predictions`/`due_experiments`/`alarms`；SCORES.md v2 增趋势变化、报警、校准、实验状态四节 |
| `benchmarks/tests/test_group_scores.py` | **升级** | 补 v2 函数测试，保留 v1 全部断言 |
| `benchmarks/cases/vf-002.md` | **新增** | scripted：仓库自校验（案例 schema 完整、judged 案例的 rubric 可解析、实验卡状态合法）——补漏类动作，validation 维度 |
| `benchmarks/rubrics/*.md`（4 张） | **补锚** | 各加 `## 校准锚` 节：引用 ledger 真实 evidence_ref 作 3.5 分位样例，判分时先对锚再打分 |
| `.claude/commands/benchmark.md` / `evolve.md` | **升级 v2** | benchmark 增「实验核销」步骤与到期清单；evolve 增「起草实验卡」硬要求 |
| `.zcode/skills/benchmark/SKILL.md`、`.zcode/skills/evolve/SKILL.md` | **新增** | ZCode 宿主入口（修 D6）；`lib/install_commands.sh` 一键装双宿主 |
| `AGENTS.md` | **新增** | 任何 agent 的冷启动入口 + 复刻协议 |
| `README.md` | **升级 v2** | 补三环架构、实验卡用法、双宿主安装；v1 内容全保留 |
| cases/rubrics(锚点除外)/ledger/pending/retros | **不动** | 数据与判分资产零迁移成本 |

### 4.2 实验卡规范（L2 闭环的载体）

```markdown
---
id: exp-001                      # exp-<三位序号>
type: 升级                        # 修剪|升级|补漏|实验提案|更高价值（同 /evolve 五类）
title: 聚合脚本 v2（趋势/报警/校准节）
parent: SCORES.md 08-29 静态无报警  # 谱系：哪个测量/痛点触发了本卡
hypothesis: 读分效率提升，报警可见后回归修复延迟 ≤1 轮
success_criteria: 测试全过；scripted 断言 6/6+1 PASS；SCORES.md 出现报警/校准节
affects: benchmarks/lib/group_scores.py   # 改了哪个基因组文件
deadline: 2026-09-06             # 核销期限（默认批准日起 +1 轮周仪式）
status: executed                 # proposed→approved→executed→verified|failed|superseded
result:                          # 核销后回填：命中/脱靶 + 一句话
created: 2026-08-30
---
（正文：实施细节、证据链接，可选）
```

规则：
- **谁起草**：/evolve 每输出一笔可验证动作，同步起草实验卡（proposed）。你批准 → approved；执行落盘 → executed。
- **谁核销**：/benchmark 步骤 0 读到期卡（`status ∈ {approved, executed}` 且 deadline ≤ 今天），对分核销：success_criteria 逐条对当前 run 证据，提议 verified/failed/superseded，**你确认后**脚本回填 status/result 并 commit。人只在两个真需要判断的点出现。
- **止损**：failed 的卡不删（archive 原则：失败也是谱系），result 写教训；同 parent 的新卡引用之。
- **元命中率**：各 type 的 verified/total 比即「哪类动作有效」，进 SCORES.md v2 元层节——L3 的输入。

### 4.3 协议变更

**/benchmark v2**（在 v1 七步上改）：
- 步骤 0 前插 **实验核销**：脚本 `due` 子命令吐到期卡清单 → 逐条对分核销（人确认）→ 回填。
- 步骤 2 judged 判分前先读 rubric `## 校准锚`，分位对齐再打分；每轮至少对 **1 条历史产物做复判探针**（与上轮分差 >±0.5 即判分器漂移信号，写进 triage.log，L3 素材）。
- 步骤 5 聚合升级为 v2（趋势变化/报警/校准/实验四节自动生成）。
- 报警自动开箱：scripted fail 或 judged 跌破通过线 → 同轮在 pending-reviews/ 起草一条待三选（P3 修复回流）。

**/evolve v2**：决策单每行必须给出 `exp-id`（新建卡或引用既有卡）；one-shot 动作显式标注「不跟踪」。第五类（更高价值问题）优先从 **no-data ≥3 期维度**与**报警维度**出题（P4 自出题）。

**SCORES.md v2 结构**：趋势主表（+较上轮 Δ）→ 报警节 → 校准节（prediction 命中率、判分稳定性、judge 标签分布）→ 实验节（各状态计数、type 命中率、到期卡）。

### 4.4 产品逻辑（三个角色 × 三个触点）

| 角色 | 触点 | 动作 | 成本 |
|---|---|---|---|
| wyf（裁判/选择者） | 周仪式 ~25min | 三选 pending → 看 SCORES 报警 → 批实验卡核销 | 比v1更短（核验自动化） |
| 执行 agent | 每天干活 | 正常出产物（滞后样例源）；报警回流时接单修复 | 零新增 |
| 进化 agent | /benchmark、/evolve | 跑分、核销、出决策单、起草卡 | 命令内含，无自由发挥 |

### 4.5 明确不做（YAGNI，继承 v1 否决并追加）

v1 否决项全部有效（多用户、MySQL、全自动判分、一次性任务案例化、强制复盘）。追加：不建 Elo 锦标赛、不建种群/岛、不建 Web 看板、不做多 agent 并行进化。

---

## 5. 打分对比（v1 vs v2）

评分口径：10 分制；评的是「设计理念」本身，每维附判据。评审人立场声明：由实施者评，存在自评膨胀风险，故每维判据先写死再打分，且打分依据全部指向本 spec 可查证的条目。

| # | 维度 | v1 | v2 | 判据与依据 |
|---|---|---|---|---|
| 1 | RSI 目的达成（以始为终） | 7.5 | 9.2 | v1 有测量无递归（修改不回流验证）；v2 三环互递归（§3.2），每笔动作可核销 |
| 2 | 闭环度/递归性 | 6.0 | 9.0 | v1 /evolve 决策单状态无跟踪（D1 实证）；v2 实验卡+脚本核销（§4.2） |
| 3 | 适应度函数质量 | 7.0 | 8.8 | v1 分数无 Δ、无报警、无校准（D2/D3 实证）；v2 四节 SCORES + 复判探针 + 锚样例 |
| 4 | 防 Goodhart | 8.5 | 9.3 | v1 四道防线保留满分基座；v2 增判分器自测量（预测命中率/人机分歧可见），对应 DGM 伪造分事故的工程对策 |
| 5 | 本地环境适配 | 5.0 | 9.5 | v1 命令在 ZCode 实测失效（D6）；v2 双宿主入口 + install 脚本，且遵守并发=1 的单线程环 |
| 6 | 冷启动/可复刻 | 7.5 | 9.0 | v1 README 靠人读；v2 AGENTS.md 给 agent 直接执行 + 复刻协议（论文→沉淀→设计→重构→测试全流程可重放） |
| 7 | ROI/成本 | 9.0 | 9.2 | 复杂度税：+1 目录 +1 脚本子命令（纯标准库）；自动化返还：预测核验/报警搬运从手工变脚本，周仪式更短；无基建、零依赖不变 |
| 8 | 前沿思想接轨 | 6.5 | 9.3 | v1 早于本轮研究；v2 五原则 P1–P5 逐条落地且有纠偏声明（§2.3），不盲从 |
| | **综合** | **7.13** | **9.16** | 8/8 维度 v2 ≥ v1，4 维显著领先 → **触发重构** |

---

## 6. 重构实施清单（本会话执行）

1. `docs/superpowers/specs/2026-08-30-rsi-v2-design.md`（本文件）
2. `benchmarks/lib/group_scores.py` v2 + 测试扩展
3. `benchmarks/experiments/`（README + 模板 + exp-001 首卡：把本次重构登记为第一张可核销实验）
4. `benchmarks/cases/vf-002.md` + `benchmarks/rubrics/*.md` 补校准锚
5. `.claude/commands/{benchmark,evolve}.md` v2 → 安装双宿主（`~/.claude/commands/` + `~/.zcode/skills/`）
6. `benchmarks/lib/install_commands.sh`
7. `README.md` v2 + `AGENTS.md`
8. 全量测试 + scripted 断言套跑 + 聚合产出 v2 SCORES.md → 汇报

## 7. 风险与回滚

- 风险：实验卡变成新的形式主义（卡片堆积不核销）→ 对策：卡的 deadline 由脚本强制到期提示；/evolve 看到 `proposed` 堆积 >3 必须先修剪。
- 风险：SCORES.md 变厚没人看 → 对策：报警节置顶且只有异常行，正常行折叠进表格。
- 回滚：全部变更走 git（分支 `refactor/rsi-v2`，逐 task commit），v1 数据文件零迁移，`git revert` 一键回退。
