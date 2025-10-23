from pydantic import BaseModel # data validation library


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


### OTHER MODELS ###