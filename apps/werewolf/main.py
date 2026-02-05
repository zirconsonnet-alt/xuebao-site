import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from fastapi import APIRouter, FastAPI, File, Form, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
APPS_DIR = BASE_DIR.parent
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from werewolf import auth
from werewolf.enum import Phase
from werewolf.web_engine import GameRoom

APP_SLUG = "werewolf"
ROOT_PATH = f"/{APP_SLUG}"
ROOM_PREFIX = f"{ROOT_PATH}/room"
MAX_AVATAR_BYTES = 2 * 1024 * 1024

WEB_DIR = BASE_DIR / "web"

templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
templates.env.auto_reload = True

router = APIRouter(prefix=ROOT_PATH)


class RoomManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, GameRoom] = {}

    def create_room_id(self) -> str:
        while True:
            room_id = uuid.uuid4().hex[:8]
            if room_id not in self.rooms:
                return room_id

    def get_room(self, room_id: str) -> GameRoom:
        if room_id not in self.rooms:
            self.rooms[room_id] = GameRoom()
        return self.rooms[room_id]


ROOMS = RoomManager()
CONNECTIONS: Dict[str, Dict[str, WebSocket]] = {}
CONNECTION_USERS: Dict[str, Dict[str, Optional[str]]] = {}
SESSION_TTL_SECONDS = 60 * 60 * 12
SESSIONS: Dict[str, tuple[str, int]] = {}
BOT_ID = os.getenv("WEREWOLF_BOT_ID", "")
BOT_SECRET = os.getenv("WEREWOLF_BOT_SECRET", "")
NONCE_TTL_SECONDS = 120
NONCE_CACHE: Dict[str, int] = {}


def _now_ts() -> int:
    return int(time.time())


def _session_user_id(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    record = SESSIONS.get(token)
    if not record:
        return None
    user_id, expires_at = record
    if expires_at <= _now_ts():
        SESSIONS.pop(token, None)
        return None
    return user_id


def _is_origin_allowed(origin: Optional[str], host: Optional[str]) -> bool:
    if not origin:
        return True
    if not host:
        return False
    try:
        origin_host = urlparse(origin).netloc
    except ValueError:
        return False
    if not origin_host:
        return False
    return origin_host.lower() == host.lower()


def _purge_nonces(now_ts: int) -> None:
    expired = [nonce for nonce, expires_at in NONCE_CACHE.items() if expires_at <= now_ts]
    for nonce in expired:
        NONCE_CACHE.pop(nonce, None)


def _verify_bot_request(request: Request, body_text: str) -> Tuple[bool, str]:
    if not BOT_ID or not BOT_SECRET:
        return False, "bot_auth_unconfigured"
    bot_id = request.headers.get("X-Bot-Id", "")
    timestamp = request.headers.get("X-Timestamp", "")
    nonce = request.headers.get("X-Nonce", "")
    signature = request.headers.get("X-Signature", "")
    if not bot_id or not timestamp or not nonce or not signature:
        return False, "bot_auth_missing"
    if bot_id != BOT_ID:
        return False, "bot_auth_invalid"
    try:
        ts_value = int(timestamp)
    except ValueError:
        return False, "bot_auth_invalid"
    now_ts = _now_ts()
    if abs(now_ts - ts_value) > 60:
        return False, "bot_auth_expired"
    _purge_nonces(now_ts)
    if nonce in NONCE_CACHE:
        return False, "bot_auth_replay"
    message = f"{request.method}\n{request.url.path}\n{body_text}\n{timestamp}\n{nonce}"
    expected = hmac.new(BOT_SECRET.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False, "bot_auth_invalid"
    NONCE_CACHE[nonce] = now_ts + NONCE_TTL_SECONDS
    return True, ""


def register(parent_app: FastAPI) -> None:
    auth.init_db()
    auth.AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    parent_app.mount(
        f"{ROOT_PATH}/assets",
        StaticFiles(directory=str(WEB_DIR / "static")),
        name="werewolf-assets",
    )
    parent_app.mount(
        f"{ROOT_PATH}/avatars",
        StaticFiles(directory=str(auth.AVATAR_DIR)),
        name="werewolf-avatars",
    )
    parent_app.include_router(router)


def get_current_user_from_cookie(cookie_value: Optional[str]) -> Optional[dict]:
    if not cookie_value:
        return None
    user_id = _session_user_id(cookie_value)
    if not user_id:
        return None
    return auth.get_user_by_id(user_id)


def get_current_user(request: Request) -> Optional[dict]:
    return get_current_user_from_cookie(request.cookies.get("werewolf_session"))


def user_context(user: Optional[dict]) -> dict:
    return {
        "user": user,
        "user_name": user["username"] if user else "",
        "user_qq": user["qq_uin"] if user else "",
        "avatar_url": auth.avatar_url(ROOT_PATH, user.get("avatar_filename")) if user else None,
    }


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    room_id = ROOMS.create_room_id()
    return RedirectResponse(url=f"{ROOM_PREFIX}/{room_id}", status_code=303)


@router.get("/room/{room_id}", response_class=HTMLResponse)
async def room_view(request: Request, room_id: str):
    user = get_current_user(request)
    room_path = f"{ROOM_PREFIX}/{room_id}"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "room_id": room_id,
            "room_path": room_path,
            "asset_path": ROOT_PATH,
            "auth_path": ROOT_PATH,
            "next_path": room_path,
            **user_context(user),
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_view(request: Request):
    next_path = request.query_params.get("next") or ROOT_PATH
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "auth_path": ROOT_PATH,
            "asset_path": ROOT_PATH,
            "next_path": next_path,
        },
    )


