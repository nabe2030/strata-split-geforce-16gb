# Measurement scripts

All take the server address as an argument or environment variable (the examples use `127.0.0.1:8095`). The split engine logs one line per request; the scripts recompute speeds from that log because vLLM's own TTFT is not meaningful for this server:

```
sfnx: slot 0: prompt 19 tokens = 0 reused + 19 read in 1822 ms, 7 generated in 265 ms (26.5 tok/s), drafts 2 of 8, 5 rounds (...)
```

| File | What it does |
|---|---|
| `sharegpt_c1.sh` | ShareGPT, 200 requests, one at a time, seed 0, thinking off (`vllm bench serve` in a container); `LONG=1` sets `max_tokens` 1024. Cuts the 200 log lines out of the engine log and calls `split_recompute.py`. |
| `split_recompute.py` | Output tok/s (generated / wall), decode tok/s, prompt-read median and p99, draft acceptance, from the engine log. |
| `jamcqa_resume.py` | JamC-QA v1.0 test (2,309 questions), 3-shot, temperature 0, resumable (`pip install datasets httpx`). |
| `mcnemar.py` | Exact McNemar test between two JamC-QA runs. |
| `long_prompt_probe.py` | 64K / 128K / 256K probe: short requests, one fresh long prompt, a follow-up turn on the conversation cache. |
| `stage_rows_probe.py` | Prompt-read time by prompt length, to compare `FNX_PF_STAGE_ROWS` settings. |

Notes on what the numbers mean: each configuration was measured once; the server counts 12 more prompt tokens than the client (chat template), which is how the 200 log lines are located; `max_tokens` 1024 changes the vLLM sampling filter, so the "long" run uses a different set of 200 prompts than the "short" run.
