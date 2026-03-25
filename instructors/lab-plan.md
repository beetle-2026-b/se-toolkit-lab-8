# Lab plan — Add Observability with VictoriaLogs and VictoriaTraces

**Topic:** structured logging, distributed tracing, and AI-assisted observability
**Date:** 2026-03-24

## Main goals

- Show students that unstructured text logs are nearly useless for debugging multi-service systems — structured logging makes the difference.
- Teach the two complementary views of a running system: logs tell you what happened at each service, traces tell you how a request flowed across services.
- Demonstrate that an AI agent becomes much more useful when it can access operational data — not just application data — through MCP tools.

<!-- sometimes, you can use a debugger. other times - no -->
<!-- fix a bug in a problematic endpoint (e.g. model field mismatch) -->
<!-- optional task - improve formatting of messages in clients -->
<!-- if not enough memory - use swap) -->

## Learning outcomes

By the end of this lab, students should be able to:

- [Understand] Explain how structured logs and distributed traces provide complementary views of a multi-service system — logs capture events, traces capture request flow.
- [Apply] Add structured JSON logging at key points across multiple services so that both successful and failed requests produce a defined sequence of queryable events.
- [Apply] Implement MCP tools that query the VictoriaLogs API and return meaningful summaries to the nanobot agent.
- [Apply] Implement MCP tools that query the VictoriaTraces API and return trace information to the nanobot agent.
- [Analyze] Verify that the AI agent can combine log and trace data to answer natural-language questions about system health under normal and failure conditions.
- [Create] Configure an AI agent with a skill prompt, a cron job, and a multi-step task that chains multiple tools to produce a periodic health report.

In simple words:

> 1. I can explain the difference between logs and traces and when to use each.
> 2. I can add structured logging across services so that every request produces a queryable trail of events.
> 3. I can build MCP tools that let the AI agent search and summarize logs.
> 4. I can build MCP tools that let the AI agent look up and interpret traces.
> 5. I can verify that the agent answers "what went wrong?" correctly when something breaks.
> 6. I can write a skill, configure a cron job, and set up a multi-step agent task that chains log and trace queries into a periodic health report.

## Lab story

The LMS has been running on your VM for weeks — backend, nanobot, Flutter web app, Caddy, PostgreSQL.
The team recently added VictoriaLogs, VictoriaTraces, and an OpenTelemetry Collector to the Docker Compose stack.
The backend is already instrumented with the OpenTelemetry SDK — traces flow into VictoriaTraces and logs are collected by VictoriaLogs — but the logs are still unstructured text, and nobody on the team knows how to use any of it.
When something goes wrong, nobody knows how to find the relevant traces or query the logs effectively.
Your team lead wants you to fix the logging, then wire both systems into the AI agent so anyone can ask about system health in plain language.

A senior engineer explains the assignment:

> 1. Add structured JSON logging across the backend and nanobot so every request — successful or failed — produces a defined sequence of queryable events.
> 2. Extend the nanobot agent with MCP tools that query VictoriaLogs, so users can ask about errors and request history.
> 3. Extend the nanobot agent with MCP tools that query VictoriaTraces, so users can ask about request flow and performance.
> 4. Write an observability skill, configure a cron job for periodic health checks, and verify the agent chains multiple tools in a multi-step investigation.

## Required tasks

### Task 1 — Add Structured Logging and Explore Traces

**Purpose:**

Structured logs with consistent fields turn free-text search into precise, filterable queries.
Traces show how a single request flows across services.
Understanding both data sources directly is a prerequisite for wiring them into the AI agent.

**Summary:**

#### Part A — Add structured logging

Students run `docker compose logs backend` and see unstructured text: Uvicorn startup messages, raw request lines, Python tracebacks.
They try to find "all errors from the backend" in this output and discover it requires fragile text matching.

