import importlib.util
import logging
from pathlib import Path
from typing import Iterable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from .registry import GAME_REGISTRY, GameSpec

BASE_DIR = Path(__file__).resolve().parent.parent
HOME_DIR = BASE_DIR / "apps" / "home"

logger = logging.getLogger("xuebao")

templates = Jinja2Templates(directory=str(HOME_DIR))

app = FastAPI()

app.mount("/assets/home", StaticFiles(directory=str(HOME_DIR)), name="home-assets")
app.mount("/assets/music", StaticFiles(directory=str(BASE_DIR / "music")), name="music")


def load_game_module(spec: GameSpec):
    module_name = f"xuebao_{spec.slug.replace('-', '_')}"
    spec_obj = importlib.util.spec_from_file_location(module_name, spec.module_path)
    if spec_obj is None or spec_obj.loader is None:
        raise RuntimeError(f"Unable to load module for {spec.slug}")
    module = importlib.util.module_from_spec(spec_obj)
    spec_obj.loader.exec_module(module)
    return module


def register_games(parent_app: FastAPI, specs: Iterable[GameSpec]) -> None:
    for spec in specs:
        module = load_game_module(spec)
        register = getattr(module, "register", None)
        if register is None:
            raise RuntimeError(f"Game module missing register(): {spec.module_path}")
        register(parent_app)


register_games(app, GAME_REGISTRY)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    primary_game = next((game for game in GAME_REGISTRY if game.status == "live"), None)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "asset_base": "/assets/home",
            "games": GAME_REGISTRY,
            "primary_game": primary_game,
        },
    )


@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return HTMLResponse("<h1>404 Not Found</h1>", status_code=404)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return HTMLResponse("<h1>500 Internal Server Error</h1>", status_code=500)
