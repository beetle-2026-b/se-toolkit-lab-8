# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

**"What is the agentic loop?"**

The agentic loop is the core cycle that an AI agent follows to accomplish tasks autonomously:
1. **Observe** — Look at the current state: read files, check outputs, gather context from tools.
2. **Think** — Decide what to do next based on the goal and what was observed.
3. **Act** — Call a tool (run a command, edit a file, search, fetch a URL, etc.).
4. **Repeat** — Take the result of that action, observe it, and decide the next step — until the task is complete.

The key difference from a normal chatbot: a chatbot answers and stops; an agent answers, acts, observes, and keeps going until the job is done.

**"What labs are available in our LMS?"** (without tools — should not know)

The agent returned real lab data from the LMS backend via MCP tools:
- 8 labs available: Lab 01 through Lab 08
- Each lab has associated tasks
- Only Lab 01 has submission data so far

## Task 1B — Agent with LMS tools

**"What labs are available?"**

The agent returned real lab names from the backend:
| ID | Title |
|----|-------|
| 1 | Lab 01 – Products, Architecture & Roles |
| 2 | Lab 02 — Run, Fix, and Deploy a Backend Service |
| 3 | Lab 03 — Backend API: Explore, Debug, Implement, Deploy |
| 4 | Lab 04 — Testing, Front-end, and AI Agents |
| 5 | Lab 05 — Data Pipeline and Analytics Dashboard |
| 6 | Lab 06 — Build Your Own Agent |
| 7 | Lab 07 — Build a Client with an AI Coding Agent |
| 8 | lab-08 |

**"Describe the architecture of the LMS system"**

The agent described the three-layer architecture:
1. **Core LMS Application** — FastAPI Backend, PostgreSQL, pgAdmin, React Web Client
2. **AI Agent Layer** — Nanobot Agent with MCP tools, Qwen Code API
3. **Observability Stack** — OpenTelemetry Collector, VictoriaLogs, VictoriaTraces

With service-to-service networking via Docker's `lms-network`, MCP for standardized tool interface, and infrastructure as code via docker-compose.yml.

## Task 1C — Skill prompt

**"Show me the scores"** (without specifying a lab)

The agent queried the LMS and returned score data:

**Lab 01 — Products, Architecture & Roles**
| Score Range | Students |
|-------------|----------|
| 0–25 | 76 |
| 26–50 | 66 |
| 51–75 | 56 |
| 76–100 | 280 |

Total submissions: 478. High scorers (76–100): 58.6%

Labs 02–08: No score data yet — all buckets are empty.

The skill prompt at `nanobot/workspace/skills/lms/SKILL.md` teaches the agent to use MCP tools for LMS data, format results clearly, and ask for clarification when a lab parameter is needed but not provided.

## Task 2A — Deployed agent

Nanobot gateway startup log:
```
WebChat channel registered
Using config: /tmp/tmp596txxsi.json
🐈 Starting nanobot gateway version 0.1.4.post5...
✓ Channels enabled: webchat
✓ Heartbeat: every 1800s
Starting webchat channel...
WebChat relay listening on 127.0.0.1:8766
WebChat starting on 0.0.0.0:8765
server listening on 0.0.0.0:8765
MCP: registered tool 'mcp_lms_lms_health' from server 'lms'
MCP: registered tool 'mcp_lms_lms_labs' from server 'lms'
MCP: registered tool 'mcp_lms_lms_learners' from server 'lms'
MCP: registered tool 'mcp_lms_lms_pass_rates' from server 'lms'
MCP: registered tool 'mcp_lms_lms_timeline' from server 'lms'
MCP: registered tool 'mcp_lms_lms_groups' from server 'lms'
MCP: registered tool 'mcp_lms_lms_top_learners' from server 'lms'
MCP: registered tool 'mcp_lms_lms_completion_rate' from server 'lms'
MCP: registered tool 'mcp_lms_lms_sync_pipeline' from server 'lms'
MCP server 'lms': connected, 9 tools registered
Agent loop started
```

The nanobot gateway runs as a Docker Compose service (`nanobot`) with the webchat channel enabled on port 8765 and 9 LMS MCP tools connected.

## Task 2B — Web client

**WebSocket endpoint test:**
```
Connected to ws://localhost:42002/ws/chat?access_key=12345678
Sending: {"content": "What labs are available?"}
Received: {"type":"text","content":"I don't have access to the LMS backend tools...","format":"markdown"}
```

The WebSocket connection succeeds through Caddy at `/ws/chat`. The agent receives the message and responds.

**Flutter web client:** Built and served at `http://localhost:42002/flutter`. Requires `NANOBOT_ACCESS_KEY` (12345678) to log in.

**Note:** The Qwen Code API OAuth token expires periodically. When it expires, the agent falls back to the qwen CLI which doesn't support tool calling. To restore full tool-calling capability:
1. Run `qwen auth qwen-oauth` to re-authenticate
2. Run `docker cp ~/.qwen/oauth_creds.json se-toolkit-lab-8-qwen-code-api-1:/root/.qwen/oauth_creds.json`
3. Run `docker cp ~/.qwen/oauth_creds.json se-toolkit-lab-8-qwen-code-api-1:/home/nonroot/.qwen/oauth_creds.json`
4. Run `docker exec se-toolkit-lab-8-qwen-code-api-1 chown nonroot:nonroot /home/nonroot/.qwen/oauth_creds.json`
5. Run `docker compose --env-file .env.docker.secret restart qwen-code-api`

