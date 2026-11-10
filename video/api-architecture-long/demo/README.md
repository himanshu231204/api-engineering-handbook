# demo/

Real run of the handbook's [`examples/llm-gateway`](../../../examples/llm-gateway/README.md) used in the "See it run" chapter of the video.

- `run_demo.sh` - the exact commands (start the example first: `uvicorn main:app --port 8000`).
- `real_output.txt` - the output of that run, shown on screen (long commands are trimmed with `…` in the video, and the pill says so).

The first provider is a deliberately flaky test adapter (about 50% failure), so which requests fall back to `provider_a` differs on every run; this file is the run that was recorded.
