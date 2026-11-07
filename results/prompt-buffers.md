# Prompt-path buffers and expert RAM on 16 GB cards (0.2.11)

Question: does a larger prompt-read buffer make long fresh prompts faster on 16 GB cards, as it does on 48 GB cards? Answer: no. 256K server, conversation cache 16 GiB, no reuse, mean of 2 runs per cell. Read seconds, and in brackets the decode tok/s of a 300-token generation right after (fixed prompt; drafts acceptance moves it by about ±5 tok/s).

| Configuration (rows x chunks per pass; changes from default) | 32K | 100K | 200K | Start |
|---|---|---|---|---|
| **A: 4096 x 2 (automatic choice on these cards)** | **25.0 s (58.0)** | **74.7 (59.1)** | **150.7 (53.6)** | ok |
| 2048 x 4 (`FNX_PF_ROWS=2048 FNX_PF_PASS=4`) | 27.1 (61.5) | 74.2 (61.0) | 155.2 (53.4) | ok |
| 4096 x 4 | 27.5 (52.5) | 75.7 (54.0) | 164.1 (47.6) | ok |
| 4096 x 1 | 32.9 (57.0) | 97.1 (57.2) | 202.8 (54.6) | ok |
| 8192 x 2 / x 4 / x 1 | — | — | — | **fails** (out of memory) |
| 8192 x 2 plus `FNX_ARENA_RESERVE_MIB=2560` | — | — | — | fails, same message |
| 8192 x 2 plus `FNX_EXPERT_RAM_GIB=24` | 29.5 (47.5) | 93.1 (45.8) | 202.8 (42.1) | ok |
| 8192 x 4 plus `FNX_EXPERT_RAM_GIB=28` | 36.1 (40.5) | 111.9 (40.6) | 260.1 (34.1) | ok |

Start-up log of each configuration that started:

| Configuration | Experts in RAM | Arena slots per card | K/V pages: own → max | Free VRAM after start |
|---|---|---|---|---|
| A 4096 x 2 | 17,047 | 3,328 | 432 → 2,385 | 279 / 287 MiB |
| 2048 x 4 | 16,672 | 3,496 | 413 → 2,475 | 277 / 285 |
| 4096 x 4 | 17,643 | 3,074 | 460 → 2,248 | 279 / 287 |
| 4096 x 1 | 16,749 | 3,461 | 417 → 2,456 | 279 / 287 |
| 8192 x 2, RAM 24 | 19,040 | 2,472 | 483 → 1,880 | 275 / 283 |
| 8192 x 4, RAM 28 | 20,133 | 1,958 | 468 → 1,531 | 273 / 281 |

- Setting `FNX_PF_ROWS` by hand disables the automatic choice (which compares the buffer with free VRAM), so a value that is too large does not shrink by itself. The 8192-row starts stop with `cudaMalloc of 80 MiB on card 0: out of memory (73 MiB free; the prompt path holds 1762 MiB there already)`.
- The prompt buffers are allocated right after the first expert placement, before the arena's "VRAM short, move more of the coldest experts to RAM" correction, so `FNX_ARENA_RESERVE_MIB` does not help. About 1.8 GiB is free at that point, enough for 4096 x 4 (1.7 GiB) but not 8192 rows.
- The only way to start 8192 rows is to place more experts in RAM (`FNX_EXPERT_RAM_GIB` 24 or 28), which cuts the GPU expert slots from 3,328 to 2,472 and 1,958. That loses more than the larger buffer gains: reads are 35–73% slower and decode drops.
- A is the best configuration measured; none is more than 5% faster than it.
