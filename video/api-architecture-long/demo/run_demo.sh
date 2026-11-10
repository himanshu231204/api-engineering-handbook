#!/usr/bin/env bash
# Reproduces the terminal output shown in the "See it run" chapter.
# Needs: python3 -m venv .venv && .venv/bin/pip install -r ../../../examples/llm-gateway/requirements.txt
# Start the server first (from examples/llm-gateway):  uvicorn main:app --port 8000
# NOTE: the first provider fails ~50% of the time on purpose, so which calls fall back to provider_a differs run to run.
set -u
BASE=http://localhost:8000
echo '$ for i in 1 2 3 4 5; do curl -s -X POST localhost:8000/chat ... | print(provider, cost_usd); done'
for i in 1 2 3 4 5; do
  sleep 1.2
  curl -s -X POST $BASE/chat -H "Content-Type: application/json" \
    -d '{"tenant_id": "acme_corp", "prompt": "Summarize the Q3 roadmap."}' \
  | python3 -c "import sys, json; d = json.load(sys.stdin); print(d['provider'], d['cost_usd'])"
done
echo '$ curl -s localhost:8000/usage'
curl -s $BASE/usage; echo
echo '$ for i in $(seq 1 8); do curl ... -w "%{http_code}\n" ... /chat; done   # a burst, after the bucket refilled'
sleep 6
for i in $(seq 1 8); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST $BASE/chat -H "Content-Type: application/json" \
    -d '{"tenant_id": "acme_corp", "prompt": "hi"}'
done
