from fastapi import FastAPI, HTTPException, status, Response
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
def hstatus():
    return {"status": "ok"}

lista = {
    "task1": {"id": "1", "title": "title1", "done": "false"},
    "task2": {"id": "2", "title": "title2", "done": "false"},
    "task3": {"id": "3", "title": "title3", "done": "false"}
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

@app.post("/tasks",status_code=status.HTTP_201_CREATED)
async def title_accept(title:dict):
    for x in title.items():
        if x[0] == "title" and x[1].strip() != "":
            tsk_qnt = str(int((next(reversed(lista))[-1]))+1)
            lista[f"task{tsk_qnt}"] = {"id": tsk_qnt, "title":x[1],"done":"false"}
            return list(lista.items())[-1]
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is missing from body or empty")

@app.put("/tasks/{id}",status_code=200)
async def update_accept(update:dict,id:str):
    try:
        for x in lista.values():
            if x["id"] == id:
                if "title" in update:
                    if update["title"].strip() != "":
                        x["title"] = update["title"]
                    else:
                        raise KeyError
                if "done" in update:
                    if update["done"].strip() != "":
                        x["done"] = update["done"]
                    else: raise KeyError
                return x
    except KeyError: raise HTTPException(status_code=404, detail="Invalid payload")
    raise HTTPException(status_code=404, detail="Invalid payload")

@app.delete("/tasks/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_tsk(id:str):
    for x in lista.values():
        if x["id"] == id:
            del lista[f"task{id}"]
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404,detail="Missing id")




    
            

            
            


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
