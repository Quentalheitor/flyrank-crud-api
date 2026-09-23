import os
from typing import Optional
from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine, select

load_dotenv()


postgres_url = os.getenv("DATABASE_URL")
print(postgres_url)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool



sqlite_file_name = "Task.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
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