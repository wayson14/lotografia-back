#!/usr/bin/env python3

### === IMPORTS === ###
### Standard library
from datetime import datetime, timedelta
import os
import time
from typing import Annotated, Optional

### Backend frameworks (FastAPI is built on Starlette)
import uvicorn # ASGI server
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Request, Response
from fastapi import Depends, FastAPI, HTTPException, status, Query
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.formparsers import MultiPartParser # framework, on top of which FastAPI is built
from starlette.middleware.base import BaseHTTPMiddleware

### NiceGUI TODO: move it to another file
# from nicegui import app, ui, events

### Own modules
# TODO: change for specific imports
from auth import *
from models import *
from views import *
from db_connector import create_db_and_tables, get_session, SessionDep

### === CONSTANTS AND SWITCHES === ###
fastapi_app = FastAPI()

MultiPartParser.spool_max_size = 1024 * 1024 * 1024 * 20  # 20 GiB

@fastapi_app.on_event("startup")
def on_startup():
    create_db_and_tables()

### === Endpoints === ###
### HEROES ENDPOINTS ###
@fastapi_app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep ):
    hashed_password = get_password_hash(hero.password)
    extra_data = {"hashed_password": hashed_password}
    db_hero = Hero.model_validate(hero, update=extra_data) # here we inject data before it is stored
  
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@fastapi_app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hero]:
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

@fastapi_app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@fastapi_app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}

@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDep):
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset = True)
    hero_data = hero.model_dump(exclude_unset=True)
    hero_db.sqlmodel_update(hero_data)
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db
###################################

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


### === MIDDLEWARES === ###
### EXPERIMENTAL
# passwords = {'user1': 'pass1', 'user2': 'pass2'}
# unrestricted_page_routes = {'/app/login'}
# class AppAuthMiddleware(BaseHTTPMiddleware):
#     """This middleware restricts access to all NiceGUI pages.

#     It redirects the user to the login page if they are not authenticated.
#     """

#     async def dispatch(self, request: Request, call_next):
#         if not app.storage.user.get('authenticated', False):
#             if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
#                 return RedirectResponse(f'/app/login?redirect_to={request.url.path}')
#         return await call_next(request)

# app.add_middleware(AppAuthMiddleware)

# @fastapi_app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.perf_counter()
#     response = await call_next(request)
#     process_time = time.perf_counter() - start_time
#     response.headers["X-Process-Time"] = str(process_time)
#     return response


### ROOT
@fastapi_app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI! Browse to /app to see the NiceGUI app.'}


# UI
@ui.page('/login')
def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    def login():
        if 'username' in app.storage.user.keys():
            if app.storage.user['username'] == username.value:
                ui.notify('You are already logged in.', color='info')
                return
        
        
        user = authenticate_user(fake_users_db, username.value, password.value)
        if not user:
            ui.notify('Login failed. Please check your credentials.', color='negative')
            return
        app.storage.user['username'] = user.username
        app.storage.user['authenticated'] = True
        ui.notify('Login successful!', color='positive')
        ui.navigate.to("/")
    
    def logout():
        if app.storage.user:
            app.storage.user["username"] = None
            app.storage.user["authenticated"] = False
            ui.notify('Logged out successfully.', color='positive')
        else:
            ui.notify('You are not logged in.', color='info')

    ui.label(app.storage.user.get('username', None)).bind_text_from(app.storage.user, 'username')

    username = ui.input('Username').on('keydown.enter', login)
    password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', login)
    
    ui.button('Log in', on_click=login)
    ui.button('Log out', on_click=logout)
    ui.button('Go to root', on_click = lambda: ui.navigate.to("/"))



ui.run_with(
    fastapi_app,
    mount_path='/app/',  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
    storage_secret='pick your private secret here',  # NOTE setting a secret is optional but allows for persistent storage per user
)



if __name__ == '__main__':
    uvicorn.run('main:fastapi_app', host='127.0.0.1', port=8000, log_level='info')