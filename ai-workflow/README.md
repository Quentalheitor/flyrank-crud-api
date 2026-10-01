# Visual AI Workflow Engine

A visual graph orchestration app where every node is an autonomous **AI decision step** that resolves strictly to **YES** or **NO**. You build the workflow on an interactive canvas (**React Flow**), and it runs durably through **Inngest**: each node is evaluated by an LLM (Gemini), and the answer decides which branch the engine follows next.

> This project lives in the `ai-workflow/` folder of the [`flyrank-crud-api`](https://github.com/Quentalheitor/flyrank-crud-api) monorepo. All commands below are run from inside that folder.

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Requirements](#requirements)
5. [Installation & Setup](#installation--setup)
6. [Environment Variables](#environment-variables)
7. [End-to-End Testing Walkthrough](#end-to-end-testing-walkthrough)
8. [API Reference](#api-reference)
9. [Project Structure](#project-structure)
10. [Verification & Build](#verification--build)
11. [Design Notes & Known Limitations](#design-notes--known-limitations)
12. [Troubleshooting](#troubleshooting)

---

## How It Works

```text
┌────────────────────────────────────────────────────────┐
│                   Next.js Frontend                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │        React Flow Interactive Canvas             │  │
│  │  • Custom Decision Nodes (prompt per node)       │  │
│  │  • YES / NO source handles + labeled edges       │  │
│  │  • Animated traversed edges                      │  │
│  │  • Execution logs drawer, JSON export / import   │  │
│  └──────────────────────────┬───────────────────────┘  │
└─────────────────────────────┼──────────────────────────┘
                              │  POST /api/workflow/run
                              ▼
┌────────────────────────────────────────────────────────┐
│                 Inngest Orchestration                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Durable Step Traversal Engine           │  │
│  │                                                  │  │
│  │  [Root Node] ──step.run()──► LLM (Gemini)        │  │
│  │        │                                         │  │
│  │        ├── "YES" ──► follow the YES edge         │  │
│  │        └── "NO"  ──► follow the NO edge          │  │
│  │                                │                 │  │
│  │  [Next Node] ──step.run()──────┘                 │  │
│  └──────────────────────────┬───────────────────────┘  │
└─────────────────────────────┼──────────────────────────┘
                              │  writes after every step
                              ▼
                  In-memory execution store
                              ▲
                              │  GET /api/workflow/status (polled every 700 ms)
                      Frontend live updates
```

1. **Graph representation.** A workflow is a directed graph built from custom React Flow nodes (`DecisionNode`) and edges (`DecisionEdge`). Each node holds a title and an *evaluation prompt*. Each node has two bottom handles, `yes` (green) and `no` (red); an edge created from a handle is tagged with that branch.
2. **Triggering.** Clicking **Run Workflow** sends the whole graph plus the input text (the *context*) to `POST /api/workflow/run`, which emits a `workflow/execute` event to Inngest.
3. **Root selection.** The engine starts at the first node with no incoming edges (falling back to the first node in the list).
4. **Isolated, durable steps.** Every node evaluation runs inside its own `step.run("evaluate-node-<nodeId>", …)`, so each decision is retried and recorded independently by Inngest. The LLM is called at `temperature: 0` with the input context and the node's prompt, and is instructed to answer only `YES` or `NO`.
5. **Branch resolution.** After each decision the engine looks at the node's outgoing edges, picks the one whose branch matches the answer, and moves to its target. The run **ends when the current node has no edge for the decision it just made** (e.g. a leaf node).
6. **Live status.** After every step the engine writes the execution path and step results into an in-memory store. The frontend polls `/api/workflow/status`, updates node badges, animates the traversed edges, and fills the logs drawer.

---

## Features

**Visual editor**
- Interactive React Flow canvas with custom nodes, bezier edges with `YES` / `NO` badges, background grid, controls and minimap.
- Symmetrical YES / NO source handles with enlarged hit areas; the prompt textarea is excluded from node dragging.
- Dynamic pan boundary (`translateExtent`) that grows with your nodes so the viewport never gets lost.
- Add new decision nodes, edit prompts inline, reset to the default graph.
- Automatic persistence in `localStorage` (key: `ai-workflow-graph-v1`).

**Execution engine**
- Each node is an isolated Inngest step, visible in the Inngest dev dashboard.
- Binary evaluation via Gemini through its OpenAI-compatible endpoint (default model `gemini-2.5-flash-lite`).
- **Mock mode**: with no API key the engine returns random YES/NO decisions so you can test the full flow without credentials.
- Status and polling endpoints for live progress.

**Execution experience**
- Result badges (green `YES` / red `NO`) on every evaluated node.
- Traversed edges become animated, thicker and glow.
- Top-right **Execution Status** panel with the status and the path taken.
- **Execution Logs** drawer: run ID, evaluated input, execution path, and per-step prompt, decision, note and timestamp.
- **Export / Import JSON** to save and reload workflows as files.

---

## Tech Stack

| Area | Technology |
|---|---|
| Framework | Next.js 16 (App Router), React 19, TypeScript |
| Styling / UI | Tailwind CSS 4, shadcn/ui, Radix UI, lucide-react |
| Canvas | `@xyflow/react` (React Flow) v12 |
| Orchestration | Inngest v4 (durable `step.run` execution) |
| LLM client | `openai` SDK pointed at Gemini's OpenAI-compatible endpoint |

---

## Requirements

- **Node.js 22 or newer** (Next.js 16 needs ≥ 20.9 and the `openai` SDK declares ≥ 22; Node 22 satisfies both)
- **npm** (a `package-lock.json` is included)
- **Inngest CLI**, run on demand with `npx` (no global install needed)
- **Internet access** while developing/building, because the app loads the Geist fonts from Google Fonts via `next/font/google`
- **Google Gemini API key**: *optional*. Without one the engine runs in mock mode (random decisions).

---

## Installation & Setup

1. **Clone the repository and install dependencies**

   ```bash
   git clone https://github.com/Quentalheitor/flyrank-crud-api.git
   cd flyrank-crud-api/ai-workflow
   npm install
   ```

2. **Create your environment file** (see [Environment Variables](#environment-variables)):

   ```bash
   touch .env.local
   ```

3. **Start the Next.js dev server** (Terminal 1):

   ```bash
   npm run dev
   ```

   The app runs at <http://localhost:3000>.

4. **Start the Inngest Dev Server** (Terminal 2):

   ```bash
   npx inngest-cli@latest dev
   ```

   The Inngest dashboard runs at <http://localhost:8288>. It auto-discovers the app on port 3000. If it doesn't, point it at the endpoint explicitly:

   ```bash
   npx inngest-cli@latest dev -u http://localhost:3000/api/inngest
   ```

---

## Environment Variables

Create `ai-workflow/.env.local` (all `.env*` files are git-ignored):

```env
# Gemini API key (used through the OpenAI-compatible endpoint)
LLM_API_KEY=your_gemini_api_key_here

# Optional: model name (default: gemini-2.5-flash-lite)
LLM_MODEL=gemini-2.5-flash-lite

# Only needed for production deployments of Inngest
# INNGEST_SIGNING_KEY=
# INNGEST_EVENT_KEY=
```

| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | No | Gemini API key. If missing or set to `dummy-key`, the engine switches to **mock mode**. |
| `LLM_MODEL` | No | Model used for evaluations. Defaults to `gemini-2.5-flash-lite`. |
| `INNGEST_SIGNING_KEY` / `INNGEST_EVENT_KEY` | Production only | Not needed with the local Inngest Dev Server. |

> **Mock mode:** each node returns a **random** YES/NO (50/50) and its step note reads `[DEV MOCK] Simulated decision because LLM_API_KEY is not set.` Use it to test plumbing, not decision quality. The expected outcomes in the walkthrough below need a real `LLM_API_KEY`.
>
> **Using OpenAI instead of Gemini:** the base URL is hard-coded to Gemini's endpoint in `src/inngest/workflow-engine.ts`. An OpenAI key will not work unless you change `baseURL` there and set `LLM_MODEL` accordingly.

Restart `npm run dev` after changing environment variables.

---

## End-to-End Testing Walkthrough

Run both servers first (see [Installation & Setup](#installation--setup)). For steps 3 and 4 use a real `LLM_API_KEY`.

### 1. Verify function discovery

- Open the Inngest dashboard at <http://localhost:8288>.
- Under **Functions**, confirm **Execute AI Workflow** is listed with the trigger `workflow/execute`.

### 2. Canvas and editor operations

- Open <http://localhost:3000> and confirm the 3 default nodes:
  - **Inquiry Classifier**: "Is this request asking for technical support?"
  - **Urgency Check**: "Is this a critical system outage?"
  - **Sales Triage**: "Is this an enterprise lead with > 50 seats?"
- Default edges: Inquiry Classifier **YES** → Urgency Check, Inquiry Classifier **NO** → Sales Triage.
- Click **Add Decision Node** to spawn a new node.
- Drag from a node's bottom-left green handle (**YES**) or bottom-right red handle (**NO**) to another node's top handle to draw a labeled edge.
- Edit a prompt in any node's textarea, then refresh the browser to confirm the change persisted via `localStorage`.

### 3. Technical-support outage path

1. Click the green **Run Workflow** button.
2. Enter this input:

   ```text
   Hi team, our production database cluster has completely crashed. Customers cannot log in or check out!
   ```

3. Click **Run**.
4. **Expected result:**
   - The header dot turns amber and pulses, and the button reads **Evaluating...** while the run is in progress.
   - **Inquiry Classifier** → **YES** (green badge); traversal follows the YES edge to **Urgency Check**.
   - **Urgency Check** → **YES** (green badge). It has no outgoing edges, so the run ends.
   - Traversed edges animate and glow.
   - The top-right panel shows status `completed` and `Path taken: node-1 → node-2`.

### 4. Sales path (alternate branch)

1. Click **Run Workflow** again.
2. Enter this input:

   ```text
   Hello, we are an enterprise organization with 250 team members looking for licensing pricing.
   ```

3. Click **Run**.
4. **Expected result:**
   - **Inquiry Classifier** → **NO** (red badge); traversal follows the NO edge to **Sales Triage**.
   - **Sales Triage** → **YES** (green badge).
   - The panel shows `Path taken: node-1 → node-3`.

### 5. Inspect the logs drawer and Inngest steps

- Click **View Logs** (it appears after the first run) or click the Execution Status panel.
- The **Execution Logs** drawer shows the run ID, the evaluated input, the execution path, and a card per step (`#1`, `#2`, …) with the node title, YES/NO badge, prompt and timestamp.
- In Inngest (<http://localhost:8288>), open the latest run under **Runs** and check the step timeline: `evaluate-node-node-1`, then `evaluate-node-node-2` (or `-node-3`).

### 6. JSON export and import

1. Click **Export JSON** to download `ai-workflow-<timestamp>.json`.
2. Click **Reset Flow** to restore the default graph.
3. Click **Import JSON** and select the downloaded file. Your custom nodes, positions, prompts and edges should be restored.

### 7. Mock mode (no API key)

1. Remove `LLM_API_KEY` (or set it to `dummy-key`) and restart `npm run dev`.
2. Run any input. The run still completes, the decisions are random, and each step in the logs drawer shows the `[DEV MOCK]` note.

### 8. Error handling

- **Inngest not running:** stop the Inngest Dev Server and click **Run**. You should get an alert saying the Inngest Dev Server is not running, with the command to start it.
- **Empty graph (API):**

  ```bash
  curl -s -X POST http://localhost:3000/api/workflow/run \
    -H "Content-Type: application/json" \
    -d '{"workflowId":"wf_empty","inputContext":"x","nodes":[],"edges":[]}'
  # → {"error":"Graph has no nodes"}   (HTTP 400)
  ```

### 9. Testing the API without the UI

```bash
# Trigger a two-node workflow
curl -s -X POST http://localhost:3000/api/workflow/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflowId": "wf_curl_1",
    "inputContext": "Our production database is down and nobody can log in!",
    "nodes": [
      { "id": "node-1", "type": "decisionNode", "position": { "x": 0, "y": 0 },
        "data": { "title": "Inquiry Classifier", "evaluationCriteria": "Is this request asking for technical support?" } },
      { "id": "node-2", "type": "decisionNode", "position": { "x": 0, "y": 300 },
        "data": { "title": "Urgency Check", "evaluationCriteria": "Is this a critical system outage?" } }
    ],
    "edges": [
      { "id": "edge-1-2", "source": "node-1", "sourceHandle": "yes", "target": "node-2",
        "type": "decisionEdge", "data": { "branch": "YES" } }
    ]
  }'

# Poll the result
curl -s "http://localhost:3000/api/workflow/status?workflowId=wf_curl_1"
```

---

## API Reference

### `POST /api/workflow/run`

Validates the graph, pre-populates the execution store (so the first poll has data) and sends the `workflow/execute` event to Inngest.

**Body**

| Field | Type | Description |
|---|---|---|
| `workflowId` | string | Unique run identifier, used later to poll status |
| `inputContext` | string | The text every node evaluates |
| `nodes` | `DecisionNodeType[]` | `{ id, type: "decisionNode", position, data: { title, evaluationCriteria } }` |
| `edges` | `DecisionEdgeType[]` | `{ id, source, sourceHandle: "yes" \| "no", target, type: "decisionEdge", data: { branch: "YES" \| "NO" } }` |
| `startNodeId` | string (optional) | Force the starting node instead of auto-detecting the root |

**Responses**

| Status | Body |
|---|---|
| `200` | `{ "success": true, "eventId": "...", "message": "Workflow triggered successfully" }` |
| `400` | `{ "error": "Graph has no nodes" }` |
| `500` | `{ "error": "..." }`, including a hint to start the Inngest Dev Server when the connection is refused |

### `GET /api/workflow/status?workflowId=<id>`

| Status | Body |
|---|---|
| `200` | `{ "status": "pending" }` if the run is unknown |
| `200` | The execution state: `workflowId`, `status` (`running` or `completed`), `inputContext`, `executionPath` (node IDs in order), `stepResults` (per node: `nodeTitle`, `prompt`, `decision`, optional `reasoning`, `timestamp`) |
| `400` | `{ "error": "Missing workflowId parameter" }` |

### `/api/inngest`

The Inngest serve handler (`GET`, `POST`, `PUT`). The Inngest Dev Server uses it to discover and invoke the `Execute AI Workflow` function (function id `execute-ai-workflow`, app id `flyrank-ai-workflow`).

---

## Project Structure

```text
ai-workflow/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── inngest/route.ts           # Inngest serve handler
│   │   │   └── workflow/
│   │   │       ├── run/route.ts           # Dispatches the workflow/execute event
│   │   │       └── status/route.ts        # Polling endpoint for run status and step results
│   │   ├── globals.css                    # Tailwind CSS and theme tokens
│   │   ├── layout.tsx                     # Root layout and fonts
│   │   └── page.tsx                       # Canvas page, toolbar, run dialog, polling logic
│   ├── components/
│   │   ├── flow/
│   │   │   ├── decision-node.tsx          # Custom node with prompt textarea and YES/NO handles
│   │   │   ├── decision-edge.tsx          # Custom bezier edge with YES/NO badge
│   │   │   └── execution-logs-sheet.tsx   # Slide-over execution logs drawer
│   │   └── ui/                            # shadcn/ui primitives (button, card, dialog, sheet, badge, ...)
│   ├── inngest/
│   │   ├── client.ts                      # Inngest client (app id: flyrank-ai-workflow)
│   │   └── workflow-engine.ts             # Traversal engine and LLM evaluation steps
│   ├── lib/
│   │   ├── execution-store.ts             # In-memory store that survives dev hot reloads
│   │   └── utils.ts                       # Tailwind class merge helper (cn)
│   └── types/
│       └── workflow.ts                    # Shared payload / result types
├── package.json
├── tsconfig.json
└── next.config.ts
```

---

## Verification & Build

```bash
# Type check
# Next.js generates the global LayoutProps type; on a fresh clone run typegen first
npx next typegen
npx tsc --noEmit

# Production build
npm run build

# Lint
npm run lint
```

> `npx tsc --noEmit` on a brand-new clone fails with `Cannot find name 'LayoutProps'` until Next.js has generated its types. `npx next typegen`, `npm run dev` and `npm run build` all generate them.

---

## Design Notes & Known Limitations

- **In-memory execution store.** Run state lives in a process-level `Map`. It is lost on server restart and is not shared across multiple server instances or serverless invocations. For production, swap it for a shared store (Redis, a database).
- **Acyclic graphs only.** The engine does not detect cycles; a looping graph will not terminate cleanly. Keep workflows as DAGs.
- **Strict binary parsing.** A model response containing `YES` counts as YES; anything else, including an unexpected reply, counts as NO. Responses are capped at 5 tokens.
- **Polling window.** The frontend polls every 700 ms for up to 30 attempts (about 21 seconds) and then stops. Longer runs keep going in Inngest, but the UI stops updating.
- **Input is interpolated into the prompt.** The input context is placed directly in the evaluation prompt, so untrusted input can attempt prompt injection. Treat decisions as advisory unless inputs are trusted.
- **Gemini endpoint is hard-coded** (see the OpenAI note under [Environment Variables](#environment-variables)).

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Alert: "Inngest Dev Server is not running" | Start it in a second terminal: `npx inngest-cli@latest dev` |
| `Execute AI Workflow` is missing in the Inngest dashboard | Make sure `npm run dev` is running first, then start Inngest, or use `-u http://localhost:3000/api/inngest` |
| Run never leaves `running` / UI stops updating | Check the run in the Inngest dashboard; the UI polling stops after about 21 seconds |
| Decisions look random and notes say `[DEV MOCK]` | `LLM_API_KEY` is missing or `dummy-key`; add a real key and restart `npm run dev` |
| `Failed to fetch Geist from Google Fonts` | The machine is offline or behind a proxy; set `HTTP_PROXY` / `HTTPS_PROXY` or switch to `next/font/local` |
| `Cannot find name 'LayoutProps'` from `tsc` | Run `npx next typegen` first |
| Canvas reset to something unexpected | Clear the `ai-workflow-graph-v1` key in `localStorage`, or click **Reset Flow** |