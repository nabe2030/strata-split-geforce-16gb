#!/usr/bin/env python3
"""Recompute the c=1 ShareGPT numbers from the split engine's log (vllm's own TTFT is not valid for this server).
Usage: split_recompute.py OUT_DIR   (needs c1.json from vllm bench and engine_requests.txt with the 200 `sfnx: slot 0: prompt ...` lines)
Line format: prompt N tokens = R reused + X read in T ms, G generated in Y ms (S tok/s)[, drafts A of B ...]"""
import json
import re
import statistics as st
import sys

d = sys.argv[1]
R = re.compile(r"prompt (\d+) tokens = (\d+) reused \+ (\d+) read in (\d+) ms, (\d+) generated in (\d+) ms \(([\d.]+) tok/s\)(?:, drafts (\d+) of (\d+))?")
S = [tuple(float(x) if x and '.' in x else (int(x) if x else 0) for x in m.groups()) for m in map(R.search, open(d + "/engine_requests.txt")) if m]


def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(round(p / 100 * (len(v) - 1))))]


c = json.load(open(d + "/c1.json"))
seg = S[len(S) - 200:]
delta = sorted({int(s[0]) - i for s, i in zip(seg, c["input_lens"])})
pin = sum(s[0] for s in seg); gen = sum(s[4] for s in seg); dur = c["duration"]
dec = sum(s[5] for s in seg) / 1000; prm = sum(s[3] for s in seg) / 1000
ok = [s for s in seg if s[4] >= 20]
da = sum(s[7] for s in seg); db = sum(s[8] for s in seg)
r = {
    "requests": len(seg),
    "server_minus_client_input_length": delta,
    "wall_s": round(dur, 1),
    "server_input_tokens": pin,
    "server_generated_tokens": gen,
    "output_tok_s (generated / wall)": round(gen / dur, 2),
    "total_tok_s ((input + generated) / wall)": round((pin + gen) / dur, 2),
    "decode_tok_s (generated / decode seconds)": round(gen / dec, 2),
    "per_request_decode_tok_s_median (>=20 tokens)": round(st.median(s[6] for s in ok), 2),
    "prompt_read_ms_median": st.median(s[3] for s in seg),
    "prompt_read_ms_p99": pct([s[3] for s in seg], 99),
    "prompt_read_total_s": round(prm, 1),
    "decode_total_s": round(dec, 1),
    "drafts_accepted_proposed": [int(da), int(db)],
    "draft_acceptance": round(da / db, 3) if db else None,
    "failed": c["failed"],
}
json.dump(r, open(d + "/split_recomputed.json", "w"), indent=1)
for k, v in r.items():
    print(k, ":", v)
