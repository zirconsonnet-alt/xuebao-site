import json
import sys
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_SLUG = "logic-bingo"
BASE_PATH = f"/{APP_SLUG}"

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from logic import BingoGenerator

APP_DIR = BASE_DIR / "apps" / APP_SLUG

templates = Jinja2Templates(directory=str(APP_DIR))

router = APIRouter(prefix=BASE_PATH)


def register(parent_app: FastAPI) -> None:
    parent_app.mount(f"{BASE_PATH}/assets", StaticFiles(directory=str(APP_DIR)), name="logic-bingo-assets")
    parent_app.include_router(router)


def build_game_data(size: int = 5) -> dict:
    generator = BingoGenerator(size)
    sentences = [[str(generator.sentences[i][j]) for j in range(size)] for i in range(size)]
    solution = generator.matrix.tolist()
    state = [[-1] * size for _ in range(size)]
    return {
        "size": size,
        "sentences": sentences,
        "solution": solution,
        "state": state,
    }


def parse_matrix(raw: str, size: int) -> Optional[List[List[int]]]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, list) or len(value) != size:
        return None
    matrix: List[List[int]] = []
    for row in value:
        if not isinstance(row, list) or len(row) != size:
            return None
        parsed_row: List[int] = []
        for cell in row:
            try:
                parsed_row.append(int(cell))
            except (TypeError, ValueError):
                return None
        matrix.append(parsed_row)
    return matrix


def has_line(matrix: List[List[int]]) -> bool:
    n = len(matrix)
    for i in range(n):
        if all(matrix[i][j] == 1 for j in range(n)):
            return True
        if all(matrix[j][i] == 1 for j in range(n)):
            return True
    if all(matrix[i][i] == 1 for i in range(n)):
        return True
    if all(matrix[i][n - 1 - i] == 1 for i in range(n)):
        return True
    return False


def status_payload(message: str, level: str) -> dict:
    return {"message": message, "status_class": f"status status--{level}"}


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = build_game_data()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "base_path": BASE_PATH,
            **data,
        },
    )


@router.post("/new", response_class=HTMLResponse)
async def new_game(request: Request):
    data = build_game_data()
    return templates.TemplateResponse(
        "_game.html",
        {
            "request": request,
            "base_path": BASE_PATH,
            **data,
        },
    )


@router.post("/answer", response_class=HTMLResponse)
async def answer(
    request: Request,
    size: int = Form(...),
    sentences_json: str = Form(...),
    solution_json: str = Form(...),
):
    sentences: List[List[str]] = json.loads(sentences_json)
    solution = parse_matrix(solution_json, size)
    if solution is None:
        return templates.TemplateResponse(
            "_board.html",
            {
                "request": request,
                "base_path": BASE_PATH,
                "size": size,
                "sentences": sentences,
                "solution": [[0] * size for _ in range(size)],
                "state": [[-1] * size for _ in range(size)],
            },
        )
    return templates.TemplateResponse(
        "_board.html",
        {
            "request": request,
            "base_path": BASE_PATH,
            "size": size,
            "sentences": sentences,
            "solution": solution,
            "state": solution,
        },
    )


@router.post("/submit", response_class=HTMLResponse)
async def submit(
    request: Request,
    size: int = Form(...),
    state_json: str = Form(...),
    solution_json: str = Form(...),
):
    state = parse_matrix(state_json, size)
    solution = parse_matrix(solution_json, size)
    if state is None or solution is None:
        payload = status_payload("数据格式不正确，请刷新后重试。", "error")
    elif any(cell == -1 for row in state for cell in row):
        payload = status_payload("请先填完矩阵。", "warn")
    elif state == solution and has_line(state):
        payload = status_payload("您成功连成一线！", "ok")
    elif state == solution:
        payload = status_payload("您未能连成一线！", "warn")
    else:
        payload = status_payload("您的逻辑有误！", "error")
    return templates.TemplateResponse(
        "_status.html",
        {
            "request": request,
            **payload,
        },
    )

