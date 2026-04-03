---
description: "Query VictoriaLogs and VictoriaTraces for system observability data. Use when investigating errors, failures, or system health."
always: true
---

# Observability Skill

You have access to observability tools that query VictoriaLogs (structured logs) and VictoriaTraces (distributed traces). Use these tools to investigate system health, errors, and failures.

## Available Tools

### Log tools (VictoriaLogs)
- **`mcp_obs_logs_search`** — Search logs by query string and time range. Use LogsQL queries. Example queries:
  - `level:error` — all error logs
  - `_stream:{service="backend"} AND level:error` — backend errors only
  - `_time:1h AND level:error` — errors in the last hour
  - `event:db_query AND level:error` — database query errors
- **`mcp_obs_logs_error_count`** — Count errors per service over a time window. Returns a summary of error counts.

### Trace tools (VictoriaTraces)
- **`mcp_obs_traces_list`** — List recent traces for a service. Shows trace IDs, durations, and status.
- **`mcp_obs_traces_get`** — Fetch a specific trace by ID. Shows the full span hierarchy with timing.

## Rules

1. **When the user asks about errors or failures**, search logs first using `mcp_obs_logs_search` with a query like `_time:1h AND level:error`.
2. **If you find a trace ID in the logs**, use `mcp_obs_traces_get` to fetch the full trace and understand the failure chain.
3. **For system health questions**, use `mcp_obs_logs_error_count` to get a summary of errors per service.
4. **Summarize findings concisely** — don't dump raw JSON. Present key findings in readable format.
5. **If no errors are found**, report that the system appears healthy.
6. **When investigating a specific failure**, chain tools: search logs → find trace ID → fetch trace → analyze span hierarchy.

## Example Workflow

User: "Any errors in the last hour?"
1. Call `mcp_obs_logs_search` with query `_time:1h AND level:error`
2. Summarize any errors found, or report "No errors found in the last hour."

User: "What went wrong with the last request?"
1. Call `mcp_obs_logs_search` with query `level:error` and a recent time range
2. If a trace ID appears in the logs, call `mcp_obs_traces_get` with that ID
3. Analyze the trace spans to identify where the failure occurred
4. Report the root cause concisely
