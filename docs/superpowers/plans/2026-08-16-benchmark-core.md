# 能力评测内核 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `~/Desktop/code/ai-ops` 建起能力评测内核（子系统 A）：10 条案例 + 4 张判分卡 + `/benchmark` `/evolve` 命令 + 评分聚合脚本，跑出基线 SCORES.md。

**Architecture:** 全部产物为本地文件：案例/rubric 是 markdown；脚本级 case 通过 Bash 断言执行，judged case 按 rubric 取最近真实产物判分并由用户审批；`group_scores.py` 聚合 ledger jsonl 生成趋势表；两个 Claude Code 命令封装运行与进化流程。数据流：pending 三选 → 遍历 cases → 写 ledger/runs/{date}.jsonl → 聚合 → SCORES.md → git commit。

**Tech Stack:** Bash + Python3（标准库，无第三方依赖）+ Claude Code commands（markdown prompt）+ git。

**执行模式前提（Checkpoint 纪律）:** 所有实现工作在分支 `feat/benchmark-core` 上进行；每个 Task 完成后 commit。

---

## File Structure

| 文件 | 职责 |
|---|---|
| `~/.claude/commands/benchmark.md`（仓库镜像 `.claude/commands/benchmark.md`） | 跑分命令：指导 Claude 执行三选/遍历/判分/写账本/聚合/提交 |
| `~/.claude/commands/evolve.md`（仓库镜像 `.claude/commands/evolve.md`） | 进化命令：读趋势产出五类动作，用户审批后执行 |
| `benchmarks/rubrics/*.md`（4 个） | 判分卡：锚 + 权重 + 通过线 + 评分指引 |
| `benchmarks/cases/*.md`（10 个） | 案例：frontmatter + 场景 + 门槛 + 判分依据/断言 |
| `benchmarks/lib/group_scores.py` | 聚合 ledger jsonl → 每维度趋势 → 写 SCORES.md |
| `benchmarks/tests/test_group_scores.py` | 聚合脚本的自测（纯 assert，无依赖） |
| `benchmarks/ledger/runs/` | 每次运行原始评分 jsonl |
| `benchmarks/ledger/SCORES.md` | 自动生成的趋势总览 |
| `pending-reviews/triage.log` | 三选决策流水 |
| `README.md` | 系统用法：命令 + 周仪式 |
| `.gitignore` | 忽略 .DS_Store / __pycache__ |

---

### Task 1: 分支 + 骨架 + README

**Files:**
- Create: `~/Desktop/code/ai-ops/.gitignore`
- Create: `~/Desktop/code/ai-ops/README.md`

- [ ] **Step 1: 建 feature 分支**

```bash
git -C ~/Desktop/code/ai-ops checkout -b feat/benchmark-core
```

- [ ] **Step 2: 写 `.gitignore`**

```gitignore
.DS_Store
__pycache__/
*.pyc
```

- [ ] **Step 3: 写 `README.md`**

```markdown
# ai-ops · 能力评测内核（Subsystem A）

把"纠错"沉淀成可重跑、可测量的能力资产。设计见 `docs/superpowers/specs/2026-08-16-benchmark-core-design.md`。

## 命令
- `/benchmark` — 跑分：三选 pending 箱 → 遍历 cases（脚本断言 / rubric 判分）→ 写账本 → 聚合 → commit
- `/evolve` — 进化：读趋势 → 修剪 / 升级 / 补漏 / 实验提案 / 更高价值问题（五类,你审批生效）

## 周仪式（~30min）
三选 pending → `/benchmark` → `/evolve` → commit

## 目录
- `benchmarks/cases/` 案例 · `benchmarks/rubrics/` 判分卡 · `benchmarks/ledger/` 账本+趋势
- `pending-reviews/` 纠错备选箱 · `retrospectives/` 长任务复盘卡

## 6 周成功标准
1) 重复纠错案例变少 2) 真实执行过修剪/升级 3) 评价 agent 的注意力下降 4) 能回答"agent 哪强哪弱、依据是什么"
```

- [ ] **Step 4: 提交**

```bash
git -C ~/Desktop/code/ai-ops add .gitignore README.md
git -C ~/Desktop/code/ai-ops commit -m "feat: bench-core 骨架(分支+README+gitignore)"
```

---

### Task 2: 4 张判分卡

