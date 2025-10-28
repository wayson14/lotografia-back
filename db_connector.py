from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

from models import * 

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args = connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

class DBConnector():
    def get_user(self, username: str) -> User | None:
        with Session(engine) as session:
            user = session.exec(
                select(User).where(User.username == username)
            ).first()
            return user
        
    def get_projects(self, username: str) -> list["Project"] | None:
        with Session(engine) as session:
            user = session.exec(
                select(User).where(User.username == username)
            ).first()
            return user.projects
    

def test_dbconnector_get_projects():
    db = DBConnector()
    assert db.get_projects(username="test") == []
    


SessionDep = Annotated[Session, Depends(get_session)]

