import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import validate_config


try:
    validate_config()
except ValueError as e:
    print(f"\nConfiguration Error: {e}\n")
    # We do not crash the app here, so DEMO_MODE toggle or error message works via UI

app = FastAPI(title="ComicCraft", description="AI Comic Story Creator", version="1.0.0")

# Mount static files with absolute path
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
static_dir = str(BASE_DIR / "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Import routes here to avoid circular imports
from app.routes import router
app.include_router(router)
