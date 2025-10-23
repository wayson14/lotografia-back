#!/usr/bin/env python3
import os
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from nicegui import app, ui, events

from starlette.formparsers import MultiPartParser

MultiPartParser.spool_max_size = 1024 * 1024 * 1024 * 10  # 10 GiB

# Create base FastAPI app and ensure uploads directory exists
fastapi_app = FastAPI()
UPLOAD_DIR = Path.cwd() / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum allowed upload size in bytes (example: 2 GiB). Adjust as needed.
MAX_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024


@fastapi_app.get('/')
def get_root():
    return {'message': 'Hello, FastAPI! Browse to /gui to see the NiceGUI app.'}



async def handle_upload(e: events.UploadEventArguments):
    filename = f"{uuid.uuid4().hex}_{Path(e.file.name).name}"
    dest = UPLOAD_DIR / filename
    await e.file.save(dest)
    print(dest)
    # await _save_stream(e.file.,dest)
    

@ui.page('/')
async def show():
    ui.label('Hello, NiceGUI!')

    # NOTE dark mode will be persistent for each user across tabs and server restarts
    ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
    ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')
    ui.upload(multiple=True,on_upload=handle_upload).classes('max-w-full' )



    

@ui.page('/test-client')
def test_client():
    ui.markdown('# Upload test client')
    file_input = ui.upload()
    # progress = ui.progress(value=0)
    status = ui.label('Ready')

    def upload_click():
        # JS will handle the multipart upload so we use a small script that posts the file
        status.set_text('Uploading...')
        # Build JS that reads the file from the first input element and POSTs it with fetch
        js = """
        (async () => {
            const input = document.querySelector('input[type=file]');
            if (!input || !input.files || input.files.length === 0) { return; }
            const file = input.files[0];
            const form = new FormData();
            form.append('file', file);
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);
            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    const pct = Math.round((e.loaded / e.total) * 100);
                    window._nicegui_update_progress(pct);
                }
            };
            xhr.onload = function() {
                window._nicegui_upload_done(xhr.status, xhr.responseText);
            };
            xhr.onerror = function() {
                window._nicegui_upload_done(0, 'network error');
            };
            xhr.send(form);
        })();
        """
        # Start the upload XHR (client-side). The global callbacks are defined below.
        ui.run_javascript(js)

    btn = ui.button('Upload', on_click=upload_click)

    # We'll use client-side JS to update the NiceGUI progress bar and status label directly.
    # Give the progress and status elements predictable DOM ids so JS can update them.
    # progress.element_id = 'ng_progress'
    status.element_id = 'ng_status'

    # JS snippet will locate those elements by id and update them during XHR upload.
    # Wire a small global function to be invoked by the XHR callbacks created above.
    ui.run_javascript("window._nicegui_update_progress = (pct) => { const p = document.getElementById('ng_progress'); if (p) p.value = pct; const s = document.getElementById('ng_status'); if (s) s.textContent = `Uploading: ${pct}%`; }")
    ui.run_javascript("window._nicegui_upload_done = (status, body) => { const s = document.getElementById('ng_status'); if (s) { if (status === 200) s.textContent = 'Upload complete'; else s.textContent = 'Upload failed: ' + status + ' ' + body; } }")



ui.run_with(
    fastapi_app,
    mount_path='/gui',  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
    storage_secret='pick your private secret here',  # NOTE setting a secret is optional but allows for persistent storage per user
)


if __name__ == '__main__':
    uvicorn.run('main:fastapi_app', host='127.0.0.1', port=8000, log_level='info')