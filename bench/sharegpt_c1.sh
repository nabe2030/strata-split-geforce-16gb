#!/bin/bash
# ShareGPT, 200 requests, one at a time (c=1), seed 0, thinking off, using `vllm bench serve` in a container.
# Usage: URL=http://HOST:8095 MODEL=name ENGINE_LOG=/path/engine.log [LONG=1] [OUT=./out] ./sharegpt_c1.sh
# ENGINE_LOG is the split engine's log; if it lives on another machine set LOG_CAT="ssh user@host cat".
# Needs: docker with the vllm/vllm-openai image, a ShareGPT json (DATASET dir), a tokenizer dir for the model (TOKENIZER).
set -euo pipefail
: "${URL:?}"; : "${MODEL:?}"; : "${ENGINE_LOG:?}"
OUT="${OUT:-./out}"; DATASET="${DATASET:?dir with ShareGPT_V3_unfiltered_cleaned_split.json}"; TOKENIZER="${TOKENIZER:?dir with the model tokenizer}"
IMAGE="${IMAGE:-vllm/vllm-openai:latest}"
LOG_CAT="${LOG_CAT:-cat}"              # e.g. LOG_CAT="ssh user@host cat" when the engine runs on another machine
mkdir -p "$OUT"; EXTRA=""; [ "${LONG:-0}" = 1 ] && EXTRA="--sharegpt-output-len 1024"
for q in "What is the capital of Japan?" "Explain TCP in two sentences." "What is the sum of 1 to 10?" "Write a haiku about rain." "What is 17*23?"; do   # 5 warm-up requests, not recorded
  curl -s -m 300 "$URL/v1/chat/completions" -H 'Content-Type: application/json' \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"$q\"}],\"max_tokens\":64,\"temperature\":0,\"chat_template_kwargs\":{\"enable_thinking\":false}}" >/dev/null
done
N0=$($LOG_CAT "$ENGINE_LOG" | wc -l)
docker run --rm --network host -v "$DATASET":/datasets:ro -v "$TOKENIZER":/tokenizer:ro -v "$(realpath "$OUT")":/results \
  --entrypoint vllm "$IMAGE" bench serve --backend openai-chat --base-url "$URL" \
  --endpoint /v1/chat/completions --model "$MODEL" --tokenizer /tokenizer \
  --dataset-name sharegpt --dataset-path /datasets/ShareGPT_V3_unfiltered_cleaned_split.json $EXTRA \
  --num-prompts 200 --max-concurrency 1 --seed 0 --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}' \
  --save-result --save-detailed --result-dir /results --result-filename c1.json > "$OUT/c1.log" 2>&1
# The engine log has one `sfnx: slot 0: prompt N tokens = R reused + X read in T ms, G generated in Y ms (S tok/s), drafts A of B` line per request.
$LOG_CAT "$ENGINE_LOG" | tail -n +$((N0+1)) | grep -E 'slot 0: prompt' > "$OUT/engine_requests_raw.txt"
# Cut the 200 lines that belong to this run: the server counts 12 more prompt tokens than the client (chat template), so match input lengths.
python3 - "$OUT" <<'PY'
import json, re, sys
d = sys.argv[1]; L = json.load(open(d + "/c1.json"))["input_lens"]
lines = open(d + "/engine_requests_raw.txt").read().splitlines()
tok = [int(re.search(r"prompt (\d+) tokens", l)[1]) for l in lines]
hits = [o for o in range(len(tok) - len(L) + 1) if all(tok[o + i] - 12 == L[i] for i in range(len(L)))]
o = hits[0] if hits else max(0, len(lines) - len(L))
open(d + "/engine_requests.txt", "w").write("\n".join(lines[o:o + len(L)]) + "\n")
print(len(lines), "log lines; aligned at", hits[:1] or "tail (no exact match)")
PY
python3 "$(dirname "$0")/split_recompute.py" "$OUT"
