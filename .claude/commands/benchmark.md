# 跑能力评测（v2）

根：`~/Desktop/code/ai-ops`（ROOT）。执行：

0. **实验核销（v2 新增，先于一切）**：`python3 $ROOT/benchmarks/lib/group_scores.py due` 取到期核验队列 → 逐条对照最近 run 数据核销实验卡的 `success_criteria`，提议 verified / failed / superseded → **用户确认后**回填卡 `status`/`result`，每笔追加 `$ROOT/pending-reviews/triage.log` 一行：`YYYY-MM-DD\texp\t<exp-id>\t<verified|failed|superseded>\t<一句话证据>`。
1. **三选 pending 箱**：`$ROOT/pending-reviews/*` 每条目 → 转正(起草 case 收录后删条目) / 丢弃 / 退回。每笔追加 `$ROOT/pending-reviews/triage.log` 一行：`YYYY-MM-DD\t<promote|discard|hold>\t<id|name>\t<原因>`。转正的 case 需过采样门槛三问（会再现？判分能防回归？固定成本 < 复用价值？）。
2. **核验上轮预测**：用步骤 0 输出的 predictions 清单（来自最近一期 run 的 `prediction` 字段），本轮实测比对，每条追加 `$ROOT/pending-reviews/triage.log` 一行：`YYYY-MM-DD\tcheck\t<case_id>\t命中 | 脱靶(<差值>)`。
3. **遍历 `$ROOT/benchmarks/cases/` status=active**：
   - scripted：按 case 的`## 断言`跑 Bash，记 pass/fail/skip(+原因)。
   - judged：**只判滞后产物** —— 取该维度"日期早于本周一"的最近真实产物按 rubric 判分；当周/当场的产物禁止入评（防自评膨胀）。无合格产物 → no-data 不判负。judged 单轮上限 4 条，超出先问用户。
   - judged 判分前**先读对应 rubric 的 `## 校准锚`**，分位对齐再打分；锚样例产物已被更近期产物替代时在汇报中提出换锚。
   - **复判探针（v2）**：每轮至少对 1 条上轮 judged 过的产物按同一 rubric 重判一次，与上轮分差 >±0.5 = 判分器漂移信号，追加 triage.log 一行：`YYYY-MM-DD\tprobe\t<case_id>\t<上轮分>→<本轮分>`。
   - 判分必须引用产物片段（evidence_ref），无证据不判分。
   - 每条 judged 记一个**可证伪预测**（`prediction` 字段）：下轮可核验的定量断言，如「下轮同产物 re-score 分差 ≤ ±0.5」。评分本身当作可校准假设，不得直接复读产物结论。
4. **报警回流（v2）**：聚合后读 SCORES.md 报警节——scripted fail 或 judged 跌破通过线 → 本轮在 `pending-reviews/` 起草一条待三选（回归修复回流）；no-data 连续 ≥3 期 → 留给 /evolve 出题，不在本轮处理。
5. **写账本**：追加 `$ROOT/benchmarks/ledger/runs/YYYY-MM-DD.jsonl`，每 case 一行：
   `{"case_id","dimension","score"(judged，含"prediction")|"status"(scripted)，"evidence_ref","judge"}`
   judge 按身份写实：滞后自评 → `agent-selfgrade`；本次用户亲审复核 → `user`；未判不写。同日重跑以本次为准（整文件重写）。
6. **聚合**：`python3 $ROOT/benchmarks/lib/group_scores.py`（v2 自动产出报警/趋势Δ/校准/实验四节）。
7. **提交**：`git -C $ROOT add -A && git -C $ROOT commit -m "benchmark: $(date +%F) run"`（提交前 git status/diff 自查；`.obsidian/` 已 gitignore 不入库）。
8. **汇报一句话**：到期实验核销结果、哪些维度涨/跌、上轮预测命中/脱靶、报警项、哪些 case 需用户裁决。