@router.post("/login")
async def login(
    request: Request, qq_uin: str = Form(...), secret: str = Form(...), next: str = Form(ROOT_PATH)
):
    try:
        user = auth.authenticate_by_qq(qq_uin, secret)
    except ValueError as exc:
        error_map = {
            "empty_qq": "请输入 QQ 号。",
            "qq_chars": "QQ 号只允许数字。",
            "qq_length": "QQ 号长度不正确。",
            "empty_secret": "请输入密钥。",
        }
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "auth_path": ROOT_PATH,
                "asset_path": ROOT_PATH,
                "next_path": next,
                "error": error_map.get(str(exc), "账号或密钥错误。"),
            },
            status_code=400,
        )
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "auth_path": ROOT_PATH,
                "asset_path": ROOT_PATH,
                "next_path": next,
                "error": "账号或密钥错误，或尚未确认。",
            },
            status_code=400,
        )
    session_token = secrets.token_urlsafe(32)
    SESSIONS[session_token] = (user["id"], _now_ts() + SESSION_TTL_SECONDS)
    response = RedirectResponse(url=next or ROOT_PATH, status_code=303)
    response.set_cookie(
        "werewolf_session",
        session_token,
        httponly=True,
        samesite="lax",
        path=ROOT_PATH,
        max_age=SESSION_TTL_SECONDS,
        secure=request.url.scheme == "https",
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_view(request: Request):
    next_path = request.query_params.get("next") or ROOT_PATH
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "auth_path": ROOT_PATH,
            "asset_path": ROOT_PATH,
            "next_path": next_path,
        },
    )


@router.post("/register")
async def register_user(
    request: Request, next: str = Form(ROOT_PATH)
):
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "auth_path": ROOT_PATH,
            "asset_path": ROOT_PATH,
            "next_path": next,
            "error": "请先通过 QQ 机器人获取密钥。",
        },
        status_code=400,
    )


@router.post("/logout")
async def logout(request: Request):
    next_path = request.query_params.get("next") or ROOT_PATH
    token = request.cookies.get("werewolf_session")
    if token:
        SESSIONS.pop(token, None)
    response = RedirectResponse(url=next_path, status_code=303)
    response.delete_cookie("werewolf_session", path=ROOT_PATH)
    return response


@router.get("/account", response_class=HTMLResponse)
async def account_view(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{ROOT_PATH}/login", status_code=303)
    next_path = request.query_params.get("next") or ROOT_PATH
    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "auth_path": ROOT_PATH,
            "asset_path": ROOT_PATH,
            "next_path": next_path,
            **user_context(user),
        },
    )


