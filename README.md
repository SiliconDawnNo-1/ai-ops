# ai-ops · 能力评测内核（Subsystem A）

把"纠错"沉淀成可重跑、可测量的能力资产。设计见 `docs/superpowers/specs/2026-08-16-benchmark-core-design.md`。

## 命令
- `/benchmark` — 跑分：三选 pending 箱 → 遍历 cases（脚本断言 / rubric 判分）→ 写账本 → 聚合 → commit
- `/evolve` — 进化：读趋势 → 修剪 / 升级 / 补漏 / 实验提案 / 更高价值问题（五类，你审批生效）

## 周仪式（~30min）
三选 pending → `/benchmark` → `/evolve` → commit

## 目录
- `benchmarks/cases/` 案例 · `benchmarks/rubrics/` 判分卡 · `benchmarks/ledger/` 账本+趋势
- `pending-reviews/` 纠错备选箱 · `retrospectives/` 长任务复盘卡

## 6 周成功标准
1) 重复纠错案例变少 2) 真实执行过修剪/升级 3) 评价 agent 的注意力下降 4) 能回答"agent 哪强哪弱、依据是什么"