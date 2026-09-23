# FlyRank Backend Track — Task CRUD API

A RESTful CRUD API built with Python, FastAPI, SQLModel, and PostgreSQL. The application manages task lifecycles with strict HTTP status handling, input validation, and database persistence.

The project traces the evolution of backend storage across three distinct phases:
1. **Week 2 (A1):** Volatile in-memory data structures.
2. **Week 3 (A2):** Embedded disk persistence via SQLite.
3. **Week 3 (A3):** Production-grade containerized PostgreSQL stack orchestrated with Docker Compose.

---

## Quick Start — One-Command Stack (A3)

To run the entire application and its PostgreSQL database from scratch on any machine:

```bash
# 1. Clone the repository and enter the project root
git clone https://github.com/Quentalheitor/flyrank-crud-api.git
cd flyrank-crud-api

# 2. Configure environment secrets from the template
cp python-fastapi/.env.example python-fastapi/.env

# 3. Build and launch all services in detached mode
docker compose up -d --build
```

- **API Base URL:** `http://localhost:8000`
- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Database Connection:** `localhost:5432`

To shut down the stack while keeping database data intact:

```bash
docker compose down
```

---

## Environment Variables & Configuration

The application reads database connection parameters from environment variables. For local standalone execution, copy the example template into a local `.env` file:

```bash
cp python-fastapi/.env.example python-fastapi/.env
```

### Required Variables (`.env.example`)

| Variable | Description | Example / Default Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | Full connection URI for SQLAlchemy / Psycopg | `postgresql+psycopg://postgres:dev@localhost:5432/tasks` |

> **Note on Docker Compose:** When executing via `docker compose up`, the `api` service automatically communicates with the database container via Compose internal DNS using the host service name `db` (`postgresql+psycopg://postgres:dev@db:5432/tasks`).

---

## API Endpoints

The API maintains an identical HTTP contract across all storage migrations:

| Method | Endpoint | Description | Request Body | Expected Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API metadata and endpoint directory | None | `200 OK` |
| `GET` | `/health` | Server health status check | None | `200 OK` |
| `GET` | `/tasks` | Retrieve all persistent tasks | None | `200 OK` |
| `GET` | `/tasks/{id}` | Retrieve a specific task by its ID | None | `200 OK`, `404 Not Found` |
| `POST` | `/tasks` | Create a new task with auto-incremented ID | `{"title": "string"}` | `201 Created`, `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update a task's title and/or boolean status | `{"title": "string", "done": bool}` | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete a task from the database | None | `204 No Content` (empty body), `404 Not Found` |

---

## Live curl Verification

Sample verification command demonstrating status codes, headers, and payload serialization from the containerized PostgreSQL database:

```bash
$ curl -i http://localhost:8000/tasks/1

HTTP/1.1 200 OK
date: Wed, 23 Sep 2026 03:15:00 GMT
server: uvicorn
content-length: 45
content-type: application/json

{"id":1,"title":"title1","done":false}
```

Sample error validation verifying the required JSON error contract:

```bash
$ curl -i http://localhost:8000/tasks/999

HTTP/1.1 404 Not Found
date: Wed, 23 Sep 2026 03:15:30 GMT
server: uvicorn
content-length: 27
content-type: application/json

{"error":"Task not found"}
```

---

## Repository Structure

```text
flyrank-crud-api/
├── .gitignore
├── README.md
├── compose.yml                     # Multi-container orchestration specification
├── node-express/                   # Auxiliary track scaffold (Express)
│   ├── index.js
│   ├── package-lock.json
│   └── package.json
├── python-fastapi/                 # Primary backend track (FastAPI + SQLModel)
│   ├── .dockerignore               # Build context ignore rules
│   ├── .env.example                # Sanitized credentials template
│   ├── Dockerfile                  # API container image recipe
│   ├── Screenshots/                # Stage checkpoints & database verifications
│   │   ├── Step_4_A2_sc.png
│   │   ├── Step_5_sc.png
│   │   └── Step_5_A3_sc.png
│   ├── db.py                       # Repository module (SQLModel & database engine)
│   ├── main.py                     # HTTP route controllers & app lifespan
│   └── requirements.txt            # Pinned dependencies (FastAPI, Psycopg, etc.)
└── ai-version/                     # Auxiliary baseline implementations
    └── main.py
