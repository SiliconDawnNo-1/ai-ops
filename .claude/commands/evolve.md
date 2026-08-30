# 进化决策（v2）

根：`~/Desktop/code/ai-ops`（ROOT）。读 `$ROOT/benchmarks/ledger/SCORES.md`（v2 四节：报警/趋势/校准/实验）与 `runs/*.jsonl`。

产出**五类动作决策单**（全部用户审批后才执行，逐条 commit）。v2 硬规则：**每笔可验证动作必须同步起草实验卡** `benchmarks/experiments/exp-NNN.md`（模板 `_TEMPLATE.md`；frontmatter 规范见 experiments/README.md），决策单每行给出 exp-id；一次性动作显式标注「one-shot 不跟踪」：

1. **修剪**：维度持续低分(近4周 avg < 通过线)且真实复错误未降 → 建议退休/降级案例 或 升级对应方法。
2. **升级**：绿分且复现稳定 → 把方法沉淀进 `~/.claude/CLAUDE.md` / skill / memory（纠错→组织能力）。
3. **补漏**：分数与用户体感背离 → 调 rubric 或补 case（防 Goodhart）。
4. **实验提案**：假设 · 动作 · 成功标准 · 时限 —— 用户挑跑不跑。
5. **更高价值问题**：抛 1 个方向补盲建议（双向变异源）。**v2 优先级**：SCORES 报警行 > no-data 连续 ≥3 期的维度（自出题：给该维度一个出样任务，或提议退休案例，二选一必答）> 其他。

决策单格式（每类一行）：
`【修剪】案例 xxxx —— 原因 —— 建议动作 —— exp-id`
`【升级】方法 yyyy —— 依据 —— 落点 —— exp-id`
……用户勾选后即执行：批准的卡 status→approved；落盘完成 status→executed；执行动作 commit；更新 `pending-reviews/triage.log`。

**止损**：`proposed` 卡堆积 >3 张时，本次 /evolve 先修剪（转 approved 或合并/废弃）再出新决策单。
**元层自检（L3）**：看 SCORES「实验」节的 type 命中率——连续 2 张同类卡 failed → 停止再提该类型动作，改为补漏类。
