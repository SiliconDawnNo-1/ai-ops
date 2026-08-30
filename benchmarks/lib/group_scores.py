#!/usr/bin/env python3
"""Aggregate benchmark ledger runs + experiment cards into trends; emit SCORES.md.

v2（2026-08-30 spec §4）：在 v1 聚合语义之上增加——
- 趋势：judged 最新分相对上一 run 的变化量 Δ
- 报警：脚本通过率 <1.0、judged 跌破通过线、no-data 连续 ≥3 期
- 校准：上轮 prediction 待核验清单、judge 标签分布
- 实验：experiment cards 状态计数、到期核销队列、type 命中率

纯标准库；`python3 group_scores.py`（聚合）与
`python3 group_scores.py due`（到期核验队列，供 /benchmark 步骤 0 消费）。
"""
import glob
import json
import os
import sys
from collections import Counter
from datetime import date

PASS_LINE = 3.5           # judged 通过线（v1 spec §4）
NO_DATA_STREAK_MAX = 3    # no-data 连续期数报警线（v2 spec D4）
OPEN_STATUS = ("approved", "executed")  # 需要核销的实验卡状态


def _dimension(record):
    dim = record.get("dimension")
    return dim if dim else record.get("case_id", "?").split("-")[0]


def load_runs(runs_dir):
    """Return [(date, record), ...] across runs/*.jsonl, sorted by date then file order."""
    out = []
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.jsonl"))):
        date_str = os.path.basename(f)[: -len(".jsonl")]
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"warn: skip malformed line in {f}: {exc}", file=sys.stderr)
                    continue
                out.append((date_str, rec))
    return out


def aggregate(runs_dir):
    """Return {dimension: {runs, avg, latest, prev, delta, pass_rate}} from runs/*.jsonl.

    v1 语义不变：no-data 不判负、不进聚合；scripted 通过率 = pass 数 / scripted 记录数。
    v2 增量：prev/delta 按 run 对 run 比较（latest run 均值 vs 上一 scored run 均值）。
    """
    data = {}
    for date_str, rec in load_runs(runs_dir):
        if rec.get("status") == "no-data":
            continue  # 无产物不判负，只留账本审计，不进聚合
        dim = _dimension(rec)
        by_date = data.setdefault(dim, {}).setdefault(date_str, {"scores": [], "passes": 0, "scripted": 0})
        if rec.get("score") is not None:
            by_date["scores"].append(float(rec["score"]))
        else:
            by_date["scripted"] += 1
            if rec.get("status") == "pass":
                by_date["passes"] += 1
    out = {}
    for dim, days_by_date in data.items():
        days = sorted(days_by_date)
        scores = [s for d in days for s in days_by_date[d]["scores"]]
        runs = sum(len(day["scores"]) + day["scripted"] for day in days_by_date.values())
        judged = sum(len(day["scores"]) for day in days_by_date.values())
        passes = sum(day["passes"] for day in days_by_date.values())
        scripted = runs - judged
        latest = scores[-1] if scores else None
        prev = None
        scored_days = [d for d in days if days_by_date[d]["scores"]]
        if len(scored_days) >= 2:
            prev_scores = days_by_date[scored_days[-2]]["scores"]
            prev = sum(prev_scores) / len(prev_scores)
        out[dim] = {
            "runs": runs,
            "avg": round(sum(scores) / len(scores), 2) if scores else None,
            "latest": latest,
            "prev": round(prev, 2) if prev is not None else None,
            "delta": round(latest - prev, 2) if latest is not None and prev is not None else None,
            "pass_rate": round(passes / scripted, 2) if scripted else None,
        }
    return out


def parse_frontmatter(path):
    """Parse a markdown file's `---` frontmatter into a flat {key: value} dict (无 PyYAML)."""
    try:
        with open(path) as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return None  # 没有闭合的 ---，视为坏卡


def load_experiments(exp_dir):
    """Return experiment cards (exp-*.md) as dicts, sorted by id. Bad cards are skipped."""
    cards = []
    for f in sorted(glob.glob(os.path.join(exp_dir, "exp-*.md"))):
        fields = parse_frontmatter(f)
        if fields:
            fields["_file"] = os.path.basename(f)
            cards.append(fields)
    return cards


def due_predictions(runs_dir):
    """Return [{case_id, prediction, date}] from the most recent run（核验上轮预测）."""
    runs = load_runs(runs_dir)
    if not runs:
        return []
    latest_date = max(d for d, _ in runs)
    return [
        {"case_id": rec.get("case_id", "?"), "prediction": rec["prediction"], "date": d}
        for d, rec in runs
        if d == latest_date and rec.get("prediction")
    ]


def due_experiments(exp_dir, today):
    """Return cards needing verification: status open AND deadline <= today."""
    return [
        c for c in load_experiments(exp_dir)
        if c.get("status") in OPEN_STATUS and c.get("deadline", "9999-12-31") <= today
    ]


def experiment_stats(exp_dir):
    """Return (status Counter, {type: [verified, total]}) over all cards."""
    cards = load_experiments(exp_dir)
    status = Counter(c.get("status", "?") for c in cards)
    hit = {}
    for c in cards:
        t = c.get("type", "?")
        slot = hit.setdefault(t, [0, 0])
        slot[1] += 1
        if c.get("status") == "verified":
            slot[0] += 1
    return status, hit


