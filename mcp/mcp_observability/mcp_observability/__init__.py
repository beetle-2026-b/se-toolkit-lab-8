"""Stdio MCP server exposing VictoriaLogs and VictoriaTraces as typed tools."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

server = Server("observability")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VICTORIALOGS_URL = os.environ.get("VICTORIALOGS_URL", "http://localhost:42010")
VICTORIATRACES_URL = os.environ.get("VICTORIATRACES_URL", "http://localhost:42011")

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _LogsSearchArgs(BaseModel):
    query: str = Field(description="LogsQL query string, e.g. 'level:error' or '_time:1h AND level:error'")
    limit: int = Field(default=20, ge=1, le=100, description="Max log entries to return")


class _LogsErrorCountArgs(BaseModel):
    time_range: str = Field(default="1h", description="Time window, e.g. '1h', '30m', '24h'")


class _TracesListArgs(BaseModel):
    service: str = Field(default="Learning Management Service", description="Service name to filter traces")
    limit: int = Field(default=10, ge=1, le=50, description="Max traces to return")


class _TracesGetArgs(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _victorialogs_query(query: str, limit: int = 20) -> list[dict]:
    """Query VictoriaLogs HTTP API."""
    url = f"{VICTORIALOGS_URL}/select/logsql/query"
    params = {"query": query, "limit": str(limit)}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        results = []
        for line in lines:
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    results.append({"_raw": line})
        return results


async def _victoriatraces_list(service: str = "Learning Management Service", limit: int = 10) -> list[dict]:
    """List recent traces from VictoriaTraces."""
    url = f"{VICTORIATRACES_URL}/api/v1/traces"
    params = {"service": service, "limit": str(limit)}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", [])
        return []


async def _victoriatraces_get(trace_id: str) -> dict:
    """Fetch a specific trace by ID."""
    url = f"{VICTORIATRACES_URL}/api/v1/traces/{trace_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Trace not found: {trace_id}", "status": resp.status_code}


def _text(data: Any) -> list[TextContent]:
    """Serialize data to JSON text block."""
    if isinstance(data, str):
        return [TextContent(type="text", text=data)]
    return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchArgs) -> list[TextContent]:
    results = await _victorialogs_query(args.query, args.limit)
    if not results:
        return _text(f"No logs found for query: {args.query}")
    return _text(results)


async def _logs_error_count(args: _LogsErrorCountArgs) -> list[TextContent]:
    query = f"_time:{args.time_range} AND level:error"
    results = await _victorialogs_query(query, limit=100)
    # Count errors per service
    counts: dict[str, int] = {}
    for entry in results:
        service = entry.get("otelServiceName", entry.get("service", "unknown"))
        counts[service] = counts.get(service, 0) + 1
    return _text({"time_range": args.time_range, "error_counts": counts, "total_errors": len(results)})


async def _traces_list(args: _TracesListArgs) -> list[TextContent]:
    results = await _victoriatraces_list(args.service, args.limit)
    if not results:
        return _text(f"No traces found for service: {args.service}")
    # Summarize traces
    summary = []
    for trace in results:
        summary.append({
            "trace_id": trace.get("traceID", trace.get("trace_id", "unknown")),
            "duration_ms": trace.get("duration", 0),
            "spans": len(trace.get("spans", [])),
        })
    return _text(summary)


async def _traces_get(args: _TracesGetArgs) -> list[TextContent]:
    result = await _victoriatraces_get(args.trace_id)
    if "error" in result:
        return _text(result)
    # Summarize trace spans
    spans = result.get("data", [result])[0].get("spans", []) if isinstance(result, dict) else []
    summary = []
    for span in spans:
        summary.append({
            "operation": span.get("operationName", span.get("operation", "unknown")),
            "duration_ms": span.get("duration", 0),
            "status": span.get("status", {}).get("code", "unknown"),
            "tags": {t.get("key"): t.get("value") for t in span.get("tags", [])},
        })
    return _text({"trace_id": args.trace_id, "spans": summary})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_TOOLS: dict[str, tuple[type[BaseModel], Callable[..., Awaitable[list[TextContent]]], Tool]] = {}


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    schema = model.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("title", None)
    _TOOLS[name] = (model, handler, Tool(name=name, description=description, inputSchema=schema))


_register(
    "mcp_obs_logs_search",
    "Search VictoriaLogs by LogsQL query. Use 'level:error' for errors, '_time:1h' for time range.",
    _LogsSearchArgs,
    _logs_search,
)
_register(
    "mcp_obs_logs_error_count",
    "Count errors per service over a time window (e.g. '1h', '30m').",
    _LogsErrorCountArgs,
    _logs_error_count,
)
_register(
    "mcp_obs_traces_list",
    "List recent traces for a service from VictoriaTraces.",
    _TracesListArgs,
    _traces_list,
)
_register(
    "mcp_obs_traces_get",
    "Fetch a specific trace by ID from VictoriaTraces.",
    _TracesGetArgs,
    _traces_get,
)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [entry[2] for entry in _TOOLS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    entry = _TOOLS.get(name)
    if entry is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    model_cls, handler, _ = entry
    try:
        args = model_cls.model_validate(arguments or {})
        return await handler(args)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
