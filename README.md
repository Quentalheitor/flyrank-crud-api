# FlyRank Backend Track — Task CRUD API

A RESTful CRUD API built with Python and FastAPI to manage a task list across standard HTTP methods, data validations, and status codes. The project spans two assignments: Week 2 (A1) uses in-memory storage, and Week 3 (A2) migrates to a persistent SQLite database.

---

## Week 2 — Assignment A1: In-Memory Storage

### Setup & Running the Server

Run the following commands from the repository root to configure the virtual environment and start the development server:

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

* **API Base URL:** `http://localhost:8000`
* **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`

---

### JavaScript / Node.js Lane (`node-express/`)

The `node-express/` folder is maintained as an auxiliary workspace to replicate the identical task CRUD API specification using Node.js, Express, and `swagger-ui-express`.

The primary submission and live documentation currently focus on the **Python / FastAPI** lane. The JavaScript track serves as a parallel implementation to be completed subsequently.

---

### API Endpoints

| Method | Endpoint | Description | Request Body | Expected Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API metadata and endpoint directory | None | `200 OK` |
| `GET` | `/health` | Server health status check | None | `200 OK` |
| `GET` | `/tasks` | Retrieve all in-memory tasks | None | `200 OK` |
| `GET` | `/tasks/{id}` | Retrieve a specific task by its ID | None | `200 OK`, `404 Not Found` |
| `POST` | `/tasks` | Create a new task with auto-incremented ID | `{"title": "string"}` | `201 Created`, `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update a task's title and/or boolean status | `{"title": "string", "done": bool}` | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete a task from memory | None | `204 No Content` (empty body), `404 Not Found` |

---

### In-Memory Storage & The Mortality Observation

This application stores records in-memory using an internal Python list rather than a persistent database.

* **Behavior on Restart:** Any new tasks created or existing tasks modified/deleted through the endpoints only remain in existence while the server process runs. Stopping or restarting the Uvicorn server completely resets all records back to the initial seed tasks.
* **Why This Occurs:** Volatile system RAM holds in-memory variables. Once the process lifecycle ends, memory allocation clears immediately. This exercise highlights the stateless operational loop of web servers and demonstrates why persistent database systems are required in backend architectures.

---

### Interactive Documentation (Swagger UI)

Interactive testing for the complete CRUD cycle was validated using FastAPI's automatic Swagger UI documentation:

![Swagger UI](python-fastapi/Screenshots/Step_5_sc.png)

---

### Live curl Verification

Sample command demonstrating response headers and status codes via `curl -i`:

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

### AI vs Me — Assignment A1

#### My Prompt

> Acting as a backend engineer, I need you to build a basic CRUD API using uvicorn, FastAPI, and Python 3. The API interacts with tasks which are composed of an id, title, and "done" boolean status. It has to have the following endpoints: "/" with a hello method which returns the API name, version, and a list of all endpoints; "/health" which shows the status of the server with a simple message; "/tasks" which has a GET method that lists all the tasks in the in-memory list, and a POST method which adds a new task through a JSON body containing a "title" key with a non-empty value; "/tasks/{id}" which has a GET method which returns the task with the matching id from the endpoint, a PUT method which changes the title and/or the done status of a task that matches the id from the endpoint through a JSON body, and finally a DELETE method which removes the task from the list with the matching id from the endpoint. All of the endpoints also have to be able to handle errors and output the correct status code for the situation.

#### What did the AI do better — and do I understand its version well enough to explain it?

The AI used Pydantic `BaseModel` schemas (`TaskCreate`, `TaskUpdate`, `Task`) with typed fields and `@field_validator` decorators instead of raw `dict` parameters. This is the correct FastAPI pattern — FastAPI uses these models to auto-generate the request/response documentation in Swagger UI and to reject malformed input before it even reaches the route handler. It also replaced the dictionary of string-keyed task dicts with a `dict[int, Task]` keyed by integer IDs, making lookups a simple `tasks_db.get(task_id)` instead of a `for` loop scanning every value. Both improvements are legitimate and I can explain them — they are standard FastAPI practice.

#### What did the AI get wrong or quietly ignore from my prompt?

Two concrete gaps. First, the AI started with an **empty in-memory store** (`tasks_db = {}`), so `GET /tasks` on a fresh server returns an empty list; the assignment explicitly requires 3 pre-seeded example tasks. Second, the AI used **integer IDs** (`id: int`) while my hand-built version used string IDs (`"id": "1"`); beyond the type mismatch, the AI's `DELETE` endpoint also failed to return a proper `404` when a non-existent ID was requested on the first generation.

#### What did my prompt forget to specify — and what did the AI silently decide for you?

At least three things were left unspecified. First, whether the list should be **pre-seeded** — the AI defaulted to empty. Second, the **ID type** — integer vs string — which the AI chose on its own. Third, whether `PUT` should reject a payload that contains **neither** `title` nor `done` — the AI added that validation rule without being asked. It also silently added a `"message"` field to the `/health` response and made the root `/` return a richer JSON structure, both unrequested.

#### The Rematch

After adding explicit requirements for 3 pre-seeded tasks, integer IDs starting at 1, and exact status codes per endpoint to the prompt, the regenerated version started the server with the correct seed data, used consistent integer IDs throughout, and matched the hand-built status code behaviour across all endpoints.

---

## Week 3 — Assignment A2: SQLite Persistence

### Why SQLite?

