#!/usr/bin/env python3
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from group_scores import aggregate, render_markdown

FIXTURE = [
    '{"case_id":"rs-001","dimension":"reasoning-depth","score":3.8,"evidence_ref":"retro/2026-08-16.md","judge":"user"}\n',
    '{"case_id":"rs-001","dimension":"reasoning-depth","score":4.2,"evidence_ref":"s2","judge":"user"}\n',
    '{"case_id":"ex-001","dimension":"execution-discipline","status":"pass"}\n',
    '{"case_id":"ex-001","dimension":"execution-discipline","status":"fail"}\n',
    '{"case_id":"ih-001","dimension":"infra-health","status":"pass"}\n',
    '{"case_id":"dr-001","dimension":"diagnosis-root-cause","score":3.0,"evidence_ref":"s3","judge":"user"}\n',
]

def main():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "2026-08-16.jsonl"), "w") as fh:
            fh.writelines(FIXTURE)
        agg = aggregate(d)
        assert set(agg) == {"reasoning-depth", "execution-discipline", "infra-health", "diagnosis-root-cause"}, agg
        assert agg["reasoning-depth"]["avg"] == 4.0, agg["reasoning-depth"]
        assert agg["reasoning-depth"]["latest"] == 4.2, agg["reasoning-depth"]
        assert agg["diagnosis-root-cause"]["avg"] == 3.0
        assert agg["execution-discipline"]["pass_rate"] == 0.5, agg["execution-discipline"]
        assert agg["infra-health"]["pass_rate"] == 1.0
        md = render_markdown(agg)
        assert "reasoning-depth" in md and "4.0" in md and "4.2" in md and "0.5" in md
    print("ALL-PASS")

if __name__ == "__main__":
    main()