```

---

## Week 3 — Assignment A3: Containerized Postgres

### Architectural Separation (`main.py` & `db.py`)

The codebase enforces strict boundary separation between HTTP handling and database persistence:

- **HTTP Interface Layer (`main.py`):** Owns route endpoints, parameter parsing, HTTP status resolution, custom error payload shaping (`{"error": ...}`), and server lifecycle events (`lifespan`).
- **Repository Layer (`db.py`):** Owns the SQLModel table schema, connection engine, session transactions, and CRUD functions. Route handlers never interact with `Session` or SQL expressions directly.

### Persistence & Docker Volumes

PostgreSQL runs inside a container using `postgres:16-alpine` and stores all data inside the container path `/var/lib/postgresql/data`.

- **Data Durability:** A named volume (`taskdata`) is mounted to the Postgres data path. When the container stack is stopped or removed via `docker compose down`, task data outlives the container lifecycle and reloads automatically upon subsequent restarts.
- **Idempotent Seeding:** On startup, the application verifies whether the `task` table contains existing rows. Exactly three example tasks are inserted on the initial boot only, preventing record duplication on server reloads.

### Stage 0 — A Real Database in One Command

Docker Desktop installed and confirmed:

```bash
docker --version
```

Postgres container started with a named volume for persistence:

```bash
docker run --name flyrank-postgres \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=tasks \
  -p 5432:5432 \
  -v flyrank-postgres-data:/var/lib/postgresql/data \
  -d postgres
```

Verified the container is running and the SQL prompt is accessible:

```bash
docker ps
docker exec -it flyrank-postgres psql -U postgres -d tasks
```

SQL prompt output:

```sql
psql (18.6 (Debian 18.6-1.pgdg13+2))
Type "help" for help.

tasks=# SELECT 1;
 ?column?
----------
        1
(1 row)
```

### Database Verification Proof

Inspection performed directly inside the running database container via `psql`:

```bash
docker compose exec db psql -U postgres -d tasks
```

```sql
tasks=# \dt
        List of relations
 Schema | Name | Type  |  Owner
--------+------+-------+----------
 public | task | table | postgres
(1 row)

tasks=# SELECT * FROM task;
 id | title  | done
----+--------+------
  1 | title1 | f
  2 | title2 | f
  3 | title3 | f
(3 rows)
```

![Database Verification](python-fastapi/Screenshots/Step_5_A3_sc.png)

---

## Week 3 — Assignment A2: SQLite Persistence

### Why SQLite?

- **Native to Python — No Installation Required:** SQLite ships as part of Python's standard library via the built-in `sqlite3` module. No separate database server, driver installation, or system-level dependency is needed — it works out of the box in any standard Python environment.
- **Single-File Database:** The entire database — schema, data, and indexes — is stored in a single file on disk (`tasks.db`). This makes the project trivially portable: copying or deleting the file is all it takes to move or reset the database.
- **Zero Configuration:** There is no server process to start, no port to open, no credentials to configure, and no connection string beyond a local file path. The engine initializes itself on first run and is ready immediately.
- **True Persistence:** Tasks, status changes, and newly created records are written directly to disk, ensuring that all data survives server restarts — the core limitation addressed in this migration from A1.
- **Automatic Provisioning:** The database file and table schema are automatically initialized on server startup if they do not already exist.
- **Clean Cloning:** `tasks.db` is included in `.gitignore`, allowing fresh clones of the repository to start from a clean baseline and execute the idempotent seeding logic on initial run.

### Setup & Running the Server (A2)

```bash
# 1. Navigate to the primary Python track directory
cd python-fastapi

# 2. Create and activate an isolated Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install project dependencies
pip install -r requirements.txt

# 4. Start the FastAPI development server on port 8000
uvicorn main:app --reload --port 8000
```

One-line start command:

```bash
cd python-fastapi && uvicorn main:app --reload --port 8000
```

- **API Base URL:** `http://localhost:8000`
- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`

### Data Persistence & Storage Layer

In Week 2 (A1), records lived in process memory and vanished whenever the server stopped. In Week 3 (A2), the storage layer was replaced with SQLite without changing external route contracts:

- **Database Engine:** SQLite via SQLModel / SQLAlchemy engine.
- **Storage Location:** `python-fastapi/tasks.db`.
- **Idempotent Seeding:** On startup, the application queries the row count of the tasks table. Exactly three pre-seeded tasks are inserted **only if the table is empty**, preventing data multiplication across subsequent restarts.
- **SQL Safety:** All record queries, updates, and deletes utilize parameterized query binding via the ORM, preventing SQL injection vulnerabilities.

### Stage 4: Manual SQL Exploration

Direct database inspection was performed using DBeaver 26.2.0 connected to the local SQLite database file (`Task.db`):

![DBeaver SQL Exploration](python-fastapi/Screenshots/Step_4_A2_sc.png)

#### Example Query Executed

```sql
SELECT * FROM task t;
```

- **Execution Outcome:** Fetched all 3 initial task rows (`id`: 1, 2, 3; `title`: "title1", "title2", "title3"; `done`: 0) directly from disk in 0.002 seconds.
- **Observation:** Data altered directly via SQL statements (e.g., `UPDATE task SET done = 1 WHERE id = 1;`) is reflected immediately on subsequent API `GET /tasks` requests without requiring a server reboot, proving that the SQLite database file serves as the single source of truth.

### Live curl Verification (A2)

```bash
$ curl -i http://localhost:8000/tasks/1

