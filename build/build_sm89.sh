#!/bin/bash
# Build Strata's all-cards split engine for sm_89 (GeForce RTX 40 series) on two cards.
# Wraps the upstream script packaging/build_split_cuda.sh; only the paths below are ours.
# Usage: STRATA_SRC=/path/to/Strata CUDA=/path/to/cuda-root LLAMA_CPP=/path/to/llama.cpp-3cf03257... ./build_sm89.sh
set -euo pipefail
: "${STRATA_SRC:?path to a Strata checkout (v0.2.10, or the branch with patches/0002 applied)}"
: "${CUDA:?CUDA 13 toolkit root (contains bin/nvcc)}"
: "${LLAMA_CPP:?llama.cpp checkout at the commit pinned by Strata (3cf03257f219afbe7334045ff7c6a06ac68c627d for 0.2.10 and 0.2.11)}"
BUILD_DIR="${BUILD_DIR:-$PWD/build-sm89}"
JOBS="${JOBS:-4}"                      # the build is heavy on RAM; 4 jobs on a 12-core box was fine
VENV_BIN="${VENV_BIN:-}"               # a bin/ directory that has cmake and ninja, if the system ones are missing
export PATH="${VENV_BIN:+$VENV_BIN:}$CUDA/bin:$PATH"
command -v cmake >/dev/null || { echo "cmake not on PATH (set VENV_BIN)"; exit 127; }
command -v ninja >/dev/null || { echo "ninja not on PATH (set VENV_BIN)"; exit 127; }
SRC="$STRATA_SRC" B="$BUILD_DIR" CUDA="$CUDA" GG="$LLAMA_CPP" ARCH=89 CARDS="2" JOBS="$JOBS" \
  nice -n 15 bash "$STRATA_SRC/packaging/build_split_cuda.sh" 2>&1 | tee build.log
echo "binary: $BUILD_DIR/strata-split-2-sm89"
# The CUDA runtime libraries (libcudart, libcublas, libcublasLt .so.13) are not copied by the script:
# copy them next to the binary (RUNPATH is $ORIGIN) or point LD_LIBRARY_PATH / "lib_dirs" in the run config at $CUDA/lib64.
