from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI()

@app.get("/")
def hello():
    return {
        "name": "Base CRUD",
        "version": "1.0",
        "endpoints": ["/tasks", "/health"]
    }

@app.get("/health")
def status():
    return {"status": "ok"}

lista = {
    "task1": {"id": "01", "title": "title1", "done": "done1"},
    "task2": {"id": "02", "title": "title2", "done": "done2"},
    "task3": {"id": "03", "title": "title3", "done": "done3"}
}

@app.get("/tasks")
def tasklist():
    return lista

@app.get("/tasks/{id}")
def get_single_tsk(id: str):
    for task in lista.values():
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
