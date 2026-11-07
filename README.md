# Strata's all-cards split engine on 2x GeForce RTX 4060 Ti 16 GB

Running Strata's all-cards split engine (0.2.10 / 0.2.11, built from John Fink's sFNX) for Qwen3.8-Flash-Next (125B MoE) on a consumer PC with two RTX 4060 Ti 16 GB cards and 128 GB of RAM — a configuration the Strata docs list as untested ("no GeForce pair on hand").

It works. It needed four changes, and it is the fastest decoder we have for this model on this box: 1.2x the layer split on the same two cards, 1.6x one card, and on our agent benchmark 2.3x a DGX Spark. Full write-up in Japanese: [Qiita article](https://qiita.com/nabe2030/items/a0e4213c839400f65627). Upstream discussion: [Niko1221/Strata#5187](https://github.com/Niko1221/Strata/issues/5187), [PR #5258](https://github.com/Niko1221/Strata/pull/5258), [#5440](https://github.com/Niko1221/Strata/issues/5440).

## Results at a glance

Same PC, same 200 ShareGPT requests one at a time (c=1), context 8K, MTP drafter, thinking off. Strata 0.2.10, measured 2026-11-04/05, one run each.

| | Split engine (tuned) | Layer split, 2 cards | 1 card |
|---|---|---|---|
| Generated tokens / wall time | 35.7 tok/s | **40.6** | 32.3 |
| Decode, median | **58.2 tok/s** | 48.7 | 36.3 |
| Prompt read, median | 2.49 s | 1.05 | 1.01 |

- **Decode is the fastest**, but every request pays about **1.4 s** more than the layer split to read the prompt (the non-resident experts have to cross PCIe). With `max_tokens` 1024 the two tie (49.4 vs 49.3 tok/s); the break-even is **about 730 output tokens**. Code generation and long answers favour the split engine; short chat turns favour the layer split.
- **Quality is unchanged**: JamC-QA (2,309 Japanese multiple-choice questions) 64.96% vs 65.09% for the layer split (McNemar p=0.81).
- **256K context works**: a fresh 200K-token prompt reads in 150 s (~1,330 tok/s) and decodes at 49 tok/s right after; the next turn hits the conversation cache (2.4 s).
- **Agent work** ([GembaBench](https://github.com/nabe2030/gembabench): OpenCode v2 doing 6 server-investigation tasks on throwaway VMs, 3 runs each, 256K context): 5.7 h total for the split engine vs 7.3 h for the layer split and 12.9 h for a DGX Spark, with the same scores.

### 0.2.11

Strata 0.2.11 (2026-11-05) changed the split engine's prompt-path defaults and fused the shared expert into the routed launches. Rebuilt from the [PR #5258 branch](https://github.com/nabe2030/Strata/tree/pool-floor) (includes 0.2.11), same settings, binary swapped, one run each:

| | 0.2.10 | 0.2.11 |
|---|---|---|
| Short outputs, generated tokens / wall time | 35.70 tok/s | 37.25 (+4.3%) |
| `max_tokens` 1024, generated tokens / wall time | 49.44 tok/s | 51.12 (+3.4%) |
| Decode median (long outputs) | 58.85 tok/s | 61.0 (+3.7%) |
| JamC-QA | 64.96% | 64.79% (p=0.65) |
| 200K-token fresh prompt read | 150.3 s | 155.5 s (+3.5%) |

The new prompt-path defaults are sized for 48 GB cards; on 16 GB the auto-selection falls to the smallest buffer (4096 rows x 2 chunks), and forcing larger buffers either fails to start or evicts experts from VRAM and is slower (see `results/`). The per-request overhead is untouched by 0.2.11 — that is [#5440](https://github.com/Niko1221/Strata/issues/5440).

## The four changes

1. **No sm_89 binary.** The split engine ships for sm_86 and sm_120 only. Build it with the upstream script: `ARCH=89 CARDS=2 packaging/build_split_cuda.sh` (`build/`).
2. **The launcher only allows "all routed experts fit in VRAM".** The engine itself already has the RAM-resident expert path (`FNX_ARENA=1`, `FNX_EXPERT_RAM_GIB`), the launcher just forces it off. `patches/0001-*` adds env switches (`STRATA_SPLIT_SKIP_VRAM_CHECK`, `STRATA_SPLIT_FNX_ARENA`, `STRATA_SPLIT_FNX_EXPERT_RAM_GIB`); defaults unchanged. Not needed if you start the engine binary directly (as `service/` does).
3. **memlock.** The engine pins ~80 GiB; a stock Linux `ulimit -l` of 16 GiB stops it at the 27 GB embedding table. `LimitMEMLOCK=infinity` in the unit (or `prlimit --memlock=unlimited`).
4. **Mixed-quant pools.** IQ3_S has different expert types per layer, so the engine keeps 7 size pools, each needing at least 320 resident experts. The coldest-by-bytes eviction empties the large-expert pool first and the engine refuses to start; keeping more in VRAM overflows it instead. `patches/0002-*` adds a per-pool residency floor (`FNX_POOL_MIN_RESIDENT`, default 0 = upstream behaviour; we use 384). This is [PR #5258](https://github.com/Niko1221/Strata/pull/5258).

Plus one tuning: `FNX_PF_STAGE_ROWS=8`. The default (2048) reads RAM-resident experts in place over PCIe for prompts under 2048 tokens, which on this box costs 2–6 s even for short prompts; staging them instead takes a fixed ~1.6 s per card. Short prompts go 3.0 → 2.0 s, 780 tokens 6.0 → 2.4 s. Details and a proposal in [#5440](https://github.com/Niko1221/Strata/issues/5440).

## Hardware

| | |
|---|---|
| GPU | 2x NVIDIA GeForce RTX 4060 Ti 16 GB (PCIe 4.0 x8 each, both CPU-attached, no P2P) |
| CPU / board | AMD Ryzen 5 5600, GIGABYTE X570 AORUS PRO WIFI |
| RAM | 128 GB DDR4-3200 (64 GB is not enough: ~45 GiB of expert copies + 27.5 GB embedding table are pinned) |
| OS | Ubuntu 22.04, CUDA 13 |
| Model | Qwen3.8-Flash-Next GSQ-RCO IQ3_S (ISTA-DASLab, 78 GB) + MTP draft layer |

## What is here

| Path | Contents |
|---|---|
| `patches/` | 0001 launcher env switches (0.2.10 and 0.2.11 versions), 0002 pool residency floor |
| `build/` | build script wrapper for sm_89, notes on the toolchain |
| `service/` | systemd unit, run config and nftables example used to serve OpenCode (names and addresses are placeholders) |
| `bench/` | ShareGPT driver and log re-computation, JamC-QA runner, long-context probe |
| `results/` | per-step measurement tables (speed sweep, long outputs, JamC-QA, 256K, 0.2.11 comparison, prompt-buffer and `FNX_PF_STAGE_ROWS` sweeps) |
| `figures/` | charts used in the article |

## Running it

See `service/README.md`. In short: build the sm_89 binary, place the model and the MTP draft file, start the engine binary with the environment from `service/svc-cfg.example.json` (`FNX_ARENA=1 FNX_EXPERT_RAM_GIB=20 FNX_POOL_MIN_RESIDENT=384 FNX_PF_STAGE_ROWS=8`, `--spec 6 --lookup 15 --batch 1 --max-context 262144`), with memlock unlimited. Start-up takes about 95 s.

## License

Patches and scripts: MIT, same as Strata. Measurements and text: CC BY 4.0.
