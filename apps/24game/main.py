import ast
import json
import operator
import random
import re
from itertools import permutations
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from fastapi import APIRouter, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_SLUG = "24game"
BASE_PATH = f"/{APP_SLUG}"

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "apps" / APP_SLUG

templates = Jinja2Templates(directory=str(APP_DIR))

router = APIRouter(prefix=BASE_PATH)


def register(parent_app: FastAPI) -> None:
    parent_app.mount(f"{BASE_PATH}/assets", StaticFiles(directory=str(APP_DIR)), name="24game-assets")
    parent_app.include_router(router)

TARGET = 24
CARD_MIN = 1
CARD_MAX = 10
CARD_COUNT = 4
TOLERANCE = 1e-6


def status_payload(message: str, level: str = "idle") -> dict:
    status_class = "result"
    if level and level != "idle":
        status_class = f"{status_class} {level}"
    return {"message": message, "status_class": status_class}


def parse_numbers(raw: str) -> Optional[List[int]]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, list) or len(value) != CARD_COUNT:
        return None
    numbers: List[int] = []
    for item in value:
        try:
            numbers.append(int(item))
        except (TypeError, ValueError):
            return None
    return numbers


def extract_numbers(expression: str) -> List[int]:
    tokens = [int(token) for token in re.findall(r"\d+", expression)]
    return tokens


def numbers_match(numbers: List[int], used: List[int]) -> bool:
    if len(numbers) != len(used):
        return False
    pool = {}
    for num in numbers:
        pool[num] = pool.get(num, 0) + 1
    for value in used:
        count = pool.get(value, 0)
        if count <= 0:
            return False
        pool[value] = count - 1
    return True


def safe_eval(expression: str) -> float:
    parsed = ast.parse(expression, mode="eval")

    def eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("Invalid literal")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = eval_node(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Div) and abs(right) < TOLERANCE:
                raise ZeroDivisionError
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        raise ValueError("Unsupported expression")

    return eval_node(parsed)


def close_to_target(value: float) -> bool:
    return abs(value - TARGET) < TOLERANCE


def apply_op(op: Callable[[float, float], float], left: float, right: float) -> float:
    if op is operator.truediv and abs(right) < TOLERANCE:
        raise ZeroDivisionError
    return op(left, right)


def find_solution(numbers: List[int]) -> Optional[str]:
    operations: List[Tuple[str, Callable[[float, float], float]]] = [
        ("+", operator.add),
        ("-", operator.sub),
        ("*", operator.mul),
        ("/", operator.truediv),
    ]
    for perm in permutations(numbers):
        a, b, c, d = perm
        for sym1, op1 in operations:
            for sym2, op2 in operations:
                for sym3, op3 in operations:
                    try:
                        r1 = apply_op(op1, a, b)
                        r2 = apply_op(op2, r1, c)
                        r3 = apply_op(op3, r2, d)
                        if close_to_target(r3):
                            return f"(({a}{sym1}{b}){sym2}{c}){sym3}{d}"
                    except ZeroDivisionError:
                        pass
                    try:
                        r1 = apply_op(op1, a, b)
                        r2 = apply_op(op3, c, d)
                        r3 = apply_op(op2, r1, r2)
                        if close_to_target(r3):
                            return f"({a}{sym1}{b}){sym2}({c}{sym3}{d})"
                    except ZeroDivisionError:
                        pass
                    try:
                        r1 = apply_op(op2, b, c)
                        r2 = apply_op(op1, a, r1)
                        r3 = apply_op(op3, r2, d)
                        if close_to_target(r3):
                            return f"({a}{sym1}({b}{sym2}{c})){sym3}{d}"
                    except ZeroDivisionError:
                        pass
                    try:
                        r1 = apply_op(op2, b, c)
                        r2 = apply_op(op3, r1, d)
                        r3 = apply_op(op1, a, r2)
                        if close_to_target(r3):
                            return f"{a}{sym1}(({b}{sym2}{c}){sym3}{d})"
                    except ZeroDivisionError:
                        pass
                    try:
                        r1 = apply_op(op3, c, d)
                        r2 = apply_op(op2, b, r1)
                        r3 = apply_op(op1, a, r2)
                        if close_to_target(r3):
                            return f"{a}{sym1}({b}{sym2}({c}{sym3}{d}))"
                    except ZeroDivisionError:
                        pass
    return None


def build_game_data() -> dict:
    while True:
        numbers = [random.randint(CARD_MIN, CARD_MAX) for _ in range(CARD_COUNT)]
        solution = find_solution(numbers)
        if solution:
            return {"numbers": numbers, "solution": solution}


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = build_game_data()
    payload = status_payload("准备就绪。")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "base_path": BASE_PATH,
            **data,
            **payload,
        },
    )


@router.post("/new", response_class=HTMLResponse)
async def new_game(request: Request):
    data = build_game_data()
    payload = status_payload("已发新一组。")
    return templates.TemplateResponse(
        "_game.html",
        {
            "request": request,
            "base_path": BASE_PATH,
            **data,
            **payload,
        },
    )


@router.post("/shuffle", response_class=HTMLResponse)
async def shuffle(
    request: Request,
    numbers_json: str = Form(...),
    solution_text: str = Form(...),
    expression: str = Form(""),
):
    numbers = parse_numbers(numbers_json)
    if numbers is None:
        data = build_game_data()
    else:
        random.shuffle(numbers)
        data = {"numbers": numbers, "solution": solution_text}
    payload = status_payload("已洗牌。")
    return templates.TemplateResponse(
        "_game.html",
        {
            "request": request,
            "base_path": BASE_PATH,
            "expression": expression,
            **data,
            **payload,
        },
    )


@router.post("/answer", response_class=HTMLResponse)
async def answer(
    request: Request,
    solution_text: str = Form(""),
):
    message = solution_text.strip() or "本题暂未记录答案。"
    payload = status_payload(f"参考答案：{message}", "warn")
    return templates.TemplateResponse(
        "_status.html",
        {
            "request": request,
            **payload,
        },
    )


@router.post("/check", response_class=HTMLResponse)
async def check(
    request: Request,
    expression: str = Form(""),
    numbers_json: str = Form(...),
):
    numbers = parse_numbers(numbers_json)
    if numbers is None:
        payload = status_payload("缺少数字牌信息，请刷新后重试。", "fail")
        return templates.TemplateResponse("_status.html", {"request": request, **payload})

    trimmed = expression.strip()
    if not trimmed:
        payload = status_payload("请先输入表达式。", "warn")
        return templates.TemplateResponse("_status.html", {"request": request, **payload})

    if not re.match(r"^[\d+\-*/().\s]+$", trimmed):
        payload = status_payload("只允许数字和运算符。", "fail")
        return templates.TemplateResponse("_status.html", {"request": request, **payload})

    used_numbers = extract_numbers(trimmed)
    if not numbers_match(numbers, used_numbers):
        payload = status_payload("每个数字必须且只能使用一次。", "fail")
        return templates.TemplateResponse("_status.html", {"request": request, **payload})

    try:
        value = safe_eval(trimmed)
    except ZeroDivisionError:
        payload = status_payload("不允许除以零。", "fail")
        return templates.TemplateResponse("_status.html", {"request": request, **payload})
    except Exception:
        payload = status_payload("表达式无效。", "fail")
        return templates.TemplateResponse("_status.html", {"request": request, **payload})

    if close_to_target(value):
        payload = status_payload(f"漂亮！{trimmed} = 24", "win")
    else:
        payload = status_payload(f"结果为 {value:.4f}，不是 24。", "fail")
    return templates.TemplateResponse("_status.html", {"request": request, **payload})
