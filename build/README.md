# Building the split engine for sm_89

Upstream ships the split engine for sm_86 and sm_120 only. For GeForce RTX 40 cards (sm_89) build it yourself; the upstream script does it with `ARCH=89`.

```
STRATA_SRC=~/src/Strata CUDA=~/cuda-13 LLAMA_CPP=~/src/llama.cpp-3cf03257f219afbe7334045ff7c6a06ac68c627d \
  VENV_BIN=~/venv/bin ./build_sm89.sh
```

`CARDS="2"` builds the two-card variant (`strata-split-2-sm89`).

## Which source

| Goal | Source | Patches |
|---|---|---|
| 0.2.10 | tag `v0.2.10` | `patches/0002` (model.cpp hunk only, `--exclude=docs/SPLIT_ENGINE.md`), optionally `patches/0001-*-0.2.10.patch` |
| 0.2.11 | the [PR #5258 branch](https://github.com/nabe2030/Strata/tree/pool-floor) (0.2.11 plus 0002) | optionally `patches/0001-*-0.2.11.patch` |

`patches/0002` is required for a mixed-quant file such as IQ3_S on 16 GB cards, otherwise the engine refuses to start (see the top-level README). `patches/0001` only matters if you start through `strata launch`; the service in `service/` runs the engine binary directly and does not need it.

## Toolchain we used

- Ubuntu 22.04, GCC/G++ 11.4.0
- CUDA toolkit 13.4 (nvcc 13.4.92), installed in a private directory (not system-wide)
- cmake and ninja from a Python venv (`pip install cmake ninja`; no npm anywhere)
- llama.cpp pinned by Strata at commit `3cf03257f219afbe7334045ff7c6a06ac68c627d` (same for 0.2.10 and 0.2.11)
- 12-core CPU, `JOBS=4` with `nice -n 15`: about 11 minutes for 83 ninja steps; the machine kept serving requests meanwhile
- nvcc prints several hundred diagnostics (549-D, 128-D, 177-D, ...). They come from the existing kernels and do not affect the build. The upstream script's final check that no peer-access function is callable passes.

## After the build

Copy `libcudart.so.13`, `libcublas.so.13` and `libcublasLt.so.13` next to the binary (RUNPATH is `$ORIGIN`), or list their directory under `lib_dirs` in the run config. `ldd strata-split-2-sm89` should resolve everything. The binary is about 56 MB.