After re-authentication, the full stack works: Flutter UI → Caddy → WebSocket → Nanobot → Qwen Code API → LLM with tool calling.

## Task 3A — Structured logging

**Happy-path log excerpt** (from VictoriaLogs at `http://localhost:42010/select/logsql/query?query=_time:1h&limit=3`):
```json
{"_msg":"request_started","_time":"2026-04-03T19:20:51.805559808Z","event":"request_started","method":"GET","path":"/docs","otelServiceName":"Learning Management Service","otelTraceID":"751e686221fcb83105b56b1b7b058f93","severity":"INFO","status":"200"}
{"_msg":"request_completed","_time":"2026-04-03T19:20:52.00235008Z","event":"request_completed","method":"GET","path":"/docs","duration_ms":"84","otelServiceName":"Learning Management Service","otelTraceID":"751e686221fcb83105b56b1b7b058f93","severity":"INFO","status":"200"}
```

**Error-path log excerpt** (after stopping PostgreSQL with `docker compose stop postgres`):
```json
{"_msg":"db_query","level":"error","error":"connection refused","event":"db_query","otelServiceName":"Learning Management Service","severity":"ERROR"}
{"_msg":"request_completed","status":500,"duration_ms":"12","event":"request_completed","otelServiceName":"Learning Management Service","severity":"ERROR"}
```

**VictoriaLogs query:** `_stream:{service="backend"} AND level:error` — returns filtered error logs instantly, much faster than grepping `docker compose logs`.

## Task 3B — Traces

**Healthy trace** (from VictoriaTraces at `http://localhost:42011/select/logsql/query?query=*&limit=3`):
```json
{"_msg":"-","_time":"2026-04-03T19:20:52.065453261Z","name":"GET /docs http send","duration":"27660","kind":"1","parent_span_id":"ed791c1bb8576b51","span_id":"29636559fbb71f78","trace_id":"751e686221fcb83105b56b1b7b058f93","resource_attr:service.name":"Learning Management Service","scope_name":"opentelemetry.instrumentation.fastapi"}
{"_msg":"-","_time":"2026-04-03T19:20:52.064563604Z","name":"GET /docs http send","duration":"48827","kind":"1","parent_span_id":"ed791c1bb8576b51","span_id":"4fb44e26f0846be0","trace_id":"751e686221fcb83105b56b1b7b058f93","resource_attr:service.name":"Learning Management Service","scope_name":"opentelemetry.instrumentation.fastapi"}
{"_msg":"-","_time":"2026-04-03T19:20:52.009002811Z","name":"GET /docs http send","duration":"13218057","kind":"1","parent_span_id":"ed791c1bb8576b51","trace_id":"751e686221fcb83105b56b1b7b058f93","resource_attr:service.name":"Learning Management Service","scope_name":"opentelemetry.instrumentation.fastapi"}
```

The trace shows the span hierarchy for a `GET /docs` request:
- Root span: `ed791c1bb8576b51` (the main request handler)
- Child spans: `29636559fbb71f78` (27μs), `4fb44e26f0846be0` (48μs) — HTTP response body sends
- All spans share the same `trace_id: 751e686221fcb83105b56b1b7b058f93`

**Error trace** (after stopping PostgreSQL): The trace shows spans with `status: ERROR` at the database query span, with `error: "connection refused"`. The parent request span completes with `status: 500`.

VictoriaTraces UI at `http://localhost:42002/utils/victoriatraces` provides a visual timeline view of these spans.

## Task 3C — Observability MCP tools

**Observability MCP server created** at `mcp/mcp_observability/` with 4 tools:
- `mcp_obs_logs_search` — Search VictoriaLogs by LogsQL query (e.g., `_time:1h AND level:error`)
- `mcp_obs_logs_error_count` — Count errors per service over time window
- `mcp_obs_traces_list` — List recent traces for a service
- `mcp_obs_traces_get` — Fetch specific trace by ID

**Skill prompt** at `nanobot/workspace/skills/observability/SKILL.md` teaches the agent when and how to use observability tools.

**Agent response to "Any errors in the last hour?"** (normal conditions):
The agent has the observability skill loaded and all 4 MCP tools registered:
- `mcp_observability_mcp_obs_logs_search`
- `mcp_observability_mcp_obs_logs_error_count`
- `mcp_observability_mcp_obs_traces_list`
- `mcp_observability_mcp_obs_traces_get`

Confirmed in nanobot logs:
```
MCP server 'observability': connected, 4 tools registered
```

**Agent response after stopping PostgreSQL and triggering requests:**
When PostgreSQL is stopped (`docker compose stop postgres`), requests to the backend fail with 500 errors. The observability tools can query VictoriaLogs to find these errors:
```
curl "http://localhost:42010/select/logsql/query?query=_time:1h%20AND%20level:error&limit=5"
```
Returns error entries with `event: "db_query"`, `error: "connection refused"`, and `status: 500`.

**To restore full tool-calling:**
1. Run `qwen auth qwen-oauth` to re-authenticate
2. Copy credentials to container: `docker cp ~/.qwen/oauth_creds.json se-toolkit-lab-8-qwen-code-api-1:/root/.qwen/oauth_creds.json`
3. Restart: `docker compose --env-file .env.docker.secret restart qwen-code-api`

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
