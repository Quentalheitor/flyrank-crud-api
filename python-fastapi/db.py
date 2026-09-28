import os
import re
from bs4 import BeautifulSoup
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine, select
from supabase import Client,create_client,AuthApiError
from gotrue.types import AuthResponse,UserResponse
from llm import schema
import json

load_dotenv(override=True)

postgres_url = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
print(f"--> URL ATUAL DO SUPABASE: {SUPABASE_URL}")
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)



class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool

def get_supabase() -> Client:
    return supabase_client


engine = create_engine(postgres_url)

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

def hello():
    """Returns the aplication name, its version, and a list of its endpoints"""
    return {
        "name": "Base CRUD",
        "version": "1.0",
        "endpoints": ["/tasks", "/health","/tasks/{id}"]
    }

def hstatus():
    """Returns server status"""
    return {"status": "ok"}


def tasklist():
    with Session(engine) as session:
        query = select(Task)
        tasks = session.exec(query).all()
        return tasks

def get_single_tsk(id: int):
    """Returns a task from the list that matches the id inserted in the endpoint"""
    with Session(engine) as session:
        query = select(Task).where(Task.id == id)
        ided_task = session.exec(query).first()
        return ided_task

def title_accept(title: str):
    """Adds a new task through the acceptance of json bodies that contain a "title" keyword and a non-empty value"""
    
    with Session(engine) as session:
        new_tsk = Task(title=title,done=False)
        new_tsk.id = None
        session.add(new_tsk)
        session.commit()
        session.refresh(new_tsk)
        return new_tsk

def update_accept(tsk_upd:dict,id:int):
    """Changes the title and/or the done status of a task that matches the id from the endpoint, it does this through a JSON body"""
    with Session(engine) as session:
        query = session.exec(select(Task).where(Task.id==id)).first()
        if query is None:
            return query
        if "title" in tsk_upd:
            query.title = tsk_upd["title"]
        if "done" in tsk_upd:
            query.done = tsk_upd['done']
        session.add(query)
        session.commit()
        session.refresh(query)
        return query

def delete_tsk(id:int):
    """Deletes the task that matches the id from the endpoint"""
    with Session(engine) as session:
        query = session.exec(select(Task).where(Task.id==id)).first()
        if query is None:
            return query
        session.delete(query)
        session.commit()
        return True

def signupsupa(body:dict):
    if 'email' not in body or 'password' not in body:
        return None
    else:
        try:
            result = supabase_client.auth.sign_up(body)
            return {'message':'user created succesfully', 'user': result.user.model_dump()}
        except Exception as e:
            return {'Error':str(e)}

def signinsupa(email:str,password:str):
    
    try:
        result = supabase_client.auth.sign_in_with_password(credentials={'email':email,'password':password})
        return result
    
    except AuthApiError as e:
        return e
    except Exception as e:
        return {'Error':str(e)}

def logoutsupa():
    try:
        result = supabase_client.auth.sign_out()
        return result
    except AuthApiError as e:
        return e
    except Exception as e:
        return {'Error':str(e)}

def verifytkn(token:str):
    try:
        result = supabase_client.auth.get_user(token)
        return result.user
    
    except AuthApiError as e:
        return e
    except Exception as e:
        return {'Error':str(e)}

def _extract_json(raw_text: str) -> str:
    cleaned = raw_text.strip()
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return cleaned[start_idx : end_idx + 1]
    return cleaned


def ticket_triage(ticket: schema.Input):
    if os.getenv("LLM_STUB", "0") == "1":
        output = {
            "category": "billing",
            "urgency": "low",
            "difficulty": "easy",
            "suggested_team": "finance",
            "confidence": 0.5,
            "reason": "Test stub response satisfying schema.",
        }
        return schema.Output.model_validate(output)

    prompt_path = os.path.join("prompts", "support_ticket_triage-v1.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    client = OpenAI(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        timeout=30.0,
    )
    user_input = ticket.model_dump_json()

    res1 = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
    )

    raw_output_1 = res1.choices[0].message.content or ""
    clean_json_1 = _extract_json(raw_output_1)

    try:
        return schema.Output.model_validate_json(clean_json_1)

    except (schema.ValidationError, json.JSONDecodeError) as e1:
        if isinstance(e1, schema.ValidationError):
            formatted_errors = [
                {
                    "field": ".".join(
                        str(p) for p in err["loc"] if p != "body"
                    ),
                    "message": err["msg"],
                }
                for err in e1.errors()
            ]
        else:
            formatted_errors = [{"field": "json_syntax", "message": str(e1)}]

        repair_instruction = (
            f"Your previous answer was rejected for the following validation errors:\n"
            f"{json.dumps(formatted_errors, indent=2)}\n\n"
            f"Previous broken output:\n{raw_output_1}\n\n"
            f"Return ONLY corrected JSON strictly matching the schema."
        )

        res2 = client.chat.completions.create(
            model=os.getenv("LLM_MODEL"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": raw_output_1},
                {"role": "user", "content": repair_instruction},
            ],
        )

        raw_output_2 = res2.choices[0].message.content or ""
        clean_json_2 = _extract_json(raw_output_2)

        try:
            return schema.Output.model_validate_json(clean_json_2)

        except (schema.ValidationError, json.JSONDecodeError) as e2:
            if isinstance(e2, schema.ValidationError):
                retry_errors = [
                    {
                        "field": ".".join(
                            str(p) for p in err["loc"] if p != "body"
                        ),
                        "message": err["msg"],
                    }
                    for err in e2.errors()
                ]
            else:
                retry_errors = [{"field": "json_syntax", "message": str(e2)}]

            quarantine_entry = {
                "prompt_version": "support_ticket_triage-v1",
                "input": user_input,
                "error": retry_errors,
                "raw_output": raw_output_2,
            }

            os.makedirs("logs", exist_ok=True)
            logs_location = os.path.join("logs", "quarantine.jsonl")
            with open(logs_location, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(quarantine_entry) + "\n")
            return retry_errors