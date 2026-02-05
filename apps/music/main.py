from __future__ import annotations

import json
from pathlib import Path
import sys
import traceback

from fastapi import APIRouter, FastAPI, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

APP_SLUG = "music"
BASE_PATH = f"/{APP_SLUG}"

# 当前文件：xuebao-site/apps/music/main.py
BASE_DIR = Path(__file__).resolve().parent  # .../apps/music
PROJECT_ROOT = BASE_DIR.parents[1]          # .../xuebao-site
COMPOSER_DIR = BASE_DIR / "composer"        # .../apps/music/composer

# Signal dist：编译完成后在 apps/music/signal/app/dist（已修改过 base href）
SIGNAL_DIST_DIR = BASE_DIR / "signal" / "app" / "dist"

# -----------------------------
# sys.path 注入（关键）
# -----------------------------
# 让 `import composer` 可用（composer 在 apps/music/composer）
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 关键：让 composer 代码里的 `from base.enums import ...` 生效
# 因为 base 实际在 composer/base 下，需要把 composer 目录作为顶层路径
if str(COMPOSER_DIR) not in sys.path:
    sys.path.insert(0, str(COMPOSER_DIR))

router = APIRouter(prefix=BASE_PATH)


def register(parent_app: FastAPI) -> None:
    """
    在主 app 中注册 music 子应用：
    - 挂载 Signal 的静态资源到 /music/signal
    - 注册 /music 下的 API 与首页
    """
    # 如果 dist 不存在，先不要 mount（否则启动就直接崩）
    if SIGNAL_DIST_DIR.exists():
        parent_app.mount(
            f"{BASE_PATH}/signal",
            StaticFiles(directory=str(SIGNAL_DIST_DIR)),
            name="music-signal",
        )
    else:
        # dist 不存在时，你仍然可以访问 /music/ 看到 host 页面
        # 只是 iframe 里打开 /music/signal/edit.html 会 404
        pass

    parent_app.include_router(router)


# -----------------------------
# Pages
# -----------------------------
@router.get("/api/ping")
async def ping():
    """
    用于验证路由是否真实命中当前文件版本。
    """
    return PlainTextResponse("music ping ok", status_code=200)


@router.get("/")
async def index():
    """
    music 首页：作为 /music/piano 与 /music/theory 的入口聚合页。
    """
    index_path = BASE_DIR / "web" / "index.html"
    if not index_path.exists():
        return PlainTextResponse(
            f"Index file not found: {index_path}\n"
            f"Please create apps/music/web/index.html",
            status_code=500,
        )

    html = index_path.read_text(encoding="utf-8").replace("__BASE_PATH__", BASE_PATH)
    return HTMLResponse(content=html)


@router.get("/piano")
async def piano_roll():
    """
    钢琴卷帘（Signal host）。原先 /music/ 的内容迁移到 /music/piano。
    """
    host_path = BASE_DIR / "web" / "host.html"
    if not host_path.exists():
        return PlainTextResponse(
            f"Host file not found: {host_path}\n"
            f"Please create apps/music/web/host.html",
            status_code=500,
        )
    html = host_path.read_text(encoding="utf-8").replace("__BASE_PATH__", BASE_PATH)
    return HTMLResponse(content=html)


@router.get("/theory")
async def theory_index():
    """
    音乐理论分析子站（纯前端页面 + API）。
    """
    page_path = BASE_DIR / "web" / "theory.html"
    if not page_path.exists():
        return PlainTextResponse(
            f"Theory page not found: {page_path}\n"
            f"Please create apps/music/web/theory.html",
            status_code=500,
        )
    html = page_path.read_text(encoding="utf-8").replace("__BASE_PATH__", BASE_PATH)
    return HTMLResponse(content=html)


# -----------------------------
# API: theory analysis
# -----------------------------
class TheoryKeySpec(BaseModel):
    tonic: str = Field(..., description="C/D/E/F/G/A/B")
    main_mode_type: str = Field(..., description="Ionian/Aeolian/...")


class TheoryModeSpec(BaseModel):
    access: str = Field(..., description="Relative/Substitute/SubV")
    role: str = Field(..., description="Degree(I..VII) or Mode(Ionian..Locrian) depending on access")


class TheoryChordSpec(BaseModel):
    degree: str = Field(..., description="I..VII (degree inside current mode)")
    variant: str = Field("Base", description="Base/Ascending/Descending")
    composition: Optional[List[str]] = Field(None, description="e.g. ['I','III','V']")


class TheoryChordInModeRequest(BaseModel):
    key: TheoryKeySpec
    mode: TheoryModeSpec
    chord: TheoryChordSpec


class TheoryModeInKeyRequest(BaseModel):
    key: TheoryKeySpec
    mode: TheoryModeSpec


