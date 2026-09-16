import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator, model_validator

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="A lightweight CRUD API for managing tasks.",
)

# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------
class Task(BaseModel):
    id: str
    title: str
    done: bool = False


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title cannot be empty")

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title must contain at least one non-whitespace character")
        return cleaned


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Title must contain at least one non-whitespace character")
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def verify_at_least_one_field(self) -> "TaskUpdate":
        if self.title is None and self.done is None:
            raise ValueError("At least one field ('title' or 'done') must be provided")
        return self


# ---------------------------------------------------------
# In-Memory Storage (Pre-seeded)
# ---------------------------------------------------------
tasks_db: Dict[str, Task] = {
    "1": Task(id="1", title="Set up environment and dependencies", done=True),
    "2": Task(id="2", title="Implement CRUD endpoints with FastAPI", done=False),
    "3": Task(id="3", title="Write automated tests", done=False),
}


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/", status_code=status.HTTP_200_OK)
def root(request: Request):
    """Returns API metadata and registered application routes."""
    endpoints = []
    for route in request.app.routes:
        if hasattr(route, "methods"):
            # Exclude internal/docs endpoints for cleaner output
            if route.path not in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}:
                endpoints.append({
                    "path": route.path,
                    "methods": sorted(list(route.methods - {"HEAD", "OPTIONS"}))
                })

    return {
        "name": app.title,
        "version": app.version,
        "endpoints": sorted(endpoints, key=lambda x: x["path"]),
    }


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Simple server health status check."""
    return {
        "status": "healthy",
        "message": "Server is operational"
    }


@app.get("/tasks", response_model=List[Task], status_code=status.HTTP_200_OK)
def list_tasks():
    """Lists all existing tasks in memory."""
    return list(tasks_db.values())


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    """Creates a new task with a generated string ID."""
    task_id = str(uuid.uuid4())
    new_task = Task(id=task_id, title=payload.title, done=False)
    tasks_db[task_id] = new_task
    return new_task


@app.get("/tasks/{id}", response_model=Task, status_code=status.HTTP_200_OK)
def get_task(id: str):
    """Retrieves a single task by ID."""
    task = tasks_db.get(id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{id}' was not found.",
        )
    return task


@app.put("/tasks/{id}", response_model=Task, status_code=status.HTTP_200_OK)
def update_task(id: str, payload: TaskUpdate):
    """Updates title and/or done status of an existing task."""
    task = tasks_db.get(id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{id}' was not found.",
        )

    updated_title = payload.title if payload.title is not None else task.title
    updated_done = payload.done if payload.done is not None else task.done

    updated_task = Task(id=id, title=updated_title, done=updated_done)
    tasks_db[id] = updated_task
    return updated_task


@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: str):
    """Deletes a task by ID."""
    if id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{id}' was not found.",
        )
    del tasks_db[id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)