from pydantic import BaseModel # data validation library
from sqlmodel import Field, Session, SQLModel, create_engine, select

### SECURITY DATA MODELS ###
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel): # define a user model using Pydantic BaseModel class
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str


### HERO MODELS ### (for every CRUD operation there exists a separate data model)
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str
    hashed_password: str = Field()


class HeroPublic(HeroBase):
    id: int

class HeroCreate(HeroBase):
    secret_name: str
    password: str

class HeroUpdate(HeroBase): ### for PATCH requests - update model
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None
    password: str | None = None


