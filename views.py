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



