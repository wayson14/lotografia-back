#!/usr/bin/env python3
import os
import uuid
from pathlib import Path
import uvicorn
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from nicegui import app, ui, events
from starlette.formparsers import MultiPartParser

MultiPartParser.spool_max_size = 1024 * 1024 * 1024 * 20  # 20 GiB

# Create base FastAPI app and ensure uploads directory exists
fastapi_app = FastAPI()
UPLOAD_DIR = Path.cwd() / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@fastapi_app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI! Browse to /gui to see the NiceGUI app.'}


async def handle_upload(e: events.UploadEventArguments):
    filename = f"{uuid.uuid4().hex}_{Path(e.file.name).name}"
    dest = UPLOAD_DIR / filename
    await e.file.save(dest)
    print(dest)
    

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