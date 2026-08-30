#!/usr/bin/env python3
"""group_scores v1+v2 全量测试：纯 assert，无第三方依赖。"""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from group_scores import (aggregate, render_markdown, load_runs, load_experiments,
                          parse_frontmatter, due_predictions, due_experiments,
                          experiment_stats, no_data_streaks, alarms)

FIXTURE = [
    '{"case_id":"rs-001","dimension":"reasoning-depth","score":3.8,"evidence_ref":"retro/2026-08-16.md","judge":"user"}\n',
    '{"case_id":"rs-001","dimension":"reasoning-depth","score":4.2,"evidence_ref":"s2","judge":"user"}\n',
    '{"case_id":"ex-001","dimension":"execution-discipline","status":"pass"}\n',
    '{"case_id":"ex-001","dimension":"execution-discipline","status":"fail"}\n',
    '{"case_id":"ih-001","dimension":"infra-health","status":"pass"}\n',
    '{"case_id":"dr-001","dimension":"diagnosis-root-cause","score":3.0,"evidence_ref":"s3","judge":"user"}\n',
    '{"case_id":"cg-001","dimension":"cross-domain-generalization","status":"no-data"}\n',
]

EXP_CARD = """---
id: exp-001
type: 升级
title: 聚合脚本 v2
parent: SCORES.md 静态无报警
hypothesis: 读分效率提升
success_criteria: 测试全过
affects: benchmarks/lib/group_scores.py
deadline: {deadline}
status: {status}
result:
created: 2026-08-30
---
正文可省。
"""

EXP_BAD = "no frontmatter here\n"


def write(tmp, name, text):
    with open(os.path.join(tmp, name), "w") as fh:
        fh.write(text)


def test_v1_aggregate(d):
    """v1 契约：单文件聚合语义不回归。"""
    write(d, "2026-08-16.jsonl", "".join(FIXTURE))
    agg = aggregate(d)
    assert set(agg) == {"reasoning-depth", "execution-discipline", "infra-health", "diagnosis-root-cause"}, agg
    assert agg["reasoning-depth"]["avg"] == 4.0, agg["reasoning-depth"]
    assert agg["reasoning-depth"]["latest"] == 4.2, agg["reasoning-depth"]
    assert agg["diagnosis-root-cause"]["avg"] == 3.0
    assert agg["execution-discipline"]["pass_rate"] == 0.5, agg["execution-discipline"]
    assert agg["infra-health"]["pass_rate"] == 1.0
    assert "cross-domain-generalization" not in agg, agg  # no-data 不判负、不进聚合
    md = render_markdown(agg)
    assert "reasoning-depth" in md and "4.0" in md and "4.2" in md and "0.5" in md


def test_v2_delta(d):
    """跨 run 判分趋势：latest/prev/delta 按文件序推进。"""
    write(d, "2026-08-16.jsonl", '{"case_id":"lm-001","dimension":"long-task-meta","score":4.35}\n')
    write(d, "2026-08-29.jsonl", '{"case_id":"lm-001","dimension":"long-task-meta","score":4.75}\n')
    agg = aggregate(d)
    b = agg["long-task-meta"]
    assert b["latest"] == 4.75 and b["prev"] == 4.35 and b["delta"] == 0.4, b


def test_v2_load_runs_and_streak(d):
    """load_runs 保留 no-data 审计行；streak 数连续最新优先的 no-data 期数。"""
    write(d, "2026-08-16.jsonl", '{"case_id":"cg-001","dimension":"cg","status":"no-data"}\n')
    write(d, "2026-08-18.jsonl", '{"case_id":"cg-001","dimension":"cg","status":"no-data"}\n')
    write(d, "2026-08-29.jsonl", '{"case_id":"cg-001","dimension":"cg","status":"no-data"}\n')
    runs = load_runs(d)
    assert len(runs) == 3 and all(r.get("status") == "no-data" for _x, r in runs)
    streaks = no_data_streaks(d)
    assert streaks.get("cg-001") == 3, streaks
    write(d, "2026-08-30.jsonl", '{"case_id":"cg-001","dimension":"cg","score":3.8}\n')
    assert no_data_streaks(d) == {}, "出现判分后连续性被打断"


def test_v2_frontmatter_and_experiments(d):
    exp = os.path.join(d, "exp")
    os.mkdir(exp)
    write(exp, "exp-001.md", EXP_CARD.format(deadline="2026-08-01", status="executed"))
    write(exp, "exp-002.md", EXP_BAD)
    cards = load_experiments(exp)
    assert len(cards) == 1, cards  # 坏卡跳过
    c = cards[0]
    assert c["id"] == "exp-001" and c["type"] == "升级" and c["_file"] == "exp-001.md"
    assert parse_frontmatter(os.path.join(exp, "exp-002.md")) is None
    # 到期：open 状态且 deadline ≤ today
    assert len(due_experiments(exp, "2026-08-15")) == 1
    assert due_experiments(exp, "2026-07-31") == []
    write(exp, "exp-003.md", EXP_CARD.format(deadline="2026-08-01", status="verified"))
    assert len(due_experiments(exp, "2026-08-15")) == 1, "verified 不再核销，exp-001 仍是唯一到期卡"
    status, hit = experiment_stats(exp)
    assert status["executed"] == 1 and status["verified"] == 1
    assert hit["升级"] == [1, 2], hit


def test_v2_due_predictions(d):
    write(d, "2026-08-16.jsonl", '{"case_id":"rs-001","dimension":"rd","score":4.4}\n')
    write(d, "2026-08-29.jsonl",
          '{"case_id":"rs-001","dimension":"rd","score":4.4,"prediction":"下轮分差≤±0.5"}\n')
    preds = due_predictions(d)
    assert len(preds) == 1 and preds[0]["case_id"] == "rs-001", preds  # 只取最近 run


def test_v2_alarms_and_render(d):
    exp = os.path.join(d, "exp")
    os.mkdir(exp)
    write(d, "2026-08-16.jsonl", "".join(FIXTURE))  # ex-001 fail → pass_rate 0.5；dr-001 3.0 < 3.5
    write(d, "2026-08-18.jsonl", '{"case_id":"cg-001","dimension":"cg","status":"no-data"}\n')
    write(d, "2026-08-17.jsonl", '{"case_id":"lm-001","dimension":"long-task-meta","score":4.35}\n')
    write(d, "2026-08-19.jsonl", '{"case_id":"lm-001","dimension":"long-task-meta","score":4.75}\n')
    write(exp, "exp-009.md", EXP_CARD.format(deadline="2026-08-01", status="executed"))
    agg = aggregate(d)
    alarm = alarms(agg, d, exp, "2026-08-30")
    joined = "\n".join(alarm)
    assert "execution-discipline" in joined and "0.5" in joined, alarm       # 回归
    assert "diagnosis-root-cause" in joined and "3.0" in joined, alarm       # 跌破通过线
    assert "exp-001" in joined, alarm                                        # 到期卡（以卡内 id 为准）
    md = render_markdown(agg, runs_dir=d, exp_dir=exp, today="2026-08-30")
    for section in ("## 报警", "## 趋势", "## 校准", "## 实验", "exp-001", "+0.40"):
        assert section in md, f"missing {section}"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    with tempfile.TemporaryDirectory() as d:
        for t in tests:
            with tempfile.TemporaryDirectory() as sub:
                t(sub)
    print(f"ALL-PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
