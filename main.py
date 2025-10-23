#!/usr/bin/env python3
import os
import uuid
from pathlib import Path
import uvicorn # ASGI server
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from nicegui import app, ui, events
from starlette.formparsers import MultiPartParser # framework, on top of which FastAPI is built
from pydantic import BaseModel # data validation library
### Security
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from typing import Annotated
from pwdlib import PasswordHash
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


MultiPartParser.spool_max_size = 1024 * 1024 * 1024 * 20  # 20 GiB
fastapi_app = FastAPI()
UPLOAD_DIR = Path.cwd() / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

### OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# TODO: implement environmental in production
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        # hashed value stored in a database must be a real hash - otherwise it breaks the hashing verification...
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}


    


### === Endpoints ==== ###
### Security experiments
def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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

password_hash = PasswordHash.recommended() # from pwdlib


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    
def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# def fake_decoded_token(token):
#     # totally not secure - for demo purposes only
#     user = get_user(fake_users_db, token)
#     return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None: 
        raise credentials_exception
    return user

async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@fastapi_app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        # "sub" stems from "subject" and is a standard defined in JWT docs
        data = {"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")
    
### WITH NO JWT ###
# @fastapi_app.post("/token") # according to OAuth2 spec, this response must be a JSON object
# async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
#     user_dict = fake_users_db.get(form_data.username)
#     if not user_dict:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")
#     user = UserInDB(**user_dict) 
#     hashed_password = fake_hash_password(form_data.password)
#     if not hashed_password == user.hashed_password:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")
    
#     # this access token should be something unique and secret
#     return {"access_token": user.username, "token_type": "bearer"} 


@fastapi_app.get("/users/me/items/")
async def read_own_items(current_user):
    return [{"item_id": "Foo", "owner": current_user.username}]

@fastapi_app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
    ):
    return current_user

# @fastapi_app.get("/users/me/items/")
# async def read_own_items(
#     current_user: Annotated[User, Depends(get_current_active_user)],
# ):
#     return [{"item_id": "Foo", "owner": current_user.username}]

# experiment of checking the activity status
# @fastapi_app.get("/users/me/is_active")
# async def read_users_me(current_active_user: Annotated[User, Depends(get_current_active_user)]):
#     return current_active_user

@fastapi_app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

### Logic functions
async def handle_upload(e: events.UploadEventArguments):
    filename = f"{uuid.uuid4().hex}_{Path(e.file.name).name}"
    dest = UPLOAD_DIR / filename
    await e.file.save(dest)
    print(dest)

### ROOT
@fastapi_app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI! Browse to /gui to see the NiceGUI app.'}


# UI
@ui.page('/')
async def show():
    ui.label('Hello, NiceGUI!')
    # NOTE dark mode will be persistent for each user across tabs and server restarts
    ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
    ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
    ui.upload(multiple=True,on_upload=handle_upload).classes('max-w-full' )

ui.run_with(
    fastapi_app,
    mount_path='/app',  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
    storage_secret='pick your private secret here',  # NOTE setting a secret is optional but allows for persistent storage per user
)



if __name__ == '__main__':
    uvicorn.run('main:fastapi_app', host='127.0.0.1', port=8000, log_level='info')