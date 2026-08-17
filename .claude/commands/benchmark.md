# 跑能力评测

根：`~/Desktop/code/ai-ops`（ROOT）。执行：

1. **三选 pending 箱**：`$ROOT/pending-reviews/*` 每条目 → 转正(起草 case 收录后删条目) / 丢弃 / 退回。每笔追加 `$ROOT/pending-reviews/triage.log` 一行：`YYYY-MM-DD\t<promote|discard|hold>\t<id|name>\t<原因>`。转正的 case 需过采样门槛三问（会再现？判分能防回归？固定成本 < 复用价值？）。
2. **核验上轮预测**：读最近一期跑次账本（`$ROOT/benchmarks/ledger/runs/*.jsonl` 最新文件）里的 `prediction` 字段，本轮实测比对，每条追加 `$ROOT/pending-reviews/triage.log` 一行：`YYYY-MM-DD\tcheck\t<case_id>\t命中 | 脱靶(<差值>)`。
3. **遍历 `$ROOT/benchmarks/cases/` status=active**：
   - scripted：按 case 的`## 断言`跑 Bash，记 pass/fail/skip(+原因)。
   - judged：**只判滞后产物** —— 取该维度"日期早于本周一"的最近真实产物按 rubric 判分；当周/当场的产物禁止入评（防自评膨胀）。无合格产物 → no-data 不判负。judged 单轮上限 4 条，超出先问用户。
   - 判分必须引用产物片段（evidence_ref），无证据不判分。
   - 每条 judged 记一个**可证伪预测**（`prediction` 字段）：下轮可核验的定量断言，如「下轮同产物 re-score 分差 ≤ ±0.5」。评分本身当作可校准假设，不得直接复读产物结论。
4. **写账本**：追加 `$ROOT/benchmarks/ledger/runs/YYYY-MM-DD.jsonl`，每 case 一行：
   `{"case_id","dimension","score"(judged，含"prediction")|"status"(scripted)，"evidence_ref","judge"}`
   judge 按身份写实：滞后自评 → `agent-selfgrade`；本次用户亲审复核 → `user`；未判不写。同日重跑以本次为准（整文件重写）。
5. **聚合**：`python3 $ROOT/benchmarks/lib/group_scores.py`
6. **提交**：`git -C $ROOT add -A && git -C $ROOT commit -m "benchmark: $(date +%F) run"`（提交前 git status/diff 自查；`.obsidian/` 已 gitignore 不入库）。
7. **汇报一句话**：哪些维度涨/跌、上轮预测命中/脱靶、哪些 case 需用户裁决。