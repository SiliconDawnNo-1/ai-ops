---
name: benchmark
description: 跑 ai-ops 能力评测（周仪式）。当用户说「跑 /benchmark」「跑 benchmark」「跑能力评测」时使用。含实验核销、三选纠错箱、scripted 断言、judged 滞后判分、预测核验、复判探针、聚合与提交。
---

# 执行协议（单一事实源）

读并严格执行协议文件：`/Users/wyf/Desktop/code/ai-ops/.claude/commands/benchmark.md`

- 该文件是 v2 协议的唯一权威版本（步骤 0 实验核销 → 三选 pending → 预测核验 → 遍历案例 → 报警回流 → 写账本 → 聚合 → 提交 → 汇报）。
- 判分卡在 `/Users/wyf/Desktop/code/ai-ops/benchmarks/rubrics/`，判分前先读对应卡的 `## 校准锚`。
- 聚合脚本：`python3 /Users/wyf/Desktop/code/ai-ops/benchmarks/lib/group_scores.py`；到期核验队列：`python3 .../group_scores.py due`。
- 铁律：只判滞后产物（早于本周一）；判分必带 evidence_ref；judged 上限 4 条/轮；用户是终局裁判。