@router.post("/account/avatar")
async def upload_avatar(request: Request, avatar: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{ROOT_PATH}/login", status_code=303)
    filename = (avatar.filename or "").lower()
    ext = Path(filename).suffix
    if ext not in {".png", ".jpg", ".jpeg", ".gif"}:
        return HTMLResponse(content="只支持 png/jpg/gif 格式。", status_code=400)
    content = bytearray()
    while True:
        chunk = await avatar.read(64 * 1024)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_AVATAR_BYTES:
            return HTMLResponse(content="头像大小不能超过 2MB。", status_code=400)
    stored_name = f"{user['id']}{ext}"
    (auth.AVATAR_DIR / stored_name).write_bytes(content)
    auth.update_avatar(user["id"], stored_name)
    next_path = request.query_params.get("next") or ROOT_PATH
    return RedirectResponse(url=f"{ROOT_PATH}/account?next={next_path}", status_code=303)


@router.post("/account/name")
async def update_display_name(request: Request, display_name: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{ROOT_PATH}/login", status_code=303)
    try:
        auth.update_display_name(user["id"], display_name)
    except ValueError as exc:
        error_map = {
            "empty_username": "请输入展示名。",
            "username_length": "展示名长度需要在 2-12 个字符之间。",
            "username_chars": "展示名仅支持中文、英文、数字、_ 或 -。",
        }
        next_path = request.query_params.get("next") or ROOT_PATH
        return templates.TemplateResponse(
            "account.html",
            {
                "request": request,
                "auth_path": ROOT_PATH,
                "asset_path": ROOT_PATH,
                "next_path": next_path,
                "error": error_map.get(str(exc), "更新失败。"),
                **user_context(user),
            },
            status_code=400,
        )
    next_path = request.query_params.get("next") or ROOT_PATH
    return RedirectResponse(url=f"{ROOT_PATH}/account?next={next_path}", status_code=303)


@router.post("/internal/provision")
async def internal_provision(request: Request):
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8") if body_bytes else ""
    ok, error = _verify_bot_request(request, body_text)
    if not ok:
        return JSONResponse({"error": error}, status_code=401)
    try:
        payload = json.loads(body_text or "{}")
    except json.JSONDecodeError:
        return JSONResponse({"error": "bad_request"}, status_code=400)
    try:
        result = auth.provision_user(payload.get("qq_uin", ""), payload.get("display_name"))
    except ValueError as exc:
        error_map = {
            "empty_qq": "qq_required",
            "qq_chars": "qq_invalid",
            "qq_length": "qq_invalid",
            "user_disabled": "user_disabled",
        }
        return JSONResponse({"error": error_map.get(str(exc), "provision_failed")}, status_code=400)
    return JSONResponse(
        {
            "user_id": result["id"],
            "qq_uin": result["qq_uin"],
            "display_name": result["username"],
            "status": result["status"],
            "secret": result["secret"],
        }
    )


@router.post("/internal/confirm")
async def internal_confirm(request: Request):
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8") if body_bytes else ""
    ok, error = _verify_bot_request(request, body_text)
    if not ok:
        return JSONResponse({"error": error}, status_code=401)
    try:
        payload = json.loads(body_text or "{}")
    except json.JSONDecodeError:
        return JSONResponse({"error": "bad_request"}, status_code=400)
    try:
        result = auth.confirm_user(payload.get("qq_uin", ""))
    except ValueError as exc:
        error_map = {
            "empty_qq": "qq_required",
            "qq_chars": "qq_invalid",
            "qq_length": "qq_invalid",
            "user_not_found": "user_not_found",
            "user_disabled": "user_disabled",
        }
        return JSONResponse({"error": error_map.get(str(exc), "confirm_failed")}, status_code=400)
    return JSONResponse({"user_id": result["id"], "qq_uin": result["qq_uin"], "status": result["status"]})


@router.get("/internal/user_status")
async def internal_user_status(request: Request, qq_uin: str):
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8") if body_bytes else ""
    ok, error = _verify_bot_request(request, body_text)
    if not ok:
        return JSONResponse({"error": error}, status_code=401)
    error = auth.validate_qq_uin(qq_uin)
    if error:
        return JSONResponse({"error": "qq_invalid"}, status_code=400)
    user = auth.get_user_by_qq(qq_uin)
    if not user:
        return JSONResponse({"status": None})
    return JSONResponse(
        {
            "status": user.get("status"),
            "display_name": user.get("username"),
            "avatar_filename": user.get("avatar_filename"),
        }
    )


@router.get("/room/{room_id}/player/{player_id}", response_class=HTMLResponse)
async def player_view(request: Request, room_id: str, player_id: str):
    user = get_current_user(request)
    room_path = f"{ROOM_PREFIX}/{room_id}"
    return templates.TemplateResponse(
        "player.html",
        {
            "request": request,
            "room_id": room_id,
            "room_path": room_path,
            "asset_path": ROOT_PATH,
            "auth_path": ROOT_PATH,
            "next_path": room_path,
            "player_id": player_id,
            **user_context(user),
        },
    )


@router.websocket("/room/{room_id}/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    origin = websocket.headers.get("origin")
    host = websocket.headers.get("host")
    if not _is_origin_allowed(origin, host):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    connection_id = str(id(websocket))
    user = get_current_user_from_cookie(websocket.cookies.get("werewolf_session"))
    user_id = user["id"] if user else None
    room = ROOMS.get_room(room_id)
    CONNECTIONS.setdefault(room_id, {})[connection_id] = websocket
    CONNECTION_USERS.setdefault(room_id, {})[connection_id] = user_id
    await websocket.send_text(room.to_json(user_id))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "bad_request"}))
                continue
            msg_type = message.get("type")
            if msg_type == "join":
                if not user_id:
                    await websocket.send_text(json.dumps({"type": "error", "message": "auth_required"}))
                else:
                    if room.player_for_owner(user_id):
                        await websocket.send_text(json.dumps({"type": "error", "message": "already_joined"}))
                    else:
                        display_name = message.get("display_name") or user["username"]
                        avatar = auth.avatar_url(ROOT_PATH, user.get("avatar_filename"))
                        try:
                            player = room.add_player(display_name, avatar_url=avatar, owner_id=user_id)
                        except ValueError as exc:
                            error_map = {
                                "name_taken": "昵称已被占用。",
                                "name_invalid": "昵称不合法，请输入 1-12 个字符。",
                                "room_full": "房间已满。",
                            }
                            await websocket.send_text(
                                json.dumps({"type": "error", "message": error_map.get(str(exc), "加入失败。")})
                            )
                        else:
                            await websocket.send_text(json.dumps({"type": "joined", "player_id": player.id}))
            elif msg_type == "leave":
                player = room.player_for_owner(user_id) if user_id else None
                if player:
                    room.remove_player(player.id)
            elif msg_type == "start":
                if room.is_host(user_id):
                    mode = message.get("mode")
                    if mode:
                        room.set_mode(mode)
                    room.start_game()
                else:
                    await websocket.send_text(json.dumps({"type": "error", "message": "host_only"}))
            elif msg_type == "reset":
                if room.is_host(user_id):
                    room.reset()
                else:
                    await websocket.send_text(json.dumps({"type": "error", "message": "host_only"}))
            elif msg_type == "advance":
                if room.is_host(user_id):
                    room.advance()
                else:
                    await websocket.send_text(json.dumps({"type": "error", "message": "host_only"}))
            elif msg_type == "back_to_lobby":
                if not user_id:
                    await websocket.send_text(json.dumps({"type": "error", "message": "auth_required"}))
                elif room.phase != Phase.END:
                    await websocket.send_text(json.dumps({"type": "error", "message": "游戏未结束"}))
                else:
                    room.reset()
            elif msg_type == "action":
                ok, result = room.record_action(
                    user_id,
                    message.get("player_id", ""),
                    message.get("action", ""),
                    message.get("target_id"),
                    message.get("target_id_2"),
                    message.get("text"),
                )
                if ok:
                    room.add_log(result)
                await websocket.send_text(json.dumps({"type": "action_result", "ok": ok, "message": result}))

            await broadcast_state(room_id)
    except WebSocketDisconnect:
        CONNECTIONS.get(room_id, {}).pop(connection_id, None)
        CONNECTION_USERS.get(room_id, {}).pop(connection_id, None)
        if not CONNECTIONS.get(room_id):
            CONNECTIONS.pop(room_id, None)
            CONNECTION_USERS.pop(room_id, None)


async def broadcast_state(room_id: str) -> None:
    connections = CONNECTIONS.get(room_id, {})
    connection_users = CONNECTION_USERS.get(room_id, {})
    room = ROOMS.get_room(room_id)
    closed = []
    for conn_id, conn in connections.items():
        try:
            viewer_id = connection_users.get(conn_id)
            await conn.send_text(room.to_json(viewer_id))
        except RuntimeError:
            closed.append(conn_id)
    for conn_id in closed:
        connections.pop(conn_id, None)
        connection_users.pop(conn_id, None)
    if not connections:
        CONNECTIONS.pop(room_id, None)
        CONNECTION_USERS.pop(room_id, None)