* **Zero Configuration & Serverless:** SQLite runs as an embedded library rather than an external server process. The entire database is contained within a single file (`tasks.db`).
* **True Persistence:** Tasks, status changes, and newly created records are written directly to disk, ensuring that all data persists across server restarts.
* **Automatic Provisioning:** The database file and table schema are automatically initialized on server startup if they do not exist.
* **Clean Cloning:** `tasks.db` is included in `.gitignore`, allowing fresh clones of the repository to start from a clean baseline and execute the idempotent seeding logic on initial run.

---

### Setup & Running the Server

Run the following commands from the repository root to configure the virtual environment and start the development server:

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

* **One-line start command:**
```bash
cd python-fastapi && uvicorn main:app --reload --port 8000
```

* **API Base URL:** `http://localhost:8000`
* **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`

---

### API Endpoints

The API maintains an identical contract and response structure to Assignment A1:

| Method | Endpoint | Description | Request Body | Expected Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API metadata and endpoint directory | None | `200 OK` |
| `GET` | `/health` | Server health status check | None | `200 OK` |
| `GET` | `/tasks` | Retrieve all persistent tasks from SQLite | None | `200 OK` |
| `GET` | `/tasks/{id}` | Retrieve a specific task by its ID | None | `200 OK`, `404 Not Found` |
| `POST` | `/tasks` | Create a new task with auto-incremented ID | `{"title": "string"}` | `201 Created`, `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update a task's title and/or boolean status | `{"title": "string", "done": bool}` | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete a task from the SQLite database | None | `204 No Content` (empty body), `404 Not Found` |

---

### Data Persistence & Storage Layer

In Week 2 (Assignment A1), records lived in process memory and vanished whenever the server stopped. In Week 3 (Assignment A2), the storage layer was replaced with SQLite without changing external route contracts:

* **Database Engine:** SQLite via SQLModel / SQLAlchemy engine.
* **Storage Location:** `python-fastapi/tasks.db`.
* **Idempotent Seeding:** On startup, the application queries the row count of the tasks table. Exactly three pre-seeded tasks are inserted **only if the table is empty**, preventing data multiplication across subsequent restarts.
* **SQL Safety:** All record queries, updates, and deletes utilize parameterized query binding via the ORM, preventing SQL injection vulnerabilities.

---

### Stage 4: Manual SQL Exploration

Direct database inspection was performed using a GUI database viewer (DBeaver) connected to the local SQLite database file:

#### Example Query Executed

```sql
SELECT * FROM task;
```

* **Execution Outcome:** Fetched all 3 initial task rows (`id`: 1, 2, 3; `title`: "title1", "title2", "title3"; `done`: 0) directly from disk in 0.001 seconds.
* **Observation:** Data altered directly via SQL statements (e.g., `UPDATE task SET done = 1 WHERE id = 1;`) is reflected immediately on subsequent API `GET /tasks` requests without requiring a server reboot, proving that the SQLite database file serves as the single source of truth.

---

### Live curl Verification

Sample command demonstrating persistence and response status codes via `curl -i`:

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

### AI vs Me — Assignment A2

#### My Prompt

> Acting as a backend engineer, migrate my FastAPI task CRUD API from an in-memory list to a persistent SQLite database using SQLModel or raw sqlite3. The API interacts with tasks containing an integer primary key `id`, text `title`, and boolean `done` (default false). The database file must be named `tasks.db` and created automatically if missing. Ensure the tasks table is created automatically, and seed three initial tasks only if the table is empty so data does not multiply on server restarts. Preserve all five endpoints (`GET /tasks`, `GET /tasks/{id}`, `POST /tasks`, `PUT /tasks/{id}`, `DELETE /tasks/{id}`) with the exact same request/response contracts, validation rules (400 on empty title, 404 on unknown ID), and status codes (200, 201, 204, 400, 404). All database operations must use parameterized queries.

#### What did the AI do better — and do I understand its version well enough to explain it?

The AI implementation properly structured database sessions using FastAPI's dependency injection (`Depends(get_session)`), wrapping session management inside generator contexts. This cleanly handles opening, committing, and closing connections per request, avoiding open connection leaks during unexpected exceptions.

#### What did the AI get wrong or quietly ignore from my prompt?

On initial generation, the AI attempted to create tables on every startup without verifying if seed rows already existed, which resulted in duplicate sample tasks being appended on each restart until explicit check logic (`select(Task).first()`) was introduced. Additionally, the AI initially attempted to return a JSON body on the `DELETE /tasks/{id}` route instead of an empty body with status `204 No Content`.

#### What did my prompt forget to specify — and what did the AI silently decide for you?

The prompt did not specify how SQLite's multithreading flag should be handled. By default, SQLite checks threads strictly; the AI silently added `connect_args={"check_same_thread": False}` to the engine setup, which is necessary for FastAPI's asynchronous threadpool workers. It also decided the exact schema table name (`task` vs `tasks`) based on SQLModel class name conventions.

#### The Rematch

Refining the prompt to explicitly require FastAPI's `lifespan` event handler, an explicit table name `__tablename__ = "tasks"`, an idempotent count check prior to seeding, and an empty 204 response for deletions produced a clean, single-file implementation matching the manual solution.

---

## Repository Structure

```text
flyrank-crud-api/
├── .gitignore
├── README.md
├── node-express/          # Secondary track scaffold (Express)
│   ├── index.js
│   ├── package-lock.json
│   └── package.json
├── python-fastapi/        # Primary track (FastAPI + SQLModel)
│   ├── Screenshots/
│   │   └── Step_5_sc.png
│   ├── main.py
│   └── requirements.txt
└── ai-version/            # AI-generated implementations
    └── main.py
```