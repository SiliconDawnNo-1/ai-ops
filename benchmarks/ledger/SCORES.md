# SCORES.md

聚合维度数：8

## 报警

- ⚠ execution-discipline 脚本通过率 0.88 < 1.0，存在回归待追

## 趋势

| 维度 | 运行次数 | judged平均分 | 最新分 | Δ上轮 | 脚本通过率 |
|---|---|---|---|---|---|
| cross-domain-generalization | 1 | 4.48 | 4.48 | — | — |
| diagnosis-root-cause | 4 | 4.17 | 4.15 | +0.00 | — |
| execution-discipline | 8 | — | — | — | 0.88 |
| infra-health | 8 | — | — | — | 1.0 |
| long-task-meta | 4 | 4.61 | 4.75 | +0.00 | — |
| reasoning-depth | 3 | 4.43 | 4.43 | +0.00 | — |
| retro-fit | 4 | — | — | — | 1.0 |
| validation | 5 | — | — | — | 1.0 |

## 校准

- 上轮 prediction 待核验：4 条
  - lm-001: 下轮同产物re-score分差≤±0.3;若无新复盘卡将连续第4次引用同卡→/evolve必须出新复盘卡或换锚
  - dr-001: 下轮同产物re-score分差≤±0.5;或以更近期真实归因产物为准
  - rs-001: 下轮同产物re-score分差≤±0.5
  - cg-001: 下轮同产物re-score分差≤±0.5;若雷达深挖产生新范式卡(12-learn-and-agent体系)则以其为准
- judge 标签分布：agent-selfgrade 7 / user 5

## 实验

- 卡片总数 1 ｜ verified 1
- type 命中率：升级 1/1
