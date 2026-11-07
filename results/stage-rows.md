# `FNX_PF_STAGE_ROWS`: prompt-read time by prompt length

When most routed experts live in RAM, the default `FNX_PF_STAGE_ROWS=2048` reads them in place over PCIe for any prompt shorter than 2048 tokens. On 2x16 GB cards with about 70% of the experts in RAM that is slow; staging them into VRAM first costs a fixed ~1.6 s per card and was cheaper at every prompt length we measured below 2048 tokens (48 and up).

Median server-side prompt-read time in ms (`sfnx: ... read in X ms`), 3 requests per cell, fresh random prompts (no cache reuse), context 8192, cache 1024 MiB, `--batch 1`, MTP, `max_tokens` 6, `FNX_PF_TIMING=1`. Tuned settings otherwise (`FNX_EXPERT_RAM_GIB=20` etc.).

| `FNX_PF_STAGE_ROWS` | 48 tokens | 200 | 780 | 3.4K |
|---|---|---|---|---|
| default (2048), 0.2.11 | 2645 | 3725 | 6087 | 4184 |
| default (2048), 0.2.10 | 2965 | 3867 | 6021 | ≈4400 (estimated; same path as 2.7K) |
| **8**, 0.2.11 | **1948** | **2015** | **2396** | 4215 |
| 8, 0.2.10 | 2079 | 2082 | 2434 | 4337 |
| 64, 0.2.11 | 2683 | 2016 | 2396 | 4188 |
| 256, 0.2.11 | 2525 | 3958 | 2410 | 4227 |

(The 0.2.10 rows are the mean of two runs with `FNX_EXPERT_RAM_GIB=24`.) With 64 or 256 a prompt shorter than the threshold is read in place, a longer one is staged: 200 tokens take 2.0 s with 64 and 4.0 s with 256. Prompts of 3.4K tokens are staged either way, so there is no difference.

Per-pass breakdown (`FNX_PF_TIMING=1`, ms, first pass = N−6 rows / last 6-row pass):

| Tokens | default: first / last | 8: first / last |
|---|---|---|
| 48 | 2225 / 362 (in place) | 1561 / 329 (first staged) |
| 200 | 3384 / 281 | 1660 / 289 |
| 780 | 5739 / 272 | 2060 / 275 |
| 3.4K | 3836 / 259 (first staged) | 3851 / 254 |

- Only the first pass changes. Reading in place grows from 2.2 s to 5.7 s with the row count; staging is a fixed ~1.6 s plus compute. The last 6-row pass is read in place either way (0.26–0.36 s). `FNX_PF_STAGE_ROWS=0` (stage every pass) is worse for short prompts because the 6-row pass then also pays the full ~1.4 s staging.
- The first request after start-up also runs a separate 1100-row warm-up pass (2.1 s with 8, 7.1 s with the default).
- Staged volume: 16.4–16.8 GiB per card per first pass, with 0.5–1.0 GiB still read in place (what does not fit the 384 MiB `FNX_PF_STAGE_MIB` staging area of one layer). One staging pass is limited by PCIe: about 13.5 GB/s measured.
- The decision is one comparison, `tokens.size() >= stage_rows` in `Engine::prefill` (`src/split/src/prefill.cu`), unchanged between 0.2.10 and 0.2.11. It does not look at how many experts are resident or at the PCIe speed. A proposal for an automatic threshold is in [Niko1221/Strata#5440](https://github.com/Niko1221/Strata/issues/5440).