def no_data_streaks(runs_dir):
    """Return {case_id: streak} — 自最新 run 起算，no-data 连续出现的期数。

    最新期有判分或缺席 → 该 case 不在 streak；往旧每连续一期 no-data 计 1。
    """
    files = sorted(glob.glob(os.path.join(runs_dir, "*.jsonl")), reverse=True)
    streaks = {}
    for i, f in enumerate(files):
        ids = set()
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("status") == "no-data":
                    ids.add(rec.get("case_id", "?"))
        if i == 0:
            streaks = {case: 1 for case in ids}  # 起点必须是最新一期
        else:
            for case in list(streaks):
                if case in ids:
                    streaks[case] += 1
                else:
                    del streaks[case]  # 连续性终止
    return streaks


def alarms(agg, runs_dir, exp_dir=None, today=None):
    """Return alarm lines: 回归、跌破通过线、no-data 连续期、到期实验卡."""
    out = []
    for dim, b in sorted(agg.items()):
        if b["pass_rate"] is not None and b["pass_rate"] < 1.0:
            out.append(f"⚠ {dim} 脚本通过率 {b['pass_rate']} < 1.0，存在回归待追")
        if b["latest"] is not None and b["latest"] < PASS_LINE:
            out.append(f"⚠ {dim} 最新分 {b['latest']} < 通过线 {PASS_LINE}")
    for case, streak in sorted(no_data_streaks(runs_dir).items()):
        if streak >= NO_DATA_STREAK_MAX:
            out.append(f"⚠ {case} no-data 连续 {streak} 期 → /evolve 必须出样任务或退休该案例")
    if exp_dir and today:
        for c in due_experiments(exp_dir, today):
            out.append(f"⏰ 实验卡 {c.get('id', c.get('_file', '?'))} 到期待核销（deadline {c.get('deadline')}）：{c.get('title', '')}")
    return out


def render_markdown(agg, title="SCORES.md", runs_dir=None, exp_dir=None, today=None):
    """Render SCORES.md v2：报警 → 趋势(+Δ) → 校准 → 实验。只传 agg 时仍兼容 v1 主表。"""
    lines = [f"# {title}", "", f"聚合维度数：{len(agg)}", ""]

    alarm_lines = alarms(agg, runs_dir, exp_dir, today) if runs_dir else []
    lines += ["## 报警", ""]
    lines += [f"- {a}" for a in alarm_lines] if alarm_lines else ["- 无"]

    lines += ["", "## 趋势", "",
              "| 维度 | 运行次数 | judged平均分 | 最新分 | Δ上轮 | 脚本通过率 |",
              "|---|---|---|---|---|---|"]
    for dim in sorted(agg):
        b = agg[dim]
        delta = f"{b['delta']:+.2f}" if b.get("delta") is not None else "—"
        lines.append(
            f"| {dim} | {b['runs']} | {b['avg'] if b['avg'] is not None else '—'} | "
            f"{b['latest'] if b['latest'] is not None else '—'} | {delta} | "
            f"{b['pass_rate'] if b['pass_rate'] is not None else '—'} |")

    if runs_dir:
        preds = due_predictions(runs_dir)
        labels = Counter(rec.get("judge") for _d, rec in load_runs(runs_dir)
                         if rec.get("score") is not None and rec.get("judge"))
        lines += ["", "## 校准", "", f"- 上轮 prediction 待核验：{len(preds)} 条"]
        lines += [f"  - {p['case_id']}: {p['prediction']}" for p in preds]
        if labels:
            dist = " / ".join(f"{k} {v}" for k, v in sorted(labels.items()))
            lines.append(f"- judge 标签分布：{dist}")

    if exp_dir:
        status, hit = experiment_stats(exp_dir)
        lines += ["", "## 实验", ""]
        summary = f"- 卡片总数 {sum(status.values())}"
        if status:
            summary += " ｜ " + " ｜ ".join(f"{k} {v}" for k, v in sorted(status.items()))
        lines.append(summary)
        for t, (ok, n) in sorted(hit.items()):
            lines.append(f"- type 命中率：{t} {ok}/{n}")
    return "\n".join(lines) + "\n"


def _repo_paths(runs_dir):
    """Infer (exp_dir,) from a runs dir laid out as benchmarks/ledger/runs."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(runs_dir)))  # benchmarks/
    return os.path.join(root, "experiments")


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "due":
        runs_dir = argv[1] if len(argv) > 1 else os.path.expanduser(
            "~/Desktop/code/ai-ops/benchmarks/ledger/runs")
        exp_dir = argv[2] if len(argv) > 2 else _repo_paths(runs_dir)
        today = argv[3] if len(argv) > 3 else date.today().isoformat()
        print("== 到期核验队列（/benchmark 步骤0）==")
        preds = due_predictions(runs_dir)
        print(f"predictions（最近 run 待核验）：{len(preds)}")
        for p in preds:
            print(f"  - {p['case_id']}: {p['prediction']}")
        due = due_experiments(exp_dir, today)
        print(f"experiments（到期卡）：{len(due)}")
        for c in due:
            print(f"  - {c.get('id', '?')} [{c.get('status')}] deadline={c.get('deadline')} {c.get('title', '')}")
        return

    root = os.path.expanduser("~/Desktop/code/ai-ops/benchmarks")
    runs = argv[0] if argv else os.path.join(root, "ledger", "runs")
    out = argv[1] if len(argv) > 1 else os.path.join(root, "ledger", "SCORES.md")
    exp_dir = argv[2] if len(argv) > 2 else _repo_paths(runs)
    agg = aggregate(runs)
    with open(out, "w") as fh:
        fh.write(render_markdown(agg, runs_dir=runs, exp_dir=exp_dir, today=date.today().isoformat()))
    for dim, b in sorted(agg.items()):
        print(f"[{dim}] runs={b['runs']} avg={b['avg']} latest={b['latest']} "
              f"delta={b['delta']} pass_rate={b['pass_rate']}")


if __name__ == "__main__":
    main()
