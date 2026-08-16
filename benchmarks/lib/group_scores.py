#!/usr/bin/env python3
"""Aggregate benchmark ledger runs into per-dimension trends; emit SCORES.md."""
import glob, json, os, sys

def _dimension(record):
    dim = record.get("dimension")
    return dim if dim else record.get("case_id", "?").split("-")[0]

def aggregate(runs_dir):
    """Return {dimension: {runs, avg, latest, pass_rate}} from runs/*.jsonl."""
    data = {}
    for f in sorted(glob.glob(os.path.join(runs_dir, "*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                dim = _dimension(rec)
                bucket = data.setdefault(dim, {"runs": 0, "scores": [], "passes": 0, "judged": 0})
                bucket["runs"] += 1
                if rec.get("score") is not None:
                    bucket["scores"].append(float(rec["score"]))
                    bucket["judged"] += 1
                elif rec.get("status") == "pass":
                    bucket["passes"] += 1
    out = {}
    for dim, b in data.items():
        scripted = b["runs"] - b["judged"]
        out[dim] = {
            "runs": b["runs"],
            "avg": round(sum(b["scores"]) / len(b["scores"]), 2) if b["scores"] else None,
            "latest": b["scores"][-1] if b["scores"] else None,
            "pass_rate": round(b["passes"] / scripted, 2) if scripted else None,
        }
    return out

def render_markdown(agg, title="SCORES.md"):
    lines = [f"# {title}", "", f"聚合维度数：{len(agg)}", "",
             "| 维度 | 运行次数 | judged平均分 | 最新分 | 脚本通过率 |",
             "|---|---|---|---|---|"]
    for dim in sorted(agg):
        b = agg[dim]
        lines.append(f"| {dim} | {b['runs']} | {b['avg'] if b['avg'] is not None else '—'} | "
                     f"{b['latest'] if b['latest'] is not None else '—'} | {b['pass_rate'] if b['pass_rate'] is not None else '—'} |")
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    root = os.path.expanduser("~/Desktop/code/ai-ops/benchmarks")
    runs = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "ledger", "runs")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "ledger", "SCORES.md")
    agg = aggregate(runs)
    with open(out, "w") as fh:
        fh.write(render_markdown(agg))
    for dim, b in sorted(agg.items()):
        print(f"[{dim}] runs={b['runs']} avg={b['avg']} latest={b['latest']} pass_rate={b['pass_rate']}")