# Results

Hardware and software are described in the top-level README. Every number is one run on one machine (2x RTX 4060 Ti 16 GB, 128 GB RAM, PCIe 4.0 x8 per card, no P2P), Qwen3.8-Flash-Next GSQ-RCO IQ3_S, MTP drafter, thinking off, measured 2026-11-04 to 2026-11-07. Repeat-to-repeat variance was not measured. "Split engine" is Strata's all-cards split engine built from the sources in `patches/` and `build/`; "layer split" is the stock `strata` 0.1.56 (the 0.2.10 release) with the model split in layers over the same two cards.

| File | Contents |
|---|---|
| [speed-4-configs.md](speed-4-configs.md) | ShareGPT, 200 requests, c=1: split engine (default and tuned), layer split on 2 cards, 1 card |
| [long-outputs.md](long-outputs.md) | the same with `max_tokens` 1024, and the break-even output length |
| [jamcqa.md](jamcqa.md) | JamC-QA accuracy, split engine vs layer split |
| [context-256k.md](context-256k.md) | 64K / 128K / 256K context |
| [0.2.11-comparison.md](0.2.11-comparison.md) | Strata 0.2.10 vs 0.2.11 on the split engine |
| [prompt-buffers.md](prompt-buffers.md) | prompt-path buffer sizes and expert-RAM settings on 16 GB cards |
| [stage-rows.md](stage-rows.md) | `FNX_PF_STAGE_ROWS` sweep: prompt-read time by prompt length |
| `json/` | JamC-QA `summary.json` files |

Figures (English, `figures/make_figs.py`): `../figures/speed_4_configs.png`, `../figures/split_0.2.10_vs_0.2.11.png`, `../figures/stage_rows.png`.
