#!/usr/bin/env python3

### === IMPORTS === ###
### Standard library
from datetime import datetime, timedelta
import os
import time
from typing import Annotated, Optional
import functools

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
from db_connector import create_db_and_tables, get_session, SessionDep, engine, DBConnector
# from db_connector import create_heroes

### === CONSTANTS AND SWITCHES === ###
fastapi_app = FastAPI()
MultiPartParser.spool_max_size = 1024 * 1024 * 1024 * 20  # 20 GiB

db = DBConnector()

USER_PROJECTS_PATH = os.path.join("user_projects") 

@fastapi_app.on_event("startup")
def on_startup():
    create_db_and_tables()
    if not os.path.exists(USER_PROJECTS_PATH):
        os.makedirs(USER_PROJECTS_PATH)


@fastapi_app.post("/token") # endpoint to obtain a JWT token needed to access protected routes
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    auth_result = authenticate_user(form_data.username, form_data.password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = db.get_user(form_data.username)
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

@fastapi_app.get("/users/me", response_model=UserPublic)
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
    return {'message': 'Hello, FastAPI! Browse to /app to see the NiceGUI app.'}

# APP LOGIC
UPLOAD_DIR = Path.cwd() / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

### Logic functions
async def page_reload():
    ui.run_javascript('location.reload();')

async def handle_upload(e: events.UploadEventArguments, destination=""):
    filename = f"{uuid.uuid4().hex}_{Path(e.file.name).name}"
    dest = UPLOAD_DIR / filename
    if len(destination)>0:
        dest =os.path.join(destination, Path(e.file.name).name) 
    await e.file.save(dest)
    print(dest)
    await page_reload()


def is_authenticated():
    return True


### LOGIC DECORATORS
def check_if_authenticated():
    def decorator(func):
        @functools.wraps(func)  # For preserving the metadata of func.
        def wrapper(*args, **kwargs):
            # Do stuff before func possibly using arg...
            print("AUTH DECORATOR")
            if app.storage.user.get("authenticated") != True:
                print("aaa")
                ui.navigate.to("/login")
                return
            else:  
                print("bbb")
                return  func(*args, **kwargs)
            # Do stuff after func possibly using arg...
            # return result

        return wrapper

    return decorator


### === UI === ###
def navbar():
    with ui.row():
        ui.button('Go to root', on_click = lambda: ui.navigate.to("/"))
        ui.button('Go to projects', on_click = lambda: ui.navigate.to("/projects"))
        ui.button('Go to login', on_click = lambda: ui.navigate.to("/login"))


### WELCOME
@ui.page('/')
async def show():
    navbar()
    ui.label("username").bind_text_from(app.storage.user, "username")
    ui.label('Hello, NiceGUI!')
    # NOTE dark mode will be persistent for each user across tabs and server restarts
    ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
    ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
    ui.upload(multiple=True,on_upload=handle_upload).classes('max-w-full' )

### LOGIN
@ui.page('/login')
def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    navbar()
    def login():
        if 'username' in app.storage.user.keys():
            if app.storage.user['username'] == username.value:
                ui.notify('You are already logged in.', color='info')
                return
        
        
        user = authenticate_user(username.value, password.value)
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
    ui.button('Go to projects', on_click = lambda: ui.navigate.to("/projects"))


### PROJECT CREATION
@ui.page("/add-project")
def add_project():
    navbar()
    def add_project_handler():
        ### Database section
        with Session(engine) as session:
            current_user = session.exec(
                select(User).where(User.username == app.storage.user["username"])
            ).one()
            if current_user.projects != []: 
                other_project_names = list(map(lambda project: project.name, current_user.projects))
                print(other_project_names)
                if project_name.value in other_project_names:
                    raise ValueError("Project with this name already created for this user!")
                
            new_project = Project(
                name = project_name.value,
                description = project_description.value,
                user = current_user
            )
            session.add(new_project)
            
            ### Storage creation section
            project_id = session.exec(
                select(Project.id).where(Project.user == current_user, Project.name == project_name.value)
            ).one()
            project_path = os.path.join(USER_PROJECTS_PATH, str(project_id))
            os.makedirs(project_path)
            session.commit()

    if not is_authenticated():
        ui.navigate.to("/login")
    else:
        project_name = ui.input('Project name')
        project_description = ui.input("Project description")
        ui.button('Add', on_click=add_project_handler)


### PROJECT DELETION
def handle_delete_project(project_to_delete) -> None:
    def delete_project():
        print("project deletion")
        with Session(engine) as session:
            session.delete(project_to_delete)
            session.commit()
        dialog.close()
        ui.run_javascript('location.reload();')
        
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Are you sure that you want to delete {project_to_delete.name}?")
        ui.button("Yes", on_click=lambda: delete_project())
        ui.button("No", on_click=dialog.close)
    dialog.open()


### PROJECT/project_id PAGE

# file deletion
async def handle_delete_file(file_entry: os.DirEntry) -> None:
    os.remove(file_entry.path)
    await page_reload()


# file download
def handle_download(e: events.UploadEventArguments) -> None:
    pass

# file opening (.las, .tiff)
def handle_open_file(file_entry: os.DirEntry) -> None:
    print("OPENING FILE")
    if file_entry.name[-3:].lower() in ["png", "jpg"]:
        ui.image(file_entry.path)
    else:
        ui.notify("This file extension is not supported yet!", type="info")
        print(file_entry.name[-3:].lower())
# file move (to other project)


## file action menu
def file_bar(file_entry: os.DirEntry) -> None:
    with ui.row():
        ui.label(file_entry.name)
        ui.button("Open file", on_click=lambda: handle_open_file(file_entry))
        ui.button("Download file", on_click=lambda e: ui.download.file(file_entry.path))
        ui.button("Delete file", on_click=lambda: handle_delete_file(file_entry))
        ui.button("Move file", on_click=lambda e: ui.notify("Not implemented yet!", type="info"))


@ui.page("/project/{project_id}")
@check_if_authenticated()
def project_edit(project_id: int) -> None:
    navbar()
    ### getting project data
    with Session(engine) as session:
        projects = session.exec(
            select(User).where(User.username == app.storage.user["username"])
        ).one().projects
    project = list(filter(lambda project: project.id == int(project_id), projects))[0]
    ui.label(f"Project name: {project.name}")
    ui.label(f"Project description: {project.description}")
    # ui.label(project_id)

    ### upload module
    project_path = os.path.join(USER_PROJECTS_PATH, str(project_id))
    ui.upload(multiple=True,on_upload=lambda e: handle_upload(e, destination = project_path)).classes('max-w-full' )

    ### list files in dir
    dir_generator = os.scandir(project_path)
    for entry in dir_generator:
        file_bar(entry)
        # ui.label(entry.name)


### projects PAGE
def project_bar(project: Project) -> None:
    with ui.row():
        ui.label(f"Project name: {project.name}")
        ui.label(f"Number of files: {len(list(
            os.scandir(os.path.join(USER_PROJECTS_PATH, str(project.id)))))}")
        ui.button("Go to project", on_click= lambda: ui.navigate.to(f"/project/{project.id}"))
        ui.button("Delete project", on_click=lambda e: handle_delete_project(e, project))


@ui.page("/projects")
@check_if_authenticated()
def projects() -> Optional[RedirectResponse]:
    navbar()
    # if app.storage.user.get("authenticated") != True:
    #     ui.navigate.to("/login")
    # else:
    projects = db.get_projects(app.storage.user["username"])
    ui.button("Add project", on_click = lambda: ui.navigate.to("/add-project"))
    for project in projects:
        project_bar(project)      

### APP MOUNT WITH FASTAPI
ui.run_with(
    fastapi_app,
    mount_path='/app/',  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
    storage_secret='pick your private secret here',  # NOTE setting a secret is optional but allows for persistent storage per user
)


### === FASTAPI MOUNT === ###
if __name__ == '__main__':
    uvicorn.run('main:fastapi_app', host='127.0.0.1', port=8000, log_level='info')