def _model_dump(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # pydantic v2
    if hasattr(model, "dict"):
        return model.dict()  # pydantic v1
    return {"_repr": str(model)}


def _rebuild_pydantic_model(model_cls: Any) -> None:
    """
    Support both pydantic v1 and v2 when `from __future__ import annotations`
    turns annotations into ForwardRef strings.
    """
    if hasattr(model_cls, "model_rebuild"):
        # pydantic v2
        model_cls.model_rebuild()
        return
    if hasattr(model_cls, "update_forward_refs"):
        # pydantic v1
        # Provide localns explicitly to avoid NameError on typing symbols like Optional/List.
        model_cls.update_forward_refs(**globals())


# Ensure forward refs are resolved on both pydantic v1/v2.
_rebuild_pydantic_model(TheoryKeySpec)
_rebuild_pydantic_model(TheoryModeSpec)
_rebuild_pydantic_model(TheoryChordSpec)
_rebuild_pydantic_model(TheoryChordInModeRequest)
_rebuild_pydantic_model(TheoryModeInKeyRequest)


def _to_jsonable(obj: Any) -> Any:
    try:
        from enum import Enum

        if isinstance(obj, Enum):
            return obj.name
    except Exception:
        pass
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            out[str(_to_jsonable(k))] = _to_jsonable(v)
        return out
    if hasattr(obj, "error_type") and hasattr(obj, "message"):
        return {"error_type": getattr(obj, "error_type"), "message": getattr(obj, "message")}
    return str(obj)


def _parse_degree_or_mode(value: str):
    from composer.domain.enums.core import Degrees
    from composer.domain.enums.harmony import Modes

    if value in Degrees.__members__:
        return Degrees[value]
    if value in Modes.__members__:
        return Modes[value]
    raise ValueError(f"未知 role: {value!r}（期望 Degrees 或 Modes 名称）")


@router.post("/api/theory/chord_in_mode")
async def theory_chord_in_mode(req: TheoryChordInModeRequest):
    try:
        from composer.domain.enums.core import NoteNames, Degrees
        from composer.domain.enums.harmony import Modes, ModeAccess, VariantForm
        from composer.domain.base_note import BaseNote
        from composer.domain.key import Key
        from composer.domain.relations import ModeId, ChordId
        from composer.analysis.resolve.resolver import Resolver
        from composer.analysis.api.analyze import analyze_hit

        key = Key(BaseNote(NoteNames[req.key.tonic]), Modes[req.key.main_mode_type])
        mode_id = ModeId(role=_parse_degree_or_mode(req.mode.role), access=ModeAccess[req.mode.access])
        mode = mode_id.resolve(key)

        comp = None
        if req.chord.composition:
            comp = frozenset(Degrees[d] for d in req.chord.composition)
        chord_id = ChordId(degree=Degrees[req.chord.degree], variant=VariantForm[req.chord.variant], composition=comp)
        chord = chord_id.resolve(mode)

        hits = Resolver().resolve(chord, mode)
        if not hits:
            payload = {"ok": False, "error": "no resolve hits", "input": _to_jsonable(_model_dump(req))}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
        analysis = analyze_hit(hits[0])
        if analysis is None:
            payload = {"ok": False, "error": "no analyzer for hit", "hit": str(hits[0])}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")

        view = analysis.view() if hasattr(analysis, "view") else None
        if view is None:
            payload = {"ok": True, "analysis": str(analysis)}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")

        grouped = {g.value: _to_jsonable(d) for g, d in view.as_grouped_dict().items()}
        payload = {"ok": True, "grouped": grouped}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
    except Exception:
        payload = {"ok": False, "error": traceback.format_exc()}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")


@router.post("/api/theory/chord")
async def theory_chord(req: TheoryChordInModeRequest):
    """
    Chord-only analysis（只分析和弦自身），但为了构造 Chord 实体，仍复用 key/mode/chord 的输入格式。
    """
    try:
        from composer.domain.enums.core import NoteNames, Degrees
        from composer.domain.enums.harmony import Modes, ModeAccess, VariantForm
        from composer.domain.base_note import BaseNote
        from composer.domain.key import Key
        from composer.domain.relations import ModeId, ChordId
        from composer.analysis.explain.analyzers.chord_analyzer import ChordAnalyzer

        key = Key(BaseNote(NoteNames[req.key.tonic]), Modes[req.key.main_mode_type])
        mode_id = ModeId(role=_parse_degree_or_mode(req.mode.role), access=ModeAccess[req.mode.access])
        mode = mode_id.resolve(key)

        comp = None
        if req.chord.composition:
            comp = frozenset(Degrees[d] for d in req.chord.composition)
        chord_id = ChordId(degree=Degrees[req.chord.degree], variant=VariantForm[req.chord.variant], composition=comp)
        chord = chord_id.resolve(mode)

        analysis = ChordAnalyzer().analyze(chord)
        view = analysis.view() if hasattr(analysis, "view") else None
        if view is None:
            payload = {"ok": True, "analysis": str(analysis)}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
        grouped = {g.value: _to_jsonable(d) for g, d in view.as_grouped_dict().items()}
        payload = {"ok": True, "grouped": grouped}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
    except Exception:
        payload = {"ok": False, "error": traceback.format_exc()}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")


@router.post("/api/theory/chord_in_key")
async def theory_chord_in_key(req: TheoryChordInModeRequest):
    """
    Chord ∈ Key analysis：分析和弦在调性中的功能/倾向/离调（含调性半音倾向性 evidence）。
    复用 key/mode/chord 的输入格式来构造 Chord 实体。
    """
    try:
        from composer.domain.enums.core import NoteNames, Degrees
        from composer.domain.enums.harmony import Modes, ModeAccess, VariantForm
        from composer.domain.base_note import BaseNote
        from composer.domain.key import Key
        from composer.domain.relations import ModeId, ChordId
        from composer.analysis.resolve.resolver import Resolver
        from composer.analysis.api.analyze import analyze_hit

        key = Key(BaseNote(NoteNames[req.key.tonic]), Modes[req.key.main_mode_type])
        mode_id = ModeId(role=_parse_degree_or_mode(req.mode.role), access=ModeAccess[req.mode.access])
        mode = mode_id.resolve(key)

        comp = None
        if req.chord.composition:
            comp = frozenset(Degrees[d] for d in req.chord.composition)
        chord_id = ChordId(degree=Degrees[req.chord.degree], variant=VariantForm[req.chord.variant], composition=comp)
        chord = chord_id.resolve(mode)

        hits = Resolver().resolve(chord, key)
        if not hits:
            payload = {"ok": False, "error": "no resolve hits", "input": _to_jsonable(_model_dump(req))}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
        analysis = analyze_hit(hits[0])
        if analysis is None:
            payload = {"ok": False, "error": "no analyzer for hit", "hit": str(hits[0])}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")

        view = analysis.view() if hasattr(analysis, "view") else None
        if view is None:
            payload = {"ok": True, "analysis": str(analysis)}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
        grouped = {g.value: _to_jsonable(d) for g, d in view.as_grouped_dict().items()}
        payload = {"ok": True, "grouped": grouped}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
    except Exception:
        payload = {"ok": False, "error": traceback.format_exc()}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")


@router.post("/api/theory/mode_in_key")
async def theory_mode_in_key(req: TheoryModeInKeyRequest):
    try:
        from composer.domain.enums.core import NoteNames
        from composer.domain.enums.harmony import Modes, ModeAccess
        from composer.domain.base_note import BaseNote
        from composer.domain.key import Key
        from composer.domain.relations import ModeId
        from composer.analysis.resolve.resolver import Resolver
        from composer.analysis.api.analyze import analyze_hit

        key = Key(BaseNote(NoteNames[req.key.tonic]), Modes[req.key.main_mode_type])
        mode_id = ModeId(role=_parse_degree_or_mode(req.mode.role), access=ModeAccess[req.mode.access])
        mode = mode_id.resolve(key)

        hits = Resolver().resolve(mode, key)
        if not hits:
            payload = {"ok": False, "error": "no resolve hits", "input": _to_jsonable(_model_dump(req))}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
        analysis = analyze_hit(hits[0])
        if analysis is None:
            payload = {"ok": False, "error": "no analyzer for hit", "hit": str(hits[0])}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")

        view = analysis.view() if hasattr(analysis, "view") else None
        if view is None:
            payload = {"ok": True, "analysis": str(analysis)}
            return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")

        grouped = {g.value: _to_jsonable(d) for g, d in view.as_grouped_dict().items()}
        payload = {"ok": True, "grouped": grouped}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")
    except Exception:
        payload = {"ok": False, "error": traceback.format_exc()}
        return Response(content=json.dumps(payload, ensure_ascii=False), media_type="application/json")


# -----------------------------
# API: composer midi
# -----------------------------
@router.get("/api/composer/midi")
async def composer_midi():
    """
    生成 MIDI 并返回 bytes。
    任何异常都会直接返回 traceback 便于你在浏览器里看到真实错误原因。
    """
    try:
        # 延迟导入：避免服务器启动时就爆
        from composer.generator import (
            ProgressionGenerator,
            ArrangementGenerator,
            TextureGenerator,
            MidiGenerator,
            RootGenerator,
        )

        # 1) 生成 root
        rg = RootGenerator(8)
        root_list = rg.generate()
        if not root_list:
            return PlainTextResponse("Failed to generate roots", status_code=500)

        # 2) 生成和弦进行（progression）
        pg = ProgressionGenerator(root_list=root_list)
        progression = pg.generate()
        if not progression:
            return PlainTextResponse("Failed to generate progression", status_code=500)

        # progression 元素是 (Modes|Degrees, Degrees, VariantForm)
        chord_list = [pg.key[ch[0]][ch[1], ch[2]] for ch in progression]

        # 3) 生成编排（四声部）
        ag = ArrangementGenerator(chord_list)
        arrangement_list = ag.generate()
        if not arrangement_list:
            return PlainTextResponse("Failed to generate arrangement", status_code=500)

        # 4) 织体
        tg = TextureGenerator()
        texture_list = tg.generate(arrangement_list)

        # 5) MIDI bytes
        mg = MidiGenerator()
        midi_bytes = mg.generate_midi_bytes(texture_list)

        return Response(
            content=midi_bytes,
            media_type="audio/midi",
            headers={"Content-Disposition": "inline; filename=composer.mid"},
        )

    except Exception:
        return PlainTextResponse(traceback.format_exc(), status_code=500)
