from fastapi import FastAPI, HTTPException, status, Response, Header,Depends,Request
from contextlib import asynccontextmanager
import uvicorn
import db
import inngest
from inngest import fast_api
from datetime import timedelta
import logging
from fastapi.exceptions import RequestValidationError
from llm import schema
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.encoders import jsonable_encoder
from typing import Optional

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
  if not credentials or not credentials.credentials:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "Access token required"},
    )

  token = credentials.credentials
  result = db.verifytkn(token)

  if isinstance(result, db.AuthApiError):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "Invalid or expired token"},
    )
  elif isinstance(result, Exception):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"error": f"Auth error: {str(result)}"},
    )

  return result

reports = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.create_db_and_tables()
    yield

inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)

# Create an Inngest function
@inngest_client.create_function(
    fn_id="say-hello",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    ctx.logger.info(ctx.event)
    await ctx.step.sleep("sleep-5-seconds", timedelta(seconds=8))
    return "Hello from the background!"

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requests")
)
async def make_report(ctx: inngest.Context):
    ctx.logger.info(ctx.event)
    await ctx.step.sleep("sleep-8-seconds",timedelta(seconds=5))
    def compute_report():
        body = reports[ctx.event.data['id']]
        body.update({"status":"done"})
        reports[body['id']]['status'] = 'done'
        reports[body['id']]['result'] = f"Report data for {body['topic']}"
    await ctx.step.run("process output",compute_report)
    return "Saved report processed and saved in reports"

app = FastAPI(lifespan=lifespan)

inngest.fast_api.serve(app, inngest_client, [say_hello,make_report])

@app.post("/test-hello")
async def trigger_hello():
    ids = await inngest_client.send(
        inngest.Event(name="test/hello", data={"msg": "Hello!"})
    )
    return ids

@app.post("/reports")
async def report_body(body:dict):
    result = db.clean_report(body=body)
    ids = await inngest_client.send(
        inngest.Event(name="report/requests", data={"id": result.id,"topic":result.topic,"status":result.status}))
    if isinstance(ids,list):
        report = {"id": result.id,"topic":result.topic,"status":result.status}
        reports[result.id] = report
        print(reports)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,content={'id':result.id,'status':'pending'})
    else:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get("/reports/{report_id}")
async def find_report(report_id:str):
    if report_id in reports:
        return reports[report_id]
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,content={"message":"Could not find report with matching id"})



@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append({
            "field": ".".join(str(p) for p in error["loc"] if p != "body"),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": formatted_errors}
    )

@app.get("/")
def hero_route():
    return {"message": "FlyRank Auth API running", "version": "1.0"}

@app.get("/health")
def status_route():
    return JSONResponse(status_code=status.HTTP_200_OK,content=db.hstatus)

@app.get("/tasks/{id}")
async def get_task_by_id(id: int):
    result = db.get_single_tsk(id=id)
    if result is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,content={'error':'Task not found'})
    else:
        return result

@app.get("/public/info")
def info_status_msg():
    return JSONResponse(status_code=status.HTTP_200_OK, content={ "message": "Welcome stranger! This info is public." })
    
@app.get("/protected/profile", status_code=status.HTTP_200_OK)
async def protected_profile(user=Depends(get_current_user)):
  return {
      "id": user.id,
      "email": user.email,
      "account_created_at": str(user.created_at),
  }

@app.get("/protected/dashboard")
async def dashboard(user=Depends(get_current_user)):
    return {
      "id": user.id,
      "email": user.email,
      "account_created_at": str(user.created_at),
  }
    
@app.post("/auth/signup",status_code=status.HTTP_201_CREATED)
async def signup(body: dict):
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

@app.post("/auth/logout",status_code=status.HTTP_204_NO_CONTENT)
async def logout(user=Depends(get_current_user)):
    result = db.logoutsupa()
    if isinstance(result,db.AuthApiError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail={'Error':result.message})
    elif isinstance(result,dict) and result['Error']:
        return result
    else:
        return


            

@app.post("/tasks",status_code=status.HTTP_201_CREATED)
async def add_task_by_title(title:str):
    if isinstance(title,str) and title.strip() != "":
        return db.title_accept(title=title)
    else:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={'error':'Empty title'})
        
@app.post("/triage", status_code=status.HTTP_200_OK)
async def support_ticket(ticket: schema.Input):
    if isinstance(ticket, schema.Input):
        result = db.ticket_triage(ticket=ticket)
        if result == "LLM disabled":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=jsonable_encoder({"message": "Service unavailable at the moment"})
            )
        elif isinstance(result, schema.Output):
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
        elif isinstance(result, list) and len(result) > 0:
            first_err = result[0]
            if first_err.get("field") == "Timeout error":
                return JSONResponse(status_code=status.HTTP_504_GATEWAY_TIMEOUT, content=jsonable_encoder(first_err))
            elif "code" in first_err:
                return JSONResponse(status_code=first_err["code"], content=jsonable_encoder(first_err))
            else:
                return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=jsonable_encoder(result))
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Internal error"})

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
