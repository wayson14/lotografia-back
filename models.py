from pydantic import BaseModel # data validation library
from sqlmodel import Field, Session, Relationship, SQLModel, create_engine, select

### === SECURITY AND AUTH DATA MODELS === ###
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


### USER 
class User(SQLModel, table=True): # define a user model using Pydantic BaseModel class
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str | None = Field(default=None, index=True, unique=True)
    full_name: str | None = Field(default=None)
    disabled: bool | None = Field(default=False)
    hashed_password: str | None = Field(default=None, index=True)

    projects: list["Project"] = Relationship(back_populates="user")

# class UserCreate(User):
#     password: str

    

# class UserPublic(User):
#     id: int



# class UserUpdate(User): ### for PATCH requests - update model
#     username: str | None = None
#     email: str | None = None
#     full_name: str | None = None
#     disabled: bool | None = None
#     password: str | None = None
 



### PROJECT
class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    
    user_id: int | None = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="projects")

# class ProjectPublic(Project):
#     id: int 

# class ProjectCreate(Project):
#     pass    

# class ProjectUpdate(Project): ### for PATCH requests - update model
#     user_id: int | None = None
#     name: str | None = None
#     description: str | None = None  


