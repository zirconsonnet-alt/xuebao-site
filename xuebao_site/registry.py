from dataclasses import dataclass
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / "apps"


@dataclass(frozen=True)
class GameSpec:
    slug: str
    title: str
    description: str
    entry_path: str
    status: str
    module_path: Path
    app_dir: Path


GAME_REGISTRY: List[GameSpec] = [
    GameSpec(
        slug="24game",
        title="24 点速算",
        description="用四张牌拼出 24，手脑并用，越快越爽。",
        entry_path="/24game/",
        status="live",
        module_path=APPS_DIR / "24game" / "main.py",
        app_dir=APPS_DIR / "24game" / "apps" / "24game",
    ),
    GameSpec(
        slug="logic-bingo",
        title="逻辑 Bingo",
        description="文字线索推理出正确的打勾矩阵。",
        entry_path="/logic-bingo/",
        status="live",
        module_path=APPS_DIR / "logic-bingo" / "main.py",
        app_dir=APPS_DIR / "logic-bingo" / "apps" / "logic-bingo",
    ),
]
