#!/usr/bin/env python3
"""Estimate cost of the main 'fable' model usage in one Claude Code session transcript.

Read-only on the transcript. Weighted tokens:
    W = input + 1.25*cache_creation + 0.1*cache_read + 5*output
Calibrated against a user-stated ~$24 spend at the calibration user message.
"""
import json
import sys
from datetime import datetime

TRANSCRIPT = ("/home/johnjose/.claude/projects/-home-johnjose-cos/"
              "1f3aff88-8dc6-4a87-a2cd-ecd712745d5d.jsonl")
CAL_PHRASE = "John wants a SCOPING phase for a head-to-head"
CAL_DOLLARS = 24.0
MODEL_SUBSTR = "fable"


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def text_of(obj):
    """Concatenate all string leaves of a message's content (for phrase search)."""
    out = []
    stack = [obj]
    while stack:
        x = stack.pop()
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            stack.extend(x.values())
        elif isinstance(x, list):
            stack.extend(x)
    return "\n".join(out)


def main():
    cal_ts = None
    cal_found = False
    by_id = {}          # message.id -> record (last occurrence wins)
    skipped_sidechain = 0
    fable_lines = 0
    models_seen = set()

    with open(TRANSCRIPT, encoding="utf-8") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue

            # Calibration point: first user line containing the phrase.
            if (not cal_found and o.get("type") == "user"
                    and CAL_PHRASE in text_of(o.get("message", o))):
                cal_found = True
                cal_ts = parse_ts(o["timestamp"])

            if o.get("type") != "assistant":
                continue
            msg = o.get("message")
            if not isinstance(msg, dict):
                continue
            model = str(msg.get("model", ""))
            usage = msg.get("usage")
            if not isinstance(usage, dict) or MODEL_SUBSTR not in model.lower():
                continue
            models_seen.add(model)
            fable_lines += 1
            if o.get("isSidechain") is True:
                skipped_sidechain += 1
                continue

            mid = msg.get("id")
            if mid is None:
                continue
            by_id[mid] = {
                "ts": parse_ts(o["timestamp"]),
                "in": int(usage.get("input_tokens") or 0),
                "cc": int(usage.get("cache_creation_input_tokens") or 0),
                "cr": int(usage.get("cache_read_input_tokens") or 0),
                "out": int(usage.get("output_tokens") or 0),
            }

    def w(r):
        return r["in"] + 1.25 * r["cc"] + 0.1 * r["cr"] + 5 * r["out"]

    recs = list(by_id.values())
    before = [r for r in recs if cal_ts is not None and r["ts"] < cal_ts]

    def sums(rs):
        return (sum(r["in"] for r in rs), sum(r["cc"] for r in rs),
                sum(r["cr"] for r in rs), sum(r["out"] for r in rs))

    s_cal = sums(before)
    s_tot = sums(recs)
    w_cal = sum(w(r) for r in before)
    w_tot = sum(w(r) for r in recs)
    dollars_per_w = CAL_DOLLARS / w_cal if w_cal else float("nan")
    est = dollars_per_w * w_tot
    last_ts = max((r["ts"] for r in recs), default=None)

    print(f"transcript: {TRANSCRIPT}")
    print(f"models matching '{MODEL_SUBSTR}': {sorted(models_seen)}")
    print(f"fable assistant lines with usage: {fable_lines}")
    print(f"sidechain fable lines skipped: {skipped_sidechain}")
    print(f"fable messages (unique message.id, non-sidechain): {len(recs)}")
    if cal_found:
        print(f"calibration line found at: {cal_ts.isoformat()}")
    else:
        print("calibration line NOT found; W_cal = 0, estimate unavailable")
    print(f"before calibration  input={s_cal[0]} cache_creation={s_cal[1]} "
          f"cache_read={s_cal[2]} output={s_cal[3]}")
    print(f"total               input={s_tot[0]} cache_creation={s_tot[1]} "
          f"cache_read={s_tot[2]} output={s_tot[3]}")
    print(f"W_cal = {w_cal:.1f}")
    print(f"W_total = {w_tot:.1f}")
    print(f"dollars_per_W = {dollars_per_w:.6g}")
    print(f"estimated cost now: ${est:.2f}")
    print(f"last counted message timestamp: "
          f"{last_ts.isoformat() if last_ts else 'none'}")


if __name__ == "__main__":
    sys.exit(main())
