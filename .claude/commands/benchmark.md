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