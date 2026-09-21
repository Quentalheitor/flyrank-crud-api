from fastapi import FastAPI, HTTPException, status, Response
from contextlib import asynccontextmanager
from typing import Optional
from sqlmodel import Field, SQLModel, Session, create_engine, select
import uvicorn

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool

sqlite_file_name = "Task.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing_task = session.exec(select(Task)).first()
        if not existing_task:
            session.add_all([
                    Task(title="title1",done= False),
                    Task(title="title2",done=False),
                    Task(title="title3",done=False)
            ])
            session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
def hello():
    """Returns the aplication name, its version, and a list of its endpoints"""
    return {
        "name": "Base CRUD",
        "version": "1.0",
        "endpoints": ["/tasks", "/health","/tasks/{id}"]
    }

@app.get("/health")
def hstatus():
    """Returns server status"""
    return {"status": "ok"}

lista = {
    "task1": {"id": "1", "title": "title1", "done": False},
    "task2": {"id": "2", "title": "title2", "done": False},
    "task3": {"id": "3", "title": "title3", "done": False}
}

@app.get("/tasks")
def tasklist():
    """Returns the current in-memory list of tasks """
    return lista

@app.get("/tasks/{id}")
def get_single_tsk(id: str):
    """Returns a task from the list that matches the id inserted in the endpoint"""
    for task in lista.values():
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")

@app.post("/tasks",status_code=status.HTTP_201_CREATED)
async def title_accept(title:dict):
    """Adds a new task through the acceptance of json bodies that contain a "title" keyword and a non-empty value"""
    for x in title.items():
        if x[0] == "title" and x[1].strip() != "":
            tsk_qnt = str(int((next(reversed(lista))[-1]))+1)
            ntask = {"id": tsk_qnt, "title":x[1],"done":False}
            lista[f"task{tsk_qnt}"] = ntask            
            return ntask
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is missing from body or empty")

@app.put("/tasks/{id}",status_code=200)
async def update_accept(update:dict,id:str):
    """Changes the title and/or the done status of a task that matches the id from the endpoint, it does this through a JSON body"""
    try:
        for x in lista.values():
            if x["id"] == id:
                if "title" in update:
                    if update["title"].strip() != "":
                        x["title"] = update["title"]
                    else:
                        raise KeyError
                if "done" in update:
                    if isinstance(update["done"], bool):
                        x["done"] = update["done"]
                    else: raise KeyError
                return x
    except KeyError: raise HTTPException(status_code=400, detail="Invalid payload")
    raise HTTPException(status_code=404, detail="ID not found")

@app.delete("/tasks/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_tsk(id:str):
    """Deletes the task that matches the id from the endpoint"""
    for x in lista.values():
        if x["id"] == id:
            del lista[f"task{id}"]
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404,detail="Missing id")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
