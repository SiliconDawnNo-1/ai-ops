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