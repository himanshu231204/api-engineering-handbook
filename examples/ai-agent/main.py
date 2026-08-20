"""
Tool-using agent loop, exposed via a FastAPI `/agent` endpoint.

Loop: call the LLM with the current message history and the available tool
schemas -> if it requests a tool, execute the matching Python function and
feed the result back as a new message -> repeat -> until the LLM returns a
final text answer, bounded by a max-iteration cap.

See ../../docs/14-ai-api-engineering/tool-calling.md and
../../docs/17-ai-agents-and-mcp/agent-architecture.md for the concepts this
implements a runnable, minimal version of.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from llm_client import call_llm_with_tools
from tools import TOOL_REGISTRY, TOOL_SCHEMAS

MAX_ITERATIONS = 6
TOOL_TIMEOUT_SECONDS = 15

app = FastAPI(title="Tool-Using Agent Loop Example")


class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1)


class AgentStep(BaseModel):
    tool_name: str
    tool_input: dict
    tool_result: dict


class AgentResponse(BaseModel):
    answer: str
    steps: list[AgentStep]
    iterations: int


async def execute_tool(name: str, args: dict) -> dict:
    """Look up and run the tool the model asked for, feeding back an error
    (rather than raising) if the tool is unknown or fails — the agent loop
    keeps going with that information instead of crashing the request."""
    handler = TOOL_REGISTRY.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return await handler(args)
    except Exception as exc:  # noqa: BLE001 - surface to the model as a tool result, don't crash the loop
        return {"error": f"tool execution failed: {exc}"}


async def run_agent_loop(user_message: str) -> AgentResponse:
    messages: list[dict] = [{"role": "user", "content": user_message}]
    steps: list[AgentStep] = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        response = await call_llm_with_tools(messages, TOOL_SCHEMAS)
        tool_calls = [block for block in response["content"] if block["type"] == "tool_use"]

        if not tool_calls:
            text_blocks = [block["text"] for block in response["content"] if block["type"] == "text"]
            return AgentResponse(answer="\n".join(text_blocks), steps=steps, iterations=iteration)

        # Record the model's tool-call turn, then execute each requested call.
        messages.append({"role": "assistant", "content": response["content"]})

        tool_result_blocks = []
        for call in tool_calls:
            result = await execute_tool(call["name"], call["input"])
            steps.append(AgentStep(tool_name=call["name"], tool_input=call["input"], tool_result=result))
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_result_blocks})

    # Hit the iteration cap without a final answer -- fail explicitly
    # rather than silently returning nothing. See the "Bound the loop,
    # always" guidance in docs/14-ai-api-engineering/tool-calling.md.
    raise HTTPException(
        status_code=500,
        detail=f"agent did not converge on a final answer after {MAX_ITERATIONS} iterations",
    )


@app.post("/agent", response_model=AgentResponse)
async def agent(request: AgentRequest) -> AgentResponse:
    return await run_agent_loop(request.message)


@app.get("/tools")
async def list_tools() -> list[dict]:
    """Introspection endpoint: see the tool schemas the agent has available."""
    return TOOL_SCHEMAS