Students then configure structured JSON logging across the backend and nanobot services.
They set up a JSON log formatter (via Python's logging or a library like `structlog`) so every entry has consistent fields: `level`, `event`, and `service`.

Next, students add log statements so that a single user request produces a defined sequence of events across services.
The task specifies the expected log sequence for two scenarios: a successful request and a failed request (database down).

**Expected log sequence — happy path** (e.g., user asks "what labs are available?"):

| #   | service | event                 | key fields                                |
| --- | ------- | --------------------- | ----------------------------------------- |
| 1   | nanobot | `ws_message_received` | `chat_id`                                 |
| 2   | nanobot | `tool_call`           | `tool`                                    |
| 3   | backend | `request_started`     | `method`, `path`                          |
| 4   | backend | `auth_success`        |                                           |
| 5   | backend | `db_query`            | `table`, `operation`                      |
| 6   | backend | `request_completed`   | `method`, `path`, `status`, `duration_ms` |
| 7   | nanobot | `tool_result`         | `tool`, `success`                         |
| 8   | nanobot | `ws_message_sent`     | `chat_id`                                 |

**Expected log sequence — error path** (database is down):

| #   | service | event                 | key fields                                     |
| --- | ------- | --------------------- | ---------------------------------------------- |
| 1   | nanobot | `ws_message_received` | `chat_id`                                      |
| 2   | nanobot | `tool_call`           | `tool`                                         |
| 3   | backend | `request_started`     | `method`, `path`                               |
| 4   | backend | `auth_success`        |                                                |
| 5   | backend | `db_query`            | `level: "error"`, `table`, `error`             |
| 6   | backend | `request_completed`   | `method`, `path`, `status: 500`, `duration_ms` |
| 7   | nanobot | `tool_result`         | `tool`, `success: false`                       |
| 8   | nanobot | `ws_message_sent`     | `chat_id`                                      |

Students also add an `auth_failure` event (with `level: "warning"`) for requests with an invalid API key.

Students figure out where in the code each log statement belongs — in the webchat channel (`nanobot_webchat`), the MCP tool server (`lms_mcp`), and the backend (middleware, routes, DB layer).
After redeploying, they trigger both scenarios and verify the full sequences appear in `docker compose logs`.

#### Part B — Explore logs in VictoriaLogs

Students open the VictoriaLogs web UI (vmui) and discover that the same structured logs are queryable with LogsQL — filtering by `service`, `level`, `event`, and time range.
They run the same queries they struggled with in Part A and see how structured fields make them trivial.

Students also use provided `poe` tasks to query VictoriaLogs from the terminal — e.g., `uv run poe logs-search "error"` to search by keyword and `uv run poe logs-count` to count errors per service over a time window.

#### Part C — Explore traces in VictoriaTraces

Students open the VictoriaTraces UI and trigger a request through the Flutter web app.
They find the resulting trace, inspect the span hierarchy, and identify which service each span belongs to.
They then trigger a failure (e.g., stop PostgreSQL) and compare the healthy and error traces — noting where the error appears and how the trace duration changes.

Students also use provided `poe` tasks to query the VictoriaTraces HTTP API (Jaeger-compatible endpoints) — e.g., `uv run poe traces-list` to list recent traces for a service and `uv run poe trace-get <trace-id>` to fetch a specific trace by ID.

**Acceptance criteria:**

- Both services emit JSON-structured log entries with at least `level`, `event`, and `service` fields.
- A successful request produces the happy-path log sequence, visible in `docker compose logs`.
- A failed request (database down) produces the error-path log sequence, with `level: "error"` on the DB query event.
- A request with an invalid API key produces an `auth_failure` event with `level: "warning"`.
- The student can query structured logs in VictoriaLogs by `service`, `level`, and `event` fields.
- The student can use `poe` tasks to search logs and count errors from the terminal.
- The student can find a trace in the VictoriaTraces UI and identify the span hierarchy for a cross-service request.
- The student can use `poe` tasks to list recent traces and fetch a trace by ID.

---

### Task 2 — Connect the Agent to Observability Data

**Purpose:**

Letting the AI agent query logs and traces means users can ask about system health in natural language.
Students first build this with a skill that uses `curl`, then discover why MCP tools are a better approach.

**Summary:**

#### Part A — Skill with `curl`

Students write an observability skill (`workspace/skills/observability/SKILL.md`) that instructs the agent to use `curl` to query the VictoriaLogs and VictoriaTraces HTTP APIs directly.
The skill explains the API endpoints, query syntax, and how to interpret the JSON responses.

After deploying, students ask the agent questions like "any errors in the last hour?" and "show me recent traces for the backend."
The agent figures out the right `curl` commands from the skill instructions, executes them, and summarizes the results.

Students observe the limitations: the skill prompt is long and fragile (API URLs, query syntax, response formats all embedded in prose), the agent sometimes gets the `curl` syntax wrong, and raw JSON responses require the agent to parse and interpret on every call.

#### Part B — Refactor to MCP tools

Students extract the `curl`-based queries into MCP tools with structured inputs and outputs.
They implement at least two log tools (search by keyword/time range, count errors per service) and at least two trace tools (list recent traces, fetch a trace by ID).
Each tool handles the HTTP call, parses the response, and returns a structured result.

Students update the observability skill to reference the MCP tools instead of `curl` commands — the skill becomes shorter and focused on *when* to use each tool rather than *how* to call the API.

After redeploying, students verify the agent answers the same questions correctly, and compare the experience: fewer agent errors, faster responses, and a simpler skill prompt.

**Acceptance criteria:**

- An observability skill exists and is loaded by the agent.
- The agent can answer observability questions using `curl` via the skill (Part A baseline).
- At least two MCP tools for querying VictoriaLogs are registered in the MCP server.
- At least two MCP tools for querying VictoriaTraces are registered in the MCP server.
- The agent answers "any errors in the last hour?" correctly under both normal and failure conditions.
- The agent can fetch and summarize a specific trace by ID.
- The skill prompt is updated to reference MCP tools instead of `curl` commands.
- The MCP server starts without errors after the changes.

---

### Task 3 — Add Multi-Step Investigation and a Cron Health Check

**Purpose:**

A skill that chains multiple tools turns the agent from a single-query helper into an investigator.
A cron job makes the agent proactive instead of reactive.

**Summary:**

#### Part A — Multi-step skill

Students enhance the observability skill from Task 2 to guide multi-step investigations.
For example, the skill should instruct the agent that when asked "what went wrong?", it should first search logs for recent errors, extract a trace ID from the results, then fetch the full trace to show the request flow.
Students also add guidance for summarizing results concisely rather than dumping raw data.

Students verify the multi-step behavior by triggering a failure and asking the agent to investigate — the agent should chain log and trace tools autonomously and produce a coherent summary.

#### Part B — Cron health check

Students configure a cron job in `cron/jobs.json` that runs a periodic health check.
The job uses the `agent_turn` payload kind — it sends a message like "Check for errors in the last 15 minutes and report a summary" to the agent on a schedule (e.g., every 15 minutes).
The agent receives this as a regular message, reasons using the observability skill, calls the log and trace MCP tools, and delivers the result to the webchat channel.

Students verify the cron job fires by setting a short interval (e.g., every 2 minutes), waiting for a cycle, and checking that the agent produced a health report in the Flutter web app.
They also test the multi-step scenario: trigger a failure, wait for the next cron cycle, and verify the agent's report mentions the errors and includes trace information.

**Acceptance criteria:**

- The skill guides the agent to chain log and trace tools for multi-step investigations.
- The agent produces a coherent summary when asked "what went wrong?" after a failure.
- A cron job is configured in `cron/jobs.json` that triggers a periodic health check via `agent_turn`.
- The cron job fires on schedule and the agent delivers a health report to the webchat channel.
- When errors exist, the health report includes information from both log and trace tools.

---

### Task 4 — Diagnose and Fix a Bug Using the Agent

**Purpose:**

Everything students built in Tasks 1–3 is now the tool they use to solve a real problem.
This task proves that observability and an AI agent aren't just infrastructure — they're how you debug a multi-service system when you can't attach a debugger.

**Summary:**

The instructor deploys a version of the backend with a planted bug (e.g., a model field mismatch that causes a specific endpoint to return 500 errors intermittently).
Students are not told what the bug is or where it is — only that "users are reporting errors."

Students ask the agent to investigate.
The agent searches logs for recent errors, finds the affected endpoint and error message, pulls the trace to show which service and span failed, and reports its findings.

Based on the agent's report, students locate the buggy code, fix it, redeploy, and verify the fix by asking the agent again — this time the agent should report no errors.

Students document the investigation: the questions they asked, the agent's responses, the root cause, and the fix.

**Acceptance criteria:**

- The student uses the agent to identify the affected endpoint and error type without prior knowledge of the bug.
- The agent's investigation chains log and trace tools to pinpoint the failure.
- The student fixes the bug in the code and redeploys.
- After the fix, the agent confirms no errors when asked.
- The student documents the investigation steps, root cause, and fix.

---

## Optional task

### Task 1 — Set Up Error Alerting

**Purpose:**

Detecting problems before users report them is the difference between proactive and reactive operations.

**Summary:**

Students configure an alerting pipeline that fires when the error rate crosses a threshold.
They add vmalert (part of the VictoriaMetrics stack) as a Docker Compose service with a LogsQL-based alerting rule — for example, trigger when more than five log entries matching `level: "error"` appear within a 5-minute window.

Fired alerts are visible in the vmalert UI and queryable via its API.
Students add an MCP tool to the nanobot agent that checks vmalert's `/api/v1/alerts` endpoint and reports active alerts.
This way, a user can ask the agent "are there any active alerts?" and get a real answer — closing the loop between observability and the AI assistant.

To verify, students trigger the alert by stopping PostgreSQL and sending several requests, then confirm the alert appears in the vmalert UI and the nanobot agent reports it when asked.

**Acceptance criteria:**

- vmalert is running as a Docker Compose service with at least one LogsQL-based alerting rule.
- The alert fires when the error threshold is exceeded within the configured time window.
- An MCP tool reports active alerts from the vmalert API to the nanobot agent.
- The alerting rule and threshold are configurable without code changes.
