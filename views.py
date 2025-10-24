from nicegui import app, ui, events
import uuid
from pathlib import Path
from typing import Annotated, Optional
from models import User
from auth import get_current_active_user
from fastapi import Depends
from fastapi.responses import JSONResponse, RedirectResponse
import requests

from auth import get_current_active_user
UPLOAD_DIR = Path.cwd() / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
API_PATH = "http://127.0.0.1:8000/"
### Logic functions
async def handle_upload(e: events.UploadEventArguments):
    filename = f"{uuid.uuid4().hex}_{Path(e.file.name).name}"
    dest = UPLOAD_DIR / filename
    await e.file.save(dest)
    print(dest)

## UI
@ui.page('/')
async def show():
    ui.label("username").bind_text_from(app.storage.user, "username")
    ui.label('Hello, NiceGUI!')
    # NOTE dark mode will be persistent for each user across tabs and server restarts
    ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
    ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
    ui.upload(multiple=True,on_upload=handle_upload).classes('max-w-full' )


