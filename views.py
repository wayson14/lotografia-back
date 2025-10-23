from nicegui import app, ui, events
import uuid
from pathlib import Path
from typing import Annotated
from models import User
from auth import get_current_active_user
from fastapi import Depends
UPLOAD_DIR = Path.cwd() / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

### Logic functions
async def handle_upload(e: events.UploadEventArguments):
    filename = f"{uuid.uuid4().hex}_{Path(e.file.name).name}"
    dest = UPLOAD_DIR / filename
    await e.file.save(dest)
    print(dest)

## UI
@ui.page('/')
async def show():

    def try_login():
        ui.notify("Tried login")
    ui.label('Hello, NiceGUI!')
    username = ui.input('Username').on('keydown.enter', try_login)
    password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
    ui.button('Log in', on_click=try_login)
    
    # NOTE dark mode will be persistent for each user across tabs and server restarts
    ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
    ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
    ui.upload(multiple=True,on_upload=handle_upload).classes('max-w-full' )