**Files:**
- Create: `~/Desktop/code/ai-ops/benchmarks/rubrics/insight-chain.md`
- Create: `~/Desktop/code/ai-ops/benchmarks/rubrics/diagnosis-root-cause.md`
- Create: `~/Desktop/code/ai-ops/benchmarks/rubrics/long-task-meta.md`
- Create: `~/Desktop/code/ai-ops/benchmarks/rubrics/cross-domain-generalization.md`

- [ ] **Step 1: 写四张判分卡（一次写全）**

`benchmarks/rubrics/insight-chain.md`:

```markdown
# 判分卡 · 洞察链质量（reasoning-depth）

每锚 0–5 分；总 = 加权平均；通过线：总分 ≥ 3.5/5 且"链数 ≥ 3"。
判分必须附 evidence_ref（产物路径/复盘卡 id）中的具体片段引用，无证据不给分。

| 锚 | 描述 | 权重 | 打 1 分 | 打 5 分 |
|---|---|---|---|---|
| 链数 | 非显然洞察条数（≠ 数据复述） | 30% | 只有数据搬运/归类 | ≥3 条非显然结论 |
| so-what 深度 | 平均链层数（数据→意义→后果） | 25% | 停在"数据是什么" | ≥2 层，能落到影响/决策 |
| 交叉拧链 | 数据与机制拧成一条因果链 | 20% | 数据与机制各说各话 | 同一底层因素多维拧链 |
| 反事实/情景 | 有反事实推理或情景推演 | 15% | 无 | ≥2 种情景或反事实 |
| 口径质疑 | 对来源假设/利益偏向做推理性筛选 | 10% | 全盘接受来源数值 | 质疑口径并说明影响 |
```

`benchmarks/rubrics/diagnosis-root-cause.md`:

```markdown
# 判分卡 · 诊断归因质量（diagnosis-root-cause）

每锚 0–5 分；总 = 加权平均；通过线：总分 ≥ 3.5/5。
判分必须附 evidence_ref 片段引用。

| 锚 | 描述 | 权重 | 打 1 分 | 打 5 分 |
|---|---|---|---|---|
| 根因 vs 表象 | 归因到机制层而非事件顺序 | 30% | 描述发生顺序，无机制 | 定位机制/根因，说明链条 |
| 假设-验证 | 有显式假设 + 证据闭环 | 25% | 直接下结论无验证 | 假设→验证→必要时修正 |
| 证据强度 | 关键结论有锚定证据 | 20% | 空谈/单源无出处 | 结论有可核验锚点 |
| 停止纪律 | 不陷细节、不无限铺开 | 15% | 陷进细节陷阱出不来 | 有止损/stopping，交代取舍 |
| 结论可交付 | 一句话可说清根因 | 10% | 说不清 | 一句话能讲清 |
```

`benchmarks/rubrics/long-task-meta.md`:

```markdown
# 判分卡 · 长任务元复盘质量（long-task-meta）

每锚 0–5 分；总 = 加权平均；通过线：总分 ≥ 3.5/5。
判分对象：`retrospectives/*.md` 复盘卡。

| 锚 | 描述 | 权重 | 打 1 分 | 打 5 分 |
|---|---|---|---|---|
| 归因正确性 | 根因 vs 表象，控混淆 | 30% | 甩锅后端/effort/环境 | 只归自身执行，点明机制 |
| 结构拆解 | 子结论真实独立、依赖正确 | 25% | 无拆解或维度重叠 | 独立子结论+依赖+风险 |
| 可迁移性 | 泛化方法+命名+可用条件 | 20% | 只描述该次事件 | 抽象原则+何时适用/失效 |
| 实验可测性 | 有成功标准+栓进 case | 15% | 无假设 | 假设+动作+成功标准+case |
| 执行闭环 | 结论被后续任务实际用上 | 10% | 复盘完就扔 | 下次任务引用了该卡结论 |
```

`benchmarks/rubrics/cross-domain-generalization.md`:

```markdown
# 判分卡 · 跨领域成功范式提炼质量（cross-domain-generalization）

每锚 0–5 分；总 = 加权平均；通过线：总分 ≥ 3.5/5。
判分对象：高精尖领域(前沿实验室/高端芯片/医疗/华尔街金融/奥运训练)的范式卡。

| 锚 | 描述 | 权重 | 打 1 分 | 打 5 分 |
|---|---|---|---|---|
| 问题设定提炼 | 提炼"为什么这样框定问题"的机制 | 25% | 照抄领域名词 | 讲清框定动机与取舍 |
| 长周期调测 | 数据采集+长时间段 tuning 循环结构 | 20% | 泛泛而谈 | 数据→调测→反馈的闭环 |
| 归因严谨 | 高噪声/不可复现下如何归因 | 20% | 因果当相关 | 控制混淆、多源印证、说明置信 |
| 泛化边界 | 原则有可操作边界非口号 | 20% | 无边界的口号 | 明确条件(适用/失效) |
| 表征迁移 | 映射到另一领域的等价问题 | 15% | 无 | 例证跨域等价映射+RL 对照 |
```

- [ ] **Step 2: 校验文件存在且非空**

```bash
test -s ~/Desktop/code/ai-ops/benchmarks/rubrics/insight-chain.md && test -s ~/Desktop/code/ai-ops/benchmarks/rubrics/diagnosis-root-cause.md && test -s ~/Desktop/code/ai-ops/benchmarks/rubrics/long-task-meta.md && test -s ~/Desktop/code/ai-ops/benchmarks/rubrics/cross-domain-generalization.md && echo RUBRICS-OK
```

Expected: `RUBRICS-OK`

- [ ] **Step 3: 提交**

```bash
git -C ~/Desktop/code/ai-ops add benchmarks/rubrics
git -C ~/Desktop/code/ai-ops commit -m "spec: 4 张判分卡(洞察链/诊断归因/长任务元复盘/跨领域范式)"
```

---

### Task 3: 10 条案例

**Files:**
- Create: `~/Desktop/code/ai-ops/benchmarks/cases/{rs-001,dr-001,lm-001,cg-001,ex-001,ex-002,ih-001,ih-002,vf-001,rf-001}.md`（各含 frontmatter）

- [ ] **Step 1: 写 4 条 judged 案例**

`benchmarks/cases/rs-001.md`:

```markdown
---
id: rs-001
dimension: reasoning-depth
title: 洞察链质量·调研/拆解交付
type: judged
status: active
source: deep-reasoning-data-value
created: 2026-08-16
usage: 周频
priority: P0
rubric: rubrics/insight-chain.md
---

## 场景
含外部数据的调研/拆解/分析任务（芯片成本、行业拆解、竞争对比）交付后；判分样例 = 本周该维度最近真实产物，无则 no-data。

## 质量门槛
输出 ≥3 条非显然洞察链；每条 so-what ≥2 层；数据与机制交叉拧链；≥1 处反事实或情景推演；对关键来源有口径质疑。

## 判分依据
见 rubrics/insight-chain.md；判分必须附产物片段引用。
```

`benchmarks/cases/dr-001.md`:

```markdown
---
id: dr-001
dimension: diagnosis-root-cause
title: 排查归因·失败根因判定
type: judged
status: active
source: reasoning-driven-execution
created: 2026-08-16
usage: 周频
priority: P0
rubric: rubrics/diagnosis-root-cause.md
---

## 场景
一次失败/异常/不符合预期的复盘归因（构建失败、调研结论被推翻、性能/质量事件）。

## 质量门槛
归因到机制/根因层而非事件顺序；有显式假设+证据闭环；关键结论有锚定证据；有停止纪律；一句话能说清根因。

## 判分依据
见 rubrics/diagnosis-root-cause.md。
```

`benchmarks/cases/lm-001.md`:

```markdown
---
id: lm-001
dimension: long-task-meta
title: 长任务元复盘质量
type: judged
status: active
source: D+ increment (spec §6)
created: 2026-08-16
usage: 周频
priority: P1
rubric: rubrics/long-task-meta.md
---

## 场景
长/复杂任务（启发式：多独立子结论/有交付物/跨天）完成后自动生成的复盘卡；判分样例 = `retrospectives/` 最近一张卡。

## 质量门槛
四段完整；归因控混淆（不甩锅后端/effort）；最佳实践可迁移（泛化+可用条件）；实验建议可测（成功标准+栓进 case）；结论在后续任务实际被用。

## 判分依据
见 rubrics/long-task-meta.md。
```

`benchmarks/cases/cg-001.md`:

```markdown
---
id: cg-001
dimension: cross-domain-generalization
title: 跨领域成功范式提炼
type: judged
status: active
source: D+2 increment (spec §3 范式卡通道)
created: 2026-08-16
usage: 月频
priority: P1
rubric: rubrics/cross-domain-generalization.md
---

## 场景
从高精尖领域（前沿实验室/高端芯片设计/医疗/华尔街金融/奥运训练）提炼成功范式，产出范式卡。

## 质量门槛
问题设定提炼到机制层；长周期调测循环结构讲清；高噪声下归因严谨；泛化有可操作边界；有等价问题映射示例。

## 判分依据
见 rubrics/cross-domain-generalization.md。
```

- [ ] **Step 2: 写 6 条 scripted 案例**

`benchmarks/cases/ex-001.md`:

```markdown
---
id: ex-001
dimension: execution-discipline
title: 提交消息规范（可审计）
type: scripted
status: active
source: change-impact-rollback-workflow
created: 2026-08-16
usage: 周频
priority: P1
---

## 场景
任何实现/变更提交后。

## 质量门槛
HEAD commit message 以约定前缀开头（feat/spec/docs/chore/fix/refactor），保证每步有"做了什么+进度"。

## 断言
git -C ~/Desktop/code/ai-ops log -1 --pretty=%s | grep -Eq '^(feat|spec|docs|chore|fix|refactor):'
```

`benchmarks/cases/ex-002.md`:

```markdown
---
id: ex-002
dimension: execution-discipline
title: 检查点粒度（非一次提交）
type: scripted
status: active
source: long-task-checkpoint-workflow
created: 2026-08-16
usage: 周频
priority: P1
---

## 场景
长任务实现过程。

## 质量门槛
commit 数 ≥ 4（证明长任务是分步提交，可中断恢复，而非全做完才交）。

## 断言
test $(git -C ~/Desktop/code/ai-ops rev-list --count HEAD) -ge 4
```

`benchmarks/cases/ih-001.md`:

```markdown
---
id: ih-001
dimension: infra-health
title: 内存索引预算
type: scripted
status: active
source: CLAUDE.md 记忆分层规则
created: 2026-08-16
usage: 月频
priority: P1
---

## 场景
每周维护后。

## 质量门槛
MEMORY.md ≤ 200 行（超长尾部不再加载）。

## 断言
test $(wc -l < ~/.claude/projects/-Users-wyf/memory/MEMORY.md) -le 200
```

`benchmarks/cases/ih-002.md`:

```markdown
---
id: ih-002
dimension: infra-health
title: vault 结构不变式
type: scripted
status: active
source: personal-knowledge-vault
created: 2026-08-16
usage: 月频
priority: P1
---

## 场景
vault 维护后。

## 质量门槛
CLAUDE.md 与 INDEX.md 存在且非空（基础设施结构未被破坏）。

## 断言
test -s ~/Desktop/code/document/CLAUDE.md && test -s ~/Desktop/code/document/INDEX.md
```

`benchmarks/cases/vf-001.md`:

```markdown
---
id: vf-001
dimension: validation
title: 交付物完整（spec 无 TBD）
type: scripted
status: active
source: verification-before-completion
created: 2026-08-16
usage: 周频
priority: P1
---

## 场景
每次套件迭代交付后。

## 质量门槛
README 与 spec 存在；spec 不含占位符 TBD。

## 断言
test -s ~/Desktop/code/ai-ops/README.md && test -s ~/Desktop/code/ai-ops/docs/superpowers/specs/2026-08-16-benchmark-core-design.md && ! grep -q "TBD" ~/Desktop/code/ai-ops/docs/superpowers/specs/2026-08-16-benchmark-core-design.md
```

`benchmarks/cases/rf-001.md`:

```markdown
---
id: rf-001
dimension: retro-fit
title: 复盘卡纪律
type: scripted
status: active
source: D+ increment / retro-fit
created: 2026-08-16
usage: 周频
priority: P1
---

## 场景
长任务之后。

## 质量门槛
retrospectives/ 至少 1 张卡，且最近一张含 `## 归因` 节。

## 断言
test -n "$(ls ~/Desktop/code/ai-ops/retrospectives/ | grep -v '\.DS_Store')" && grep -q '## 归因' ~/Desktop/code/ai-ops/retrospectives/*.md
```

- [ ] **Step 3: 校验案例数**

```bash
ls ~/Desktop/code/ai-ops/benchmarks/cases/*.md | wc -l
```

Expected: `10`

- [ ] **Step 4: 提交**

```bash
git -C ~/Desktop/code/ai-ops add benchmarks/cases
git -C ~/Desktop/code/ai-ops commit -m "spec: 10 条基准案例(4 judged + 6 scripted)"
```

---

### Task 4: 评分聚合脚本（TDD）

**Files:**
- Create: `~/Desktop/code/ai-ops/benchmarks/tests/test_group_scores.py`
- Create: `~/Desktop/code/ai-ops/benchmarks/lib/group_scores.py`

- [ ] **Step 1: 先写失败测试（纯 assert，无依赖）**

`~/Desktop/code/ai-ops/benchmarks/tests/test_group_scores.py`:

```python
#!/usr/bin/env python3
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from group_scores import aggregate, render_markdown

FIXTURE = [
    '{"case_id":"rs-001","dimension":"reasoning-depth","score":3.8,"evidence_ref":"retro/2026-08-16.md","judge":"user"}\n',
    '{"case_id":"rs-001","dimension":"reasoning-depth","score":4.2,"evidence_ref":"s2","judge":"user"}\n',
    '{"case_id":"ex-001","dimension":"execution-discipline","status":"pass"}\n',
    '{"case_id":"ex-001","dimension":"execution-discipline","status":"fail"}\n',
    '{"case_id":"ih-001","dimension":"infra-health","status":"pass"}\n',
    '{"case_id":"dr-001","dimension":"diagnosis-root-cause","score":3.0,"evidence_ref":"s3","judge":"user"}\n',
]

def main():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "2026-08-16.jsonl"), "w") as fh:
            fh.writelines(FIXTURE)
        agg = aggregate(d)
        assert set(agg) == {"reasoning-depth", "execution-discipline", "infra-health", "diagnosis-root-cause"}, agg
        assert agg["reasoning-depth"]["avg"] == 4.0, agg["reasoning-depth"]
        assert agg["reasoning-depth"]["latest"] == 4.2, agg["reasoning-depth"]
        assert agg["diagnosis-root-cause"]["avg"] == 3.0
        assert agg["execution-discipline"]["pass_rate"] == 0.5, agg["execution-discipline"]
        assert agg["infra-health"]["pass_rate"] == 1.0
        md = render_markdown(agg)
        assert "reasoning-depth" in md and "4.0" in md and "4.2" in md and "0.5" in md
    print("ALL-PASS")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行，确认失败（模块不存在）**

```bash
python3 ~/Desktop/code/ai-ops/benchmarks/tests/test_group_scores.py
```

Expected: 报错 `ModuleNotFoundError: No module named 'group_scores'`

- [ ] **Step 3: 实现聚合脚本**

`~/Desktop/code/ai-ops/benchmarks/lib/group_scores.py`:

```python
#!/usr/bin/env python3
"""Aggregate benchmark ledger runs into per-dimension trends; emit SCORES.md."""
import glob, json, os, sys

def _dimension(record):
    dim = record.get("dimension")
    return dim if dim else record.get("case_id", "?").split("-")[0]

def aggregate(runs_dir):
    """Return {dimension: {runs, avg, latest, pass_rate}} from runs/*.jsonl."""
    data = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                dim = _dimension(rec)
                bucket = data.setdefault(dim, {"runs": 0, "scores": [], "passes": 0, "judged": 0})
                bucket["runs"] += 1
                if rec.get("score") is not None:
                    bucket["scores"].append(float(rec["score"]))
                    bucket["judged"] += 1
                elif rec.get("status") == "pass":
                    bucket["passes"] += 1
    out = {}
    for dim, b in data.items():
        scripted = b["runs"] - b["judged"]
        out[dim] = {
            "runs": b["runs"],
            "avg": round(sum(b["scores"]) / len(b["scores"]), 2) if b["scores"] else None,
            "latest": b["scores"][-1] if b["scores"] else None,
            "pass_rate": round(b["passes"] / scripted, 2) if scripted else None,
        }
    return out

def render_markdown(agg, title="SCORES.md"):
    lines = [f"# {title}", "", f"聚合维度数：{len(agg)}", "",
             "| 维度 | 运行次数 | judged平均分 | 最新分 | 脚本通过率 |",
             "|---|---|---|---|---|"]
    for dim in sorted(agg):
        b = agg[dim]
        lines.append(f"| {dim} | {b['runs']} | {b['avg'] if b['avg'] is not None else '—'} | "
                     f"{b['latest'] if b['latest'] is not None else '—'} | {b['pass_rate'] if b['pass_rate'] is not None else '—'} |")
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    root = os.path.expanduser("~/Desktop/code/ai-ops/benchmarks")
    runs = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "ledger", "runs")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "ledger", "SCORES.md")
    agg = aggregate(runs)
    with open(out, "w") as fh:
        fh.write(render_markdown(agg))
    for dim, b in sorted(agg.items()):
        print(f"[{dim}] runs={b['runs']} avg={b['avg']} latest={b['latest']} pass_rate={b['pass_rate']}")
```

- [ ] **Step 4: 运行，确认通过**

```bash
python3 ~/Desktop/code/ai-ops/benchmarks/tests/test_group_scores.py
```

Expected: `ALL-PASS`

- [ ] **Step 5: 提交**

```bash
git -C ~/Desktop/code/ai-ops add benchmarks/lib benchmarks/tests
git -C ~/Desktop/code/ai-ops commit -m "feat: ledger 聚合脚本 group_scores(TDD)"
```

---

### Task 5: `/benchmark` 命令（仓库 + 安装全局）

**Files:**
- Create: `~/Desktop/code/ai-ops/.claude/commands/benchmark.md`
- Install: `~/.claude/commands/benchmark.md`（cp 副本）

- [ ] **Step 1: 写命令**

`~/Desktop/code/ai-ops/.claude/commands/benchmark.md`:

```markdown
# 跑能力评测

根：`~/Desktop/code/ai-ops`（ROOT）。执行：

1. **三选 pending 箱**：`$ROOT/pending-reviews/*` 每条目 → 转正(起草 case 收录后删条目) / 丢弃 / 退回。每笔追加 `$ROOT/pending-reviews/triage.log` 一行：`YYYY-MM-DD\t<promote|discard|hold>\t<id|name>\t<原因>`。转正的 case 需过采样门槛三问（会再现？判分能防回归？固定成本 < 复用价值？）。
2. **遍历 `$ROOT/benchmarks/cases/` status=active**：
   - scripted：按 case 的`## 断言`跑 Bash，记 pass/fail/skip(+原因)。
   - judged：取本周该维度最近真实产物按 rubric 判分；无产物 → no-data 不判负。judged 单轮上限 4 条，超出先问用户。
   - 判分必须引用产物片段（evidence_ref），无证据不判分。
3. **写账本**：追加 `$ROOT/benchmarks/ledger/runs/YYYY-MM-DD.jsonl`，每 case 一行：
   `{"case_id","dimension","score"(judged)|"status"(scripted),"evidence_ref","judge"}`
   judge 一律 `user`（凡用户审批过的）。同日重跑以本次为准（整文件重写）。
4. **聚合**：`python3 $ROOT/benchmarks/lib/group_scores.py`
5. **提交**：`git -C $ROOT add -A && git -C $ROOT commit -m "benchmark: $(date +%F) run"`（提交前 git status/diff 自查）。
6. **汇报一句话**：哪些维度涨/跌，哪些 case 需用户裁决。
```

- [ ] **Step 2: 安装到全局命令并校验**

```bash
cp ~/Desktop/code/ai-ops/.claude/commands/benchmark.md ~/.claude/commands/benchmark.md && test -s ~/.claude/commands/benchmark.md && head -1 ~/.claude/commands/benchmark.md
```

Expected 首行含 `跑能力评测`

- [ ] **Step 3: 提交**

```bash
git -C ~/Desktop/code/ai-ops add .claude/commands/benchmark.md
git -C ~/Desktop/code/ai-ops commit -m "feat: /benchmark 命令(三选/遍历/判分/账本/聚合)"
```

---

### Task 6: `/evolve` 命令（仓库 + 安装全局）

**Files:**
- Create: `~/Desktop/code/ai-ops/.claude/commands/evolve.md`
- Install: `~/.claude/commands/evolve.md`（cp 副本）

- [ ] **Step 1: 写命令**

`~/Desktop/code/ai-ops/.claude/commands/evolve.md`:

```markdown
# 进化决策（周）

根：`~/Desktop/code/ai-ops`（ROOT）。读 `$ROOT/benchmarks/ledger/SCORES.md` 与 `runs/*.jsonl`。

产出**五类动作决策单**（全部用户审批后才执行，逐条 commit）：
1. **修剪**：维度持续低分(近4周 avg < 通过线)且真实复错误未降 → 建议退休/降级案例 或 升级对应方法。
2. **升级**：绿分且复现稳定 → 把方法沉淀进 `~/.claude/CLAUDE.md` / skill / memory（纠错→组织能力）。
3. **补漏**：分数与用户体感背离 → 调 rubric 或补 case（防 Goodhart）。
4. **实验提案**：假设 · 动作 · 成功标准 · 时限 —— 用户挑跑不跑。
5. **更高价值问题**：抛 1 个方向补盲建议（双向变异源）。

决策单格式（每类一行）：
`【修剪】案例 xxxx —— 原因 —— 建议动作`
`【升级】方法 yyyy —— 依据 —— 落点`
……用户勾选后即执行；执行动作 commit；更新 `pending-reviews/triage.log`。
```

- [ ] **Step 2: 安装到全局命令并校验**

```bash
cp ~/Desktop/code/ai-ops/.claude/commands/evolve.md ~/.claude/commands/evolve.md && test -s ~/.claude/commands/evolve.md && head -1 ~/.claude/commands/evolve.md
```

Expected 首行含 `进化决策`

- [ ] **Step 3: 提交**

```bash
git -C ~/Desktop/code/ai-ops add .claude/commands/evolve.md
git -C ~/Desktop/code/ai-ops commit -m "feat: /evolve 命令(五类进化动作决策单)"
```

---

### Task 7: dry-run → 基线 SCORES.md + 收尾

**Files:**
- Create: `~/Desktop/code/ai-ops/benchmarks/ledger/runs/.gitkeep`
- Modify: `~/Desktop/code/ai-ops/pending-reviews/triage.log`
- Generate: `~/Desktop/code/ai-ops/benchmarks/ledger/SCORES.md`

- [ ] **Step 1: 种子 baseline 账本（当日真实 run 前先空跑一次聚合成空表）**

```bash
touch ~/Desktop/code/ai-ops/benchmarks/ledger/runs/.gitkeep
printf '2026-08-16\tpromote\t(retro call) 基线空账本,首轮真实 run\n' > ~/Desktop/code/ai-ops/pending-reviews/triage.log
python3 ~/Desktop/code/ai-ops/benchmarks/lib/group_scores.py
cat ~/Desktop/code/ai-ops/benchmarks/ledger/SCORES.md
```

Expected：SCORES.md 出现空维度表头（`聚合维度数：0`）——这是真实基线，下一轮 /benchmark 才有分数。

- [ ] **Step 2: 对 6 条 scripted 断言逐条手工预跑确认可执行**

```bash
cd ~/Desktop/code/ai-ops && sh -c 'git log -1 --pretty=%s | grep -Eq "^(feat|spec|docs|chore|fix|refactor):"; echo ex001=$?; test $(git rev-list --count HEAD) -ge 4; echo ex002=$?; test $(wc -l < ~/.claude/projects/-Users-wyf/memory/MEMORY.md) -le 200; echo ih001=$?; test -s ~/Desktop/code/document/CLAUDE.md && test -s ~/Desktop/code/document/INDEX.md; echo ih002=$?; test -s ~/Desktop/code/ai-ops/README.md && test -s ~/Desktop/code/ai-ops/docs/superpowers/specs/2026-08-16-benchmark-core-design.md && ! grep -q "TBD" ~/Desktop/code/ai-ops/docs/superpowers/specs/2026-08-16-benchmark-core-design.md; echo vf001=$?; test -n "$(ls ~/Desktop/code/ai-ops/retrospectives/ | grep -v .DS_Store)" && grep -q "归因" ~/Desktop/code/ai-ops/retrospectives/*.md; echo rf001=$?'
```

Expected：6 行 `=0`（或 rf001=0——注意 ex-001 通过取决于当前 HEAD 消息以前缀开头）。

- [ ] **Step 3: 提交收尾**

```bash
git -C ~/Desktop/code/ai-ops add -A
git -C ~/Desktop/code/ai-ops commit -m "chore: baseline 空账本 + triage.log + SCORES.md"
git -C ~/Desktop/code/ai-ops log --oneline | head -10
```

Expected：`feat/benchmark-core` 上 ≥ 6 条 commit，`ex-002` 通过（commit 数 ≥4）。

- [ ] **Step 4: 全局命令最终校验**

```bash
ls -la ~/.claude/commands/benchmark.md ~/.claude/commands/evolve.md
```

Expected：两个命令文件存在（下次会话可直接 `/benchmark` `/evolve`）。