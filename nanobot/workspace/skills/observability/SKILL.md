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
  - `event:unhandled_exception` — unhandled exceptions
- **`mcp_obs_logs_error_count`** — Count errors per service over a time window. Returns a summary of error counts.

### Trace tools (VictoriaTraces)
- **`mcp_obs_traces_list`** — List recent traces for a service. Shows trace IDs, durations, and status.
- **`mcp_obs_traces_get`** — Fetch a specific trace by ID. Shows the full span hierarchy with timing.

## Investigation Workflow: "What went wrong?"

When the user asks **"What went wrong?"** or **"Check system health"**, follow this exact sequence:

1. **Search recent error logs first:**
   - Call `mcp_obs_logs_search` with query `_time:30m AND level:error`
   - If no results, try `_time:1h AND level:error`
   - Summarize what you find: which services have errors, what error messages appear

2. **Look for trace IDs in the error logs:**
   - If error log entries contain `otelTraceID` or `trace_id`, note them
   - Call `mcp_obs_traces_get` with the trace ID to fetch the full trace

3. **Analyze the trace:**
   - Look at the span hierarchy — which span has the error?
   - Check the error message in the failing span
   - Identify the root cause (e.g., database connection refused, timeout, etc.)

4. **Summarize findings concisely:**
   - What failed (service, endpoint)
   - Why it failed (error message from logs/traces)
   - When it started (timestamp from first error)
   - Don't dump raw JSON — present key findings in readable format

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

User: "What went wrong?"
1. Call `mcp_obs_logs_search` with query `_time:30m AND level:error`
2. If errors found, look for trace IDs in the results
3. Call `mcp_obs_traces_get` with any trace ID found
4. Analyze the trace spans to identify where the failure occurred
5. Report: "I found X errors in the last 30 minutes. The root cause is [error message] in [service]. The failure started at [timestamp]."

User: "Check system health"
1. Call `mcp_obs_logs_error_count` with time_range "1h"
2. If errors found, investigate further with `mcp_obs_logs_search`
3. Report summary: "System health: [healthy/degraded/down]. [N] errors in the last hour from [services]."
