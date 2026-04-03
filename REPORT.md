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

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
