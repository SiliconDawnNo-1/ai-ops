# SCORES.md

聚合维度数：7

## 报警

- ⚠ execution-discipline 脚本通过率 0.83 < 1.0，存在回归待追
- ⚠ cg-001 no-data 连续 3 期 → /evolve 必须出样任务或退休该案例

## 趋势

| 维度 | 运行次数 | judged平均分 | 最新分 | Δ上轮 | 脚本通过率 |
|---|---|---|---|---|---|
| diagnosis-root-cause | 3 | 4.18 | 4.15 | -0.28 | — |
| execution-discipline | 6 | — | — | — | 0.83 |
| infra-health | 6 | — | — | — | 1.0 |
| long-task-meta | 3 | 4.56 | 4.75 | +0.17 | — |
| reasoning-depth | 2 | 4.43 | 4.43 | +0.00 | — |
| retro-fit | 3 | — | — | — | 1.0 |
| validation | 3 | — | — | — | 1.0 |

## 校准

- 上轮 prediction 待核验：3 条
  - lm-001: 下轮同产物re-score分差≤±0.3;若无新复盘卡则为连续第3次引用同卡→触发/evolve补漏提案
  - dr-001: 下轮同产物re-score分差≤±0.5;若出现更近期真实归因产物则以其为准
  - rs-001: 下轮同产物re-score分差≤±0.5
- judge 标签分布：agent-selfgrade 3 / user 5

## 实验

- 卡片总数 1 ｜ executed 1
- type 命中率：升级 0/1
