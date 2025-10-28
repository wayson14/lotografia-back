import pytest
from sqlmodel import select, Session

from models import User
from db_connector import engine


def get_user(username: str):
    with Session(engine) as session:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).one()
        return user

def test_get_user():
    user = get_user("test")
    assert user.username == "test"

if __name__ == "__main__":
    print(get_user(username="test"))