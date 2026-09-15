# FlyRank Backend Track — Task CRUD API (Week 2 Assignment A1)

A RESTful in-memory CRUD API built with Python and FastAPI to manage a task list across standard HTTP methods, data validations, and status codes.

---

## Setup & Running the Server (Python / FastAPI)

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

## JavaScript / Node.js Lane (`node-express/`)

The `node-express/` folder is maintained as an auxiliary workspace to replicate the identical task CRUD API specification using Node.js, Express, and `swagger-ui-express`.

The primary submission and live documentation currently focus on the **Python / FastAPI** lane. The JavaScript track serves as a parallel implementation to be completed subsequently.

---

## API Endpoints

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

## In-Memory Storage & The Mortality Observation

This application stores records in-memory using an internal Python list rather than a persistent database.

* **Behavior on Restart:** Any new tasks created or existing tasks modified/deleted through the endpoints only remain in existence while the server process runs. Stopping or restarting the Uvicorn server completely resets all records back to the initial seed tasks.
* **Why This Occurs:** Volatile system RAM holds in-memory variables. Once the process lifecycle ends, memory allocation clears immediately. This exercise highlights the stateless operational loop of web servers and demonstrates why persistent database systems are required in backend architectures.

---

## Interactive Documentation (Swagger UI)

Interactive testing for the complete CRUD cycle was validated using FastAPI's automatic Swagger UI documentation:

![Swagger UI](python-fastapi/Screenshots/Step_5_sc.png)

---

## Live curl Verification

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

## Repository Structure

```text
flyrank-crud-api/
├── .gitignore
├── README.md
├── node-express/          # Secondary track scaffold (Express)
│   ├── index.js
│   ├── package-lock.json
│   └── package.json
└── python-fastapi/        # Primary track (FastAPI)
    ├── Screenshots/
    │   └── Step_5_sc.png
    ├── main.py
    └── requirements.txt
```