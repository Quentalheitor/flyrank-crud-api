from fastapi import FastAPI, HTTPException, status, Response
from contextlib import asynccontextmanager
import uvicorn
import db
from fastapi.responses import JSONResponse





@asynccontextmanager
async def lifespan(app: FastAPI):
    db.create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
def hero_route():
    return {"message": "FlyRank Auth API running", "version": "1.0"}

@app.get("/health")
def status_route():
    return db.hstatus()


@app.get("/tasks", response_model=list[db.Task])
async def task_listing():
    return db.tasklist()


@app.get("/tasks/{id}")
async def get_task_by_id(id: int):
    result = db.get_single_tsk(id=id)
    if result is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,content={'error':'Task not found'})
    else:
        return result

@app.post("/auth/signup",status_code=status.HTTP_201_CREATED)
async def signup(body:dict):
    result = db.signupsupa(body=body)
    if result == None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={'error':"Bad Request"})
    elif 'Error' in result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=result)
    else:
        return result
        
@app.post("/auth/login",status_code=status.HTTP_200_OK)
async def signin(email:str,password:str):
    if email.strip() =="" or password.strip() == "":
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={'error':'Invalid payload'})
    else:
        result = db.signinsupa(email=email,password=password)
        if isinstance(result,db.AuthApiError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={"Erro":result.message})
        else:
            return {"Access token":result.session.access_token,"Refresh token":result.session.refresh_token}


            

@app.post("/tasks",status_code=status.HTTP_201_CREATED)
async def add_task_by_title(title:str):
    if isinstance(title,str) and title.strip() != "":
        return db.title_accept(title=title)
    else:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={'error':'Empty title'})
        
        

@app.put("/tasks/{id}",status_code=200)
async def update_tsk(update:dict,id:int):
    tsk_upd = {}
    if "title" in update and isinstance(update["title"],str) and update["title"].strip() != "":
        tsk_upd['title'] = update['title']
    if "done" in update and isinstance(update["done"], bool):
        tsk_upd["done"] = update["done"]
    if len(tsk_upd) <=0:
        raise HTTPException(status_code=400, detail="Invalid payload")
    result = db.update_accept(tsk_upd=tsk_upd,id=id)
    if result is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,content={'error':'Task not found'})
    else:
        return result



@app.delete("/tasks/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(id:int):
    result =  db.delete_tsk(id=id)
    if result is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,content={'error':'Task not found'})
    elif result == True:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
