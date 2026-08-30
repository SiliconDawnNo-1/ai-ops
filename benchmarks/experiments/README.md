# experiments/ · 实验卡台账（v2 新增，基因谱系）

每个 `/evolve` 批准的**可验证动作** = 一张卡。这是个人版的 DGM archive（见 spec v2 §3.3）：记录「哪个测量触发了修改 → 假设是什么 → 何时核销 → 结果如何」，让进化决策从一次性散文变成可追责、可统计的谱系。

## 生命周期

```
/evolve 起草 proposed ──用户批准──► approved ──执行落盘──► executed
                                                            │
                          /benchmark 到期核销（用户确认）◄── deadline 到
                                │
                     verified（达标） / failed（未达标，教训回填） / superseded（被新卡取代）
```

## 规则（spec v2 §4.2）

1. **谁建卡**：/evolve 每输出一笔可验证动作同步起草（`status: proposed`）；口头小动作显式标 one-shot 不建卡。
2. **谁核销**：/benchmark 步骤 0 跑 `python3 benchmarks/lib/group_scores.py due` 取到期清单，逐条对 `success_criteria` 核销；**用户确认后**才回填 `status`/`result` 并 commit。
3. **失败卡不删**：archive 原则，`result` 写教训；同 parent 的新卡引用它。
4. **止损**：`proposed` 堆积 >3 张，/evolve 必须先修剪（防卡片形式主义）。
5. frontmatter 必须闭合 `---`、字段扁平（脚本无 PyYAML，逐行解析 `key: value`）。

## 字段

| 字段 | 说明 |
|---|---|
| `id` | exp-NNN，与文件名一致 |
| `type` | 修剪 / 升级 / 补漏 / 实验提案 / 更高价值（同 /evolve 五类） |
| `parent` | 谱系：触发本卡的测量或痛点（SCORES 报警 / 复盘卡 / 分数落差） |
| `hypothesis` | 一句话假设：做了它，什么会变好 |
| `success_criteria` | 可核销的判定，逐条列出（对分、对测试、对文件存在性） |
| `affects` | 落进基因组的哪个文件（CLAUDE.md / skill / case / rubric / 脚本） |
| `deadline` | 核销期限，ISO 日期（默认批准日 + 下一轮周仪式） |
| `status` | proposed → approved → executed → verified / failed / superseded |
| `result` | 核销后回填：达标结论 + 一句话证据 |

模板见 `_TEMPLATE.md`（下划线开头，不被 `exp-*.md` 解析）；第一张活样本见 `exp-001.md`。
