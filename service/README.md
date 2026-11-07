# Serving the split engine

1. Build the sm_89 binary (`../build/`), place the model (IQ3_S, 2 shards) and the MTP draft files, and edit the paths in `svc-cfg.example.json` (copy it to `svc-cfg.json`).
2. Install the unit: copy `strata-split.service` to `/etc/systemd/system/`, replace the user, `/path/to/...` entries, and run `systemctl daemon-reload && systemctl enable --now strata-split`.
   `LimitMEMLOCK=infinity` is required: the engine pins about 80 GiB of host memory. Without it, start-up stops at the 27 GB embedding table. For a manual start use `sudo prlimit --memlock=unlimited:unlimited --pid $$` first.
3. The server (`serve/server.py --engine strata`) reads the run config and starts the engine binary itself. Start-up takes about 95 s; `curl http://HOST:8088/health` shows `loaded: true` when it is ready.
4. Optional: `strata-lan.nft.example` restricts the API port to your LAN. The API has no authentication.

Settings in the run config (all verified on 2x RTX 4060 Ti 16 GB, 128 GB RAM):

| Setting | Why |
|---|---|
| `FNX_ARENA=1`, `FNX_EXPERT_RAM_GIB=20` | keep a copy of all routed experts in pinned host memory and fill VRAM slots from it (the launcher forces this off) |
| `FNX_POOL_MIN_RESIDENT=384` | needs `patches/0002`; keeps every size pool of a mixed-quant file above the 320 slots the engine needs |
| `FNX_PF_STAGE_ROWS=8` | stage RAM-resident experts for any prompt of 8 tokens or more instead of reading them in place; see `results/stage-rows.md` |
| `--spec 6 --lookup 15` | MTP drafter, 6 draft tokens, plus prompt-lookup drafts |
| `--batch 1` | one request at a time |
| `--conversation-cache-mib` | RAM for the conversation cache; 1024 holds a 200K-token conversation (int8 K/V, about 5 KiB per position); 4096 leaves room for more sessions |
| `--max-context 262144` | a larger context does not need more `FNX_EXPERT_RAM_GIB`: the K/V pool grows by borrowing expert slots as the context fills |

Do not expose port 8088 to the internet. Nothing here is a hardened deployment.
