#!/usr/bin/env python3
"""Long-context probe: 3 short requests, then one fresh long prompt, then a short follow-up turn on the same conversation
(which should hit the conversation cache). Prints usage and wall time. The text is random words, so it measures reading speed
and decode after a long context, not answer quality.
Usage: long_prompt_probe.py TAG WORDS [--url http://HOST:8095] [--model NAME]
  WORDS ~ prompt length in words (about 1 token per word here): 49000 for 64K, 98000 for 128K, 200000 for a 256K server."""
import argparse
import json
import random
import time
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("tag"); ap.add_argument("words", type=int)
ap.add_argument("--url", default="http://127.0.0.1:8095"); ap.add_argument("--model", default="flash-next-iq3s-split")
a = ap.parse_args()
vocab = ("the quick brown fox jumps over a lazy dog while engineers measure latency of expert layers on graphics cards in a quiet laboratory near the river " * 20000).split()


def chat(msgs, max_tokens):
    d = {"model": a.model, "messages": msgs, "max_tokens": max_tokens, "temperature": 0, "chat_template_kwargs": {"enable_thinking": False}}
    t = time.time()
    r = urllib.request.Request(a.url + "/v1/chat/completions", json.dumps(d).encode(), {"content-type": "application/json"})
    j = json.load(urllib.request.urlopen(r, timeout=3000))
    return j, time.time() - t


def body(n, seed):
    random.seed(seed)
    return " ".join(random.choice(vocab) for _ in range(n))


for k in range(3):
    j, w = chat([{"role": "user", "content": f"[{a.tag}s{k}] " + body(30, k) + "\n\nWrite a short story about a fox, about 150 words."}], 150)
    print("short", k, j["usage"], j.get("timings", {}), "wall %.1f" % w, flush=True)
m = [{"role": "user", "content": f"[{a.tag}L] Text:\n" + body(a.words, "L" + a.tag) + "\n\nSummarize in about 100 words what kind of text this is."}]
j, w = chat(m, 150)
print("long", j["usage"], j.get("timings", {}), "wall %.1f" % w, flush=True)
m += [{"role": "assistant", "content": j["choices"][0]["message"]["content"]}, {"role": "user", "content": "Now say it again in one sentence."}]
j, w = chat(m, 60)
print("followup", j["usage"], j.get("timings", {}), "wall %.1f" % w, flush=True)
