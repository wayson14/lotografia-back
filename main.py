#!/usr/bin/env python3

### === IMPORTS === ###
### Standard library
from datetime import datetime, timedelta
import os

from typing import Annotated

### Backend frameworks (FastAPI is built on Starlette)
import uvicorn # ASGI server
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Request, Response
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.formparsers import MultiPartParser # framework, on top of which FastAPI is built

### NiceGUI TODO: move it to another file


### Own modules
# TODO: change for specific imports
from auth import *
from models import *
from views import *

### === CONSTANTS AND SWITCHES === ###
fastapi_app = FastAPI()

MultiPartParser.spool_max_size = 1024 * 1024 * 1024 * 20  # 20 GiB




### === Endpoints === ###
@fastapi_app.post("/token") # endpoint to obtain a JWT token needed to access protected routes
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
    
### WITH NO JWT (left here for learning purposes) ###
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


# @fastapi_app.get("/users/me/items/")
# async def read_own_items(current_user):
#     return [{"item_id": "Foo", "owner": current_user.username}]

@fastapi_app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
    ):
    return current_user


@fastapi_app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@fastapi_app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


### ROOT
@fastapi_app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI! Browse to /gui to see the NiceGUI app.'}


# UI

ui.run_with(
    fastapi_app,
    mount_path='/app',  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
    storage_secret='pick your private secret here',  # NOTE setting a secret is optional but allows for persistent storage per user
)



if __name__ == '__main__':
    uvicorn.run('main:fastapi_app', host='127.0.0.1', port=8000, log_level='info')