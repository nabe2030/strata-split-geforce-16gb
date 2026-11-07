#!/usr/bin/env python3
"""Prompt-read time by prompt length, for comparing FNX_PF_STAGE_ROWS settings.
Sends fresh random-word prompts (so the conversation cache cannot help) of several lengths, 3 times each, max_tokens 6,
and reports the median of the server-side prompt time (`timings.prompt_ms`). Run once per server start, then change the setting.
Usage: stage_rows_probe.py [--url http://HOST:8095] [--model NAME] [--sizes 40,190,770,3400] [--reps 3]
Also read `sfnx: slot 0: prompt N tokens = ... read in X ms` in the engine log; with FNX_PF_TIMING=1 it prints the time per prefill pass."""
import argparse
import json
import random
import statistics
import time
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:8095"); ap.add_argument("--model", default="flash-next-iq3s-split")
ap.add_argument("--sizes", default="40,190,770,3400"); ap.add_argument("--reps", type=int, default=3)
a = ap.parse_args()
rnd = random.Random(int(time.time()))
for n in map(int, a.sizes.split(",")):
    ms = []
    for _ in range(a.reps):
        text = " ".join(f"w{rnd.randint(0, 99999)}" for _ in range(n))
        d = {"model": a.model, "messages": [{"role": "user", "content": text}], "max_tokens": 6, "temperature": 0, "chat_template_kwargs": {"enable_thinking": False}}
        r = urllib.request.Request(a.url + "/v1/chat/completions", json.dumps(d).encode(), {"content-type": "application/json"})
        j = json.load(urllib.request.urlopen(r, timeout=600))
        ms.append(j["timings"]["prompt_ms"])
    print(f"~{n} words: prompt_tokens={j['usage']['prompt_tokens']} read ms median {statistics.median(ms):.0f} (all: {[round(x) for x in ms]})", flush=True)