HTTP/1.1 200 OK
date: Tue, 22 Sep 2026 00:45:00 GMT
server: uvicorn
content-length: 45
content-type: application/json

{"id":1,"title":"title1","done":false}
```

---

## Week 2 — Assignment A1: In-Memory Storage

### Setup & Running the Server (A1)

```bash
# 1. Navigate to the primary Python track directory
cd python-fastapi

# 2. Create and activate an isolated Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install project dependencies
pip install -r requirements.txt

# 4. Start the FastAPI development server on port 8000
uvicorn main:app --reload --port 8000
```

- **API Base URL:** `http://localhost:8000`
- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`

### JavaScript / Node.js Lane (`node-express/`)

The `node-express/` folder is maintained as an auxiliary workspace to replicate the identical task CRUD API specification using Node.js, Express, and `swagger-ui-express`. The primary submission and live documentation currently focus on the **Python / FastAPI** lane.

### In-Memory Storage & The Mortality Observation

This application stores records in-memory using an internal Python list rather than a persistent database.

- **Behavior on Restart:** Any new tasks created or existing tasks modified/deleted through the endpoints only remain in existence while the server process runs. Stopping or restarting the Uvicorn server completely resets all records back to the initial seed tasks.
- **Why This Occurs:** Volatile system RAM holds in-memory variables. Once the process lifecycle ends, memory allocation clears immediately. This exercise highlights the stateless operational loop of web servers and demonstrates why persistent database systems are required in backend architectures.

### Interactive Documentation (Swagger UI)

Interactive testing for the complete CRUD cycle was validated using FastAPI's automatic Swagger UI documentation:

![Swagger UI](python-fastapi/Screenshots/Step_5_sc.png)

### Live curl Verification (A1)

```bash
$ curl -i http://localhost:8000/tasks/1

HTTP/1.1 200 OK
date: Tue, 15 Sep 2026 18:45:00 GMT
server: uvicorn
content-length: 47
content-type: application/json

{"id":"1","title":"title1","done":false}
```

---

## AI vs Me — Assignment A1

### My Prompt

> Acting as a backend engineer, I need you to build a basic CRUD API using uvicorn, FastAPI, and Python 3. The API interacts with tasks which are composed of an id, title, and "done" boolean status. It has to have the following endpoints: "/" with a hello method which returns the API name, version, and a list of all endpoints; "/health" which shows the status of the server with a simple message; "/tasks" which has a GET method that lists all the tasks in the in-memory list, and a POST method which adds a new task through a JSON body containing a "title" key with a non-empty value; "/tasks/{id}" which has a GET method which returns the task with the matching id from the endpoint, a PUT method which changes the title and/or the done status of a task that matches the id from the endpoint through a JSON body, and finally a DELETE method which removes the task from the list with the matching id from the endpoint. All of the endpoints also have to be able to handle errors and output the correct status code for the situation.

### What did the AI do better — and do I understand its version well enough to explain it?

The AI used Pydantic `BaseModel` schemas (`TaskCreate`, `TaskUpdate`, `Task`) with typed fields and `@field_validator` decorators instead of raw `dict` parameters. This is the correct FastAPI pattern — FastAPI uses these models to auto-generate the request/response documentation in Swagger UI and to reject malformed input before it even reaches the route handler. It also replaced the dictionary of string-keyed task dicts with a `dict[int, Task]` keyed by integer IDs, making lookups a simple `tasks_db.get(task_id)` instead of a `for` loop scanning every value. Both improvements are legitimate and I can explain them — they are standard FastAPI practice.

### What did the AI get wrong or quietly ignore from my prompt?

Two concrete gaps. First, the AI started with an **empty in-memory store** (`tasks_db = {}`), so `GET /tasks` on a fresh server returns an empty list; the assignment explicitly requires 3 pre-seeded example tasks. Second, the AI used **integer IDs** (`id: int`) while my hand-built version used string IDs (`"id": "1"`); beyond the type mismatch, the AI's `DELETE` endpoint also failed to return a proper `404` when a non-existent ID was requested on the first generation.

### What did my prompt forget to specify — and what did the AI silently decide for you?

At least three things were left unspecified. First, whether the list should be **pre-seeded** — the AI defaulted to empty. Second, the **ID type** — integer vs string — which the AI chose on its own. Third, whether `PUT` should reject a payload that contains **neither** `title` nor `done` — the AI added that validation rule without being asked. It also silently added a `"message"` field to the `/health` response and made the root `/` return a richer JSON structure, both unrequested.

### The Rematch

After adding explicit requirements for 3 pre-seeded tasks, integer IDs starting at 1, and exact status codes per endpoint to the prompt, the regenerated version started the server with the correct seed data, used consistent integer IDs throughout, and matched the hand-built status code behaviour across all endpoints.