# Long outputs (`max_tokens` 1024), split engine vs layer split (Strata 0.2.10)

ShareGPT, 200 requests, c=1, seed 0, `--sharegpt-output-len 1024`, context 8192, thinking off. Split engine = tuned (`FNX_PF_STAGE_ROWS=8`). Both columns use the same 200 prompts (48,383 input tokens); this is a different prompt set from the short-output run because the option changes vLLM's dataset filter.

| | Split engine | Layer split, 2 cards |
|---|---|---|
| Generated tokens / wall time (tok/s) | **49.44** | 49.33 |
| (Input + generated) / wall time (tok/s) | 65.67 | 65.77 |
| Decode, median per request (tok/s) | **58.85** | 51.9 |
| Decode, min–max (requests of 20+ tokens) | 42.0–93.8 | 21.1–99.3 |
| Prompt read, median / p99 (ms) | 2541 / 3242 | **1112 / 2326** |
| Requests cut at 1024 generated tokens | 81 | 79 |
| Failed requests | 0 | 0 |
| Wall time | 2980 s | **2942 s** |
| Generated tokens (server), total / mean | 147,299 / 736 | 145,112 / 726 |
| Prompt read / decode, total seconds | 515 / 2464 | 230 / 2711 |
| Drafts accepted / proposed | 90,921 / 168,848 | 94,780 / 253,326 |

(The cut-at-1024 count is "generated tokens reached 1024"; the engine log has no finish reason.)

## Break-even
The split engine reads the prompt about 1.43 s slower per request (2.54 − 1.11 s) and decodes about 0.0020 s per token faster (1/53.52 − 1/59.78 s). The two cancel at about **730 output tokens**, which is the mean of this run (736). Estimate from these numbers; outputs of 2048 tokens or more were not measured, and prompts of 8K tokens or more change the prompt-read side.
