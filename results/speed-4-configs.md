# Four configurations on the same PC (Strata 0.2.10)

200 ShareGPT requests, one at a time (c=1), seed 0, context 8192, thinking off, MTP drafter. Speeds are recomputed from the engine log (`bench/split_recompute.py`), because vLLM's TTFT is not valid for these servers; "prompt read" is the server-side prompt time and stands in for TTFT. Same 200 requests in every column (47,455 input tokens).

| | Split engine, default | Split engine, `FNX_PF_STAGE_ROWS=8` | Layer split, 2 cards | 1 card |
|---|---|---|---|---|
| Generated tokens / wall time (tok/s) | 23.29 | 35.70 | **40.56** | 32.27 |
| (Input + generated) / wall time (tok/s) | 48.6 | 73.7 | **83.5** | 66.8 |
| Decode, median per request (tok/s) | 57.5 | **58.2** | 48.65 | 36.25 |
| Decode, min–max (requests of 20+ tokens) | 41.1–77.7 | 37.3–79.3 | 27.5–80.6 | 22.5–55.2 |
| Prompt read, median (ms) | 4980 | 2494 | 1050 | **1008** |
| Prompt read, p99 (ms) | 11887 | 3165 | 2313 | **1996** |
| Failed requests | 0 | 0 | 0 | 0 |
| Wall time | 1875 s | 1248 s | **1106 s** | 1374 s |
| Generated tokens (server) | 43,665 | 44,554 | 44,845 | 44,343 |
| Prompt read / decode, total seconds | 1138 / 736 | 505 / 742 | 221 / 884 | 207 / 1166 |
| Drafts accepted / proposed | 25,872 / 49,104 | 26,693 / 50,301 | 28,659 / 81,398 | 28,101 / 81,835 |

Conditions that differ between columns:
- Only the split engine uses `--lookup 15` and `FNX_ARENA=1 FNX_EXPERT_RAM_GIB=20 FNX_POOL_MIN_RESIDENT=384`; 17,502 of the 24,576 routed experts live in RAM (7,453 of them because VRAM was short). The two cards exchange data through pinned host memory (no peer access).
- Draft acceptance is not comparable between the split engine and the stock engine (the "proposed" count may be defined differently; the split engine also uses lookup drafts).
- The generated-token totals differ a little because sampling is not fixed.
- vLLM counted 2–6 requests per run as 0 output tokens; those are empty bodies that the server log shows with a few tokens. The recomputation uses the server log.

Resources (sampled every second on the server): the split engine kept both GPUs at 97–98% utilisation with 8–9% CPU; the layer split ran the GPUs at 43% / 55% and the CPU at about 45%. Minimum free RAM during the run: 22.0 GiB (default), 6.3 GiB (tuned), 0.8 GiB (layer split), 6.4 GiB (1 card). No swap or disk reads in any run.

## Reading
- The tuned split engine has the fastest decode (1.20x the layer split, 1.61x one card) but pays about 1.4 s more per request to read the prompt, because experts that are not resident in VRAM have to cross PCIe. On short ShareGPT answers the layer split is 1.14x faster overall.
- `FNX_PF_STAGE_ROWS=8` is the only difference between the first two columns: 1.53x faster overall; see [stage-rows.md](stage-rows.md).
