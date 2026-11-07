# Context length: 64K, 128K, 256K

Split engine with the tuned settings (`FNX_ARENA=1 FNX_EXPERT_RAM_GIB=20 FNX_POOL_MIN_RESIDENT=384 FNX_PF_STAGE_ROWS=8`), 0.2.10, `--batch 1`, MTP, only `--max-context` changed. The 8K column is the earlier tuning run. Input is random words (reading speed and decode after a long context, not answer quality).

| | 8K | 64K | 128K | 256K |
|---|---|---|---|---|
| Starts | yes | yes | yes | **yes** |
| Load time until healthy | ~95 s | 101 s | 95 s | 95 s |
| Routed experts in RAM (of 24,576; short because VRAM was short) | 17,502 (7,453) | 17,502 (7,453) | 17,504 (7,455) | 17,506 (7,457) |
| Free VRAM per card after load | 809 / 817 MiB | 265 / 273 | 265 / 273 | 263 / 271 |
| K/V pool positions at start | 366,336 | 438,336 | 437,952 | 437,760 |
| Short prompt (~65 tokens) read | ~2.0 s | 2.40–2.47 s | 2.36–2.50 s | 2.43–2.47 s |
| Short decode, 150 tokens, 3 runs (tok/s) | 41.9 (1 run) | 54.4 / 59.1 / 67.0 | 58.4 / 60.1 / 61.4 | 55.4 / 62.3 / 64.6 |
| Fresh long prompt | — | 49,040 tok in **37.0 s** (1,325 tok/s) | 98,041 tok in **72.4 s** (1,354 tok/s) | 200,040 tok in **150.3 s** (1,331 tok/s) |
| Decode right after the long prompt | — | 54.1 tok/s | 51.8 | **49.1** |
| Follow-up turn (22 new tokens) | — | 2.15 s (49,162 reused) | 2.06 s (98,160 reused) | 2.37 s (200,152 reused) |
| Max GPU temperature | — | 67 / 61 °C | 71 / 69 | 71 / 68 |
| Min MemAvailable | — | 33.4 GB | 32.9 GB | 34.0 GB |

- Expert residency does not change with `--max-context`. The K/V pool starts at its own 453 pages and, as the context fills, the arena lends expert slots to it (`K/V pool 453 -> 1089 pages, slots lent 980`, about 0.9 GiB per card at ~200K tokens), up to 2,280 pages (437,760 positions). So a long context costs decode speed only once it is used: 55–65 tok/s for short prompts at every setting, 49 tok/s after a fresh 200K-token prompt.
- The conversation cache held the 200K-token conversation in `--conversation-cache-mib 1024` (int8 K/V, about 5 KiB per position).
- One conversation only; switching between sessions and cache eviction were not measured. Answer quality at long context was not examined.
