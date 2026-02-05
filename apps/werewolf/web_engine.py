import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .enum import Kind, Mode, Phase, Role, role_emojis
from .game_mode import GameMode


class ActionType:
    PASS = "pass"
    RAISE_HAND = "raise_hand"
    POLICE_SKIP = "police_skip"
    ELECTION_VOTE = "election_vote"
    ELECTION_SKIP = "election_skip"
    WOLF_KILL = "wolf_kill"
    SEER_CHECK = "seer_check"
    GUARD_PROTECT = "guard_protect"
    WITCH_SAVE = "witch_save"
    WITCH_POISON = "witch_poison"
    CUPID_LINK = "cupid_link"
    EXPLORER_BUY = "explorer_buy"
    HUNTER_SHOOT = "hunter_shoot"
    WHITE_WOLF_BOOM = "white_wolf_boom"
    NERD_REVEAL = "nerd_reveal"
    RIDER_DUEL = "rider_duel"
    DAY_VOTE = "day_vote"
    DAY_SKIP = "day_skip"
    MORNING_SPEAK = "morning_speak"
    MORNING_SKIP = "morning_skip"


@dataclass
class PlayerState:
    id: str
    name: str
    role: Optional[Role] = None
    kind: Optional[Kind] = None
    alive: bool = True
    avatar_url: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    lover_ids: List[str] = field(default_factory=list)
    is_police: bool = False
    is_chief: bool = False
    witch_saved: bool = False
    witch_poisoned: bool = False
    explorer_bought: bool = False
    hunter_shot: bool = False
    white_wolf_exploded: bool = False
    nerd_revealed: bool = False
    rider_duel_used: bool = False
    cupid_linked: bool = False

    def display_role(self) -> str:
        if not self.role:
            return "未分配"
        emoji = role_emojis.get(self.role, "")
        return f"{emoji} {self.role.value}"


@dataclass
class PendingAction:
    action: str
    target_id: Optional[str] = None
    target_id_2: Optional[str] = None


@dataclass
class GameEvent:
    seq: int
    type: str
    priority: int
    day: int
    phase: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    payload: Dict[str, object] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "seq": self.seq,
            "type": self.type,
            "priority": self.priority,
            "day": self.day,
            "phase": self.phase,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "payload": self.payload,
            "ts": self.ts,
        }


class GameRoom:
    def __init__(self) -> None:
        self.phase = Phase.LOBBY
        self.day_count = 1
        self.mode = Mode.CLASSIC
        self.players: Dict[str, PlayerState] = {}
        self.owners: Dict[str, str] = {}
        self.host_user_id: Optional[str] = None
        self.events: List[GameEvent] = []
        self.event_seq = 0
        self.actions: Dict[str, PendingAction] = {}
        self.last_guard_target: Optional[str] = None
        self.wolf_target: Optional[str] = None
        self.witch_save_target: Optional[str] = None
        self.witch_poison_target: Optional[str] = None
        self.last_night_deaths: List[str] = []
        self.special_state = False
        self.morning_order = []
        self.morning_index = 0
        self.morning_started_at = None
        self.morning_speaker_id = None

    def log_event(
        self,
        event_type: str,
        priority: int,
        actor: Optional[PlayerState] = None,
        payload: Optional[dict] = None,
    ) -> None:
        if payload is None:
            payload = {}
        if (
            event_type == "PLAYER_JOIN"
            and self.events
            and self.events[-1].type == "PLAYER_JOIN"
            and self.events[-1].day == self.day_count
            and self.events[-1].phase == self.phase.value
        ):
            names = list(self.events[-1].payload.get("names", []))
            if actor and actor.name not in names:
                names.append(actor.name)
                self.events[-1].payload["names"] = names
            return
        self.event_seq += 1
        event = GameEvent(
            seq=self.event_seq,
            type=event_type,
            priority=priority,
            day=self.day_count,
            phase=self.phase.value,
            actor_id=actor.id if actor else None,
            actor_name=actor.name if actor else None,
            payload=payload,
        )
        self.events.append(event)
        self.events = self.events[-200:]

    def add_log(self, message: str) -> None:
        self.log_event("SYSTEM", 0, payload={"message": message})

    def _is_name_taken(self, name: str) -> bool:
        return any(player.name == name for player in self.players.values())

    def _next_default_name(self) -> str:
        index = 1
        while True:
            candidate = f"玩家{index}"
            if not self._is_name_taken(candidate):
                return candidate
            index += 1

    def add_player(self, name: str, avatar_url: Optional[str], owner_id: Optional[str]) -> PlayerState:
        cleaned = name.strip()
        player_name = cleaned or self._next_default_name()
        if len(player_name) > 12 or "\n" in player_name or "\r" in player_name:
            raise ValueError("name_invalid")
        if self._is_name_taken(player_name):
            self.add_log(f"{player_name} 昵称已被占用。")
            raise ValueError("name_taken")
        if len(self.players) >= 9:
            raise ValueError("room_full")
        player_id = uuid.uuid4().hex
        player = PlayerState(id=player_id, name=player_name, avatar_url=avatar_url)
        self.players[player_id] = player
        if owner_id:
            self.owners[player_id] = owner_id
            if not self.host_user_id:
                self.host_user_id = owner_id
        self.log_event("PLAYER_JOIN", 0, actor=player, payload={"names": [player.name]})
        return player

    def remove_player(self, player_id: str) -> None:
        if player_id in self.players:
            player = self.players.pop(player_id)
            removed_owner = self.owners.pop(player_id, None)
            if removed_owner and removed_owner == self.host_user_id:
                self.host_user_id = next(iter(self.owners.values()), None)
            self.add_log(f"{player.name} 离开了房间。")

    def player_for_owner(self, owner_id: str) -> Optional[PlayerState]:
        for player_id, user_id in self.owners.items():
            if user_id == owner_id:
                return self.players.get(player_id)
        return None

    def is_host(self, owner_id: Optional[str]) -> bool:
        return bool(owner_id and self.host_user_id == owner_id)

    def reset(self) -> None:
        self.phase = Phase.LOBBY
        self.day_count = 0
        self.actions.clear()
        self.events.clear()
        self.event_seq = 0
        self.last_guard_target = None
        self.wolf_target = None
        self.witch_save_target = None
        self.witch_poison_target = None
        self.last_night_deaths = []
        self.special_state = False
        self.morning_order = []
        self.morning_index = 0
        self.morning_started_at = None
        self.morning_speaker_id = None
        for player in self.players.values():
            player.role = None
            player.kind = None
            player.alive = True
            player.notes.clear()
            player.lover_ids = []
            player.is_police = False
            player.is_chief = False
            player.witch_saved = False
            player.witch_poisoned = False
            player.explorer_bought = False
            player.hunter_shot = False
            player.white_wolf_exploded = False
            player.nerd_revealed = False
            player.rider_duel_used = False
            player.cupid_linked = False
        self.add_log("已重置游戏，等待玩家准备。")

    def set_mode(self, mode_name: str) -> None:
        try:
            self.mode = Mode[mode_name]
            self.add_log(f"已切换为 {self.mode.value}。")
        except KeyError:
            self.add_log("未识别的模式，仍使用默认配置。")

    def start_game(self) -> None:
        if self.phase != Phase.LOBBY:
            return
        if len(self.players) < 3:
            self.add_log("玩家不足 3 人，无法开始。")
            return
        if len(self.players) > 9:
            self.add_log("玩家超过 9 人，请移除部分玩家。")
            return
        game_mode = GameMode(game_mode=self.mode, num_players=len(self.players))
        self.log_event("GAME_START", 2, payload={"mode": self.mode.value})
        roles = game_mode.generate_role_list()
        for player, role in zip(self.players.values(), roles):
            player.role = role
            player.kind = Kind.WEREWOLF if role in (Role.WEREWOLF, Role.WHITE_WOLF) else Kind.VILLAGER
            player.alive = True
            player.notes.clear()
            player.lover_ids = []
            player.is_police = False
            player.is_chief = False
            player.witch_saved = False
            player.witch_poisoned = False
            player.explorer_bought = False
            player.hunter_shot = False
            player.white_wolf_exploded = False
            player.nerd_revealed = False
            player.rider_duel_used = False
            player.cupid_linked = False
        self.phase = Phase.BEFORE_ELECTION if len(self.players) >= 6 else Phase.NIGHT
        self.day_count = 0
        self.actions.clear()
        self.last_guard_target = None
        self.wolf_target = None
        self.witch_save_target = None
        self.witch_poison_target = None
        self.last_night_deaths = []
        self.special_state = False
        self.morning_order = []
        self.morning_index = 0
        self.morning_started_at = None
        self.morning_speaker_id = None
        self.add_log(f"{self._phase_day_label()}：游戏开始。")
        self.maybe_auto_advance()

    def record_action(
        self,
        owner_id: Optional[str],
        player_id: str,
        action: str,
        target_id: Optional[str],
        target_id_2: Optional[str],
        text: Optional[str] = None,
    ) -> tuple[bool, str]:
        if not owner_id:
            return False, "请先登录"
        if self.owners.get(player_id) != owner_id:
            return False, "无法控制该玩家"
        if player_id in self.actions and action not in (ActionType.MORNING_SPEAK, ActionType.MORNING_SKIP):
            return False, "本阶段已行动"
        player = self.players.get(player_id)
        if not player:
            return False, "玩家不存在"
        if not player.alive and action not in (ActionType.NERD_REVEAL, ActionType.HUNTER_SHOOT):
            return False, "玩家已死亡"
        ok, result = self._record_action_internal(player, action, target_id, target_id_2, text)
        if ok and self.actions.get(player.id) and self.actions[player.id].action == action:
            self.maybe_auto_advance()
        return ok, result

    def _record_action_internal(
        self,
        player: PlayerState,
        action: str,
        target_id: Optional[str],
        target_id_2: Optional[str],
        text: Optional[str],
    ) -> tuple[bool, str]:
        if action == ActionType.PASS:
            self.actions[player.id] = PendingAction(action)
            return True, "已跳过"

        if self.phase == Phase.BEFORE_ELECTION:
            return self._record_before_election_action(player, action)
        if self.phase == Phase.ELECTION:
            return self._record_election_action(player, action, target_id)
        if self.phase == Phase.NIGHT:
            return self._record_night_action(player, action, target_id, target_id_2)
        if self.phase == Phase.MORNING:
            return self._record_morning_action(player, action, target_id, text)
        if self.phase == Phase.DAY:
            return self._record_day_action(player, action, target_id)
        if self.phase == Phase.DUSK:
            return self._record_dusk_action(player, action, target_id)
        return False, "当前阶段无法操作"

    def _record_before_election_action(self, player: PlayerState, action: str) -> tuple[bool, str]:
        if action == ActionType.RAISE_HAND:
            player.is_police = True
            self.actions[player.id] = PendingAction(action)
            return True, "已报名竞选"
        if action == ActionType.POLICE_SKIP:
            self.actions[player.id] = PendingAction(action)
            return True, "已放弃竞选"
        return False, "该阶段不支持此操作"

    def _record_election_action(self, player: PlayerState, action: str, target_id: Optional[str]) -> tuple[bool, str]:
        if player.is_police:
            return False, "竞选者无法投票"
        if action == ActionType.ELECTION_SKIP:
            self.actions[player.id] = PendingAction(action)
            return True, "已弃权"
        if action == ActionType.ELECTION_VOTE:
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录投票"
        return False, "该阶段不支持此操作"

    def _record_day_action(self, player: PlayerState, action: str, target_id: Optional[str]) -> tuple[bool, str]:
        if player.nerd_revealed:
            return False, "白痴无法投票"
        if action == ActionType.DAY_SKIP:
            self.actions[player.id] = PendingAction(action)
            return True, "已弃权"
        if action == ActionType.DAY_VOTE:
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录投票"
        return False, "该阶段不支持此操作"

    def _record_morning_action(
        self, player: PlayerState, action: str, target_id: Optional[str], text: Optional[str]
    ) -> tuple[bool, str]:
        if not self.morning_speaker_id or player.id != self.morning_speaker_id:
            return False, "未轮到你发言"
        if action == ActionType.MORNING_SPEAK:
            cleaned = (text or "").strip()
            if not cleaned:
                return False, "请输入发言"
            if len(cleaned) > 200:
                return False, "发言不能超过 200 字"
            self.log_event(
                "SPEECH",
                1,
                actor=player,
                payload={"text": cleaned},
            )
            return True, "已发言"
        if action == ActionType.MORNING_SKIP:
            self._advance_morning_speaker()
            if not self.morning_speaker_id:
                self.maybe_auto_advance()
            return True, "已结束发言"
        if action == ActionType.WHITE_WOLF_BOOM and player.role == Role.WHITE_WOLF:
            if player.white_wolf_exploded:
                return False, "已使用过自爆"
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录自爆"
        if action == ActionType.RIDER_DUEL and player.role == Role.RIDER:
            if player.rider_duel_used:
                return False, "已使用过决斗"
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录决斗"
        return False, "该阶段不支持此操作"

    def _record_dusk_action(self, player: PlayerState, action: str, target_id: Optional[str]) -> tuple[bool, str]:
        if action == ActionType.HUNTER_SHOOT and player.role == Role.HUNTER:
            if player.alive:
                return False, "猎人未死亡无法肘击"
            if player.hunter_shot:
                return False, "已使用过肘击"
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录肘击"
        if action == ActionType.NERD_REVEAL and player.role == Role.NERD:
            if player.alive:
                return False, "白痴未死亡无法自爆"
            if player.nerd_revealed:
                return False, "已自爆过"
            self.actions[player.id] = PendingAction(action)
            return True, "已记录自爆"
        if action == ActionType.PASS:
            self.actions[player.id] = PendingAction(action)
            return True, "已跳过"
        return False, "该阶段不支持此操作"

    def _record_night_action(
        self, player: PlayerState, action: str, target_id: Optional[str], target_id_2: Optional[str]
    ) -> tuple[bool, str]:
        if action == ActionType.WOLF_KILL and player.role in (Role.WEREWOLF, Role.WHITE_WOLF):
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录猎杀"
        if action == ActionType.SEER_CHECK and player.role == Role.SEER:
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            target = self.players[target_id]
            result = "狼人" if target.kind == Kind.WEREWOLF else "好人"
            player.notes.append(f"你查验了 {target.name}：{result}")
            self.actions[player.id] = PendingAction(action, target_id)
            return True, f"查验结果：{target.name} 是{result}"
        if action == ActionType.GUARD_PROTECT and player.role == Role.GUARD:
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            if target_id == player.id:
                return False, "无法守护自己"
            if self.last_guard_target == target_id:
                return False, "不能连续守护同一人"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录守护"
        if action == ActionType.WITCH_SAVE and player.role == Role.WITCH:
            if player.witch_saved:
                return False, "解药已用过"
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            pending_target = self._pending_wolf_target()
            if not pending_target or target_id != pending_target:
                return False, "只能治疗昨夜遇害者"
            self.actions[player.id] = PendingAction(action, target_id)
            player.witch_saved = True
            return True, "已记录解药"
        if action == ActionType.WITCH_POISON and player.role == Role.WITCH:
            if player.witch_poisoned:
                return False, "毒药已用过"
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            player.witch_poisoned = True
            return True, "已记录毒药"
        if action == ActionType.CUPID_LINK and player.role == Role.CUPID:
            if player.cupid_linked:
                return False, "丘比特已连接过"
            if not self._valid_target(target_id) or not self._valid_target(target_id_2):
                return False, "请指定两个有效目标"
            if target_id == target_id_2:
                return False, "无法连接同一人"
            self.actions[player.id] = PendingAction(action, target_id, target_id_2)
            player.cupid_linked = True
            return True, "已记录连接"
        if action == ActionType.EXPLORER_BUY and player.role == Role.EXPLORER:
            if player.explorer_bought:
                return False, "已使用过收买"
            if not self._is_explorer_target(player):
                return False, "当前无法收买"
            self.actions[player.id] = PendingAction(action)
            return True, "已记录收买"
        if action == ActionType.HUNTER_SHOOT and player.role == Role.HUNTER:
            if player.alive:
                return False, "猎人未死亡无法肘击"
            if player.hunter_shot:
                return False, "已使用过肘击"
            if not self._valid_target(target_id):
                return False, "请指定有效目标"
            self.actions[player.id] = PendingAction(action, target_id)
            return True, "已记录肘击"
        if action == ActionType.PASS:
            self.actions[player.id] = PendingAction(action)
            return True, "已跳过"
        return False, "该阶段不支持此操作"
    def advance(self) -> None:
        if self.phase == Phase.BEFORE_ELECTION:
            self._resolve_before_election()
            prev_phase = self.phase
            self.phase = Phase.ELECTION
            self.log_event(
                "PHASE_CHANGE",
                1,
                payload={"from": prev_phase.value, "to": self.phase.value},
            )
            self.add_log(f"{self._phase_day_label()}。")
            self.maybe_auto_advance()
            return
        if self.phase == Phase.ELECTION:
            self._resolve_election()
            prev_phase = self.phase
            self.phase = Phase.NIGHT
            self.log_event(
                "PHASE_CHANGE",
                1,
                payload={"from": prev_phase.value, "to": self.phase.value},
            )
            self.add_log(f"{self._phase_day_label()}。")
            self.maybe_auto_advance()
            return
        if self.phase == Phase.NIGHT:
            self._resolve_night()
            winner = self._check_victory()
            if winner:
                self._end_game(winner)
                return
            prev_phase = self.phase
            self.phase = Phase.DAWN
            self.log_event(
                "PHASE_CHANGE",
                1,
                payload={"from": prev_phase.value, "to": self.phase.value},
            )
            self._log_dawn()
            self.maybe_auto_advance()
            return
        if self.phase == Phase.DAWN:
            prev_phase = self.phase
            self.phase = Phase.MORNING
            self.log_event(
                "PHASE_CHANGE",
                1,
                payload={"from": prev_phase.value, "to": self.phase.value},
            )
            self.add_log(f"{self._phase_day_label()}。")
            self._start_morning()
            self.maybe_auto_advance()
            return
        if self.phase == Phase.MORNING:
            self._resolve_morning()
            winner = self._check_victory()
            if winner:
                self._end_game(winner)
                return
            if self.special_state:
                self.special_state = False
                prev_phase = self.phase
                self.phase = Phase.NIGHT
                self.add_log(f"{self._phase_day_label()}。")
            else:
                prev_phase = self.phase
                self.phase = Phase.DAY
                self.add_log(f"{self._phase_day_label()}。")
            self.log_event(
                "PHASE_CHANGE",
                1,
                payload={"from": prev_phase.value, "to": self.phase.value},
            )
            self.maybe_auto_advance()
            return
        if self.phase == Phase.DAY:
            self._resolve_day()
            winner = self._check_victory()
            if winner:
                self._end_game(winner)
                return
            prev_phase = self.phase
            self.phase = Phase.DUSK
            self.log_event(
                "PHASE_CHANGE",
                1,
                payload={"from": prev_phase.value, "to": self.phase.value},
            )
            self.add_log(f"{self._phase_day_label()}。")
            self.maybe_auto_advance()
            return
        if self.phase == Phase.DUSK:
            self._resolve_dusk()
            winner = self._check_victory()
            if winner:
                self._end_game(winner)
                return
            self.day_count += 1
            prev_phase = self.phase
            self.phase = Phase.NIGHT
            self.log_event(
                "PHASE_CHANGE",
                1,
                payload={"from": prev_phase.value, "to": self.phase.value},
            )
            self.add_log(f"{self._phase_day_label()}。")
            self.maybe_auto_advance()

    def _resolve_before_election(self) -> None:
        for player in self.players.values():
            if player.id not in self.actions:
                player.is_police = False
        self.actions.clear()

    def _resolve_election(self) -> None:
        votes: Dict[str, float] = {}
        for player in self.players.values():
            if not player.alive or player.is_police:
                continue
            action = self.actions.get(player.id)
            if action and action.action == ActionType.ELECTION_VOTE and action.target_id:
                votes[action.target_id] = votes.get(action.target_id, 0) + 1
        self.actions.clear()
        if not votes:
            self.add_log("警长竞选无人投票，警长空缺。")
            return
        max_votes = max(votes.values())
        top = [pid for pid, count in votes.items() if count == max_votes]
        if len(top) == 1:
            chief = self.players[top[0]]
            for player in self.players.values():
                player.is_chief = False
            chief.is_chief = True
            self.add_log(f"{chief.name} 成为了警长。")
            self.log_event(
                "VOTE_RESULT",
                2,
                payload={"type": "election", "result": "chief", "name": chief.name},
            )
        else:
            self.add_log("投票平票，警长空缺。")
            self.log_event(
                "VOTE_RESULT",
                2,
                payload={"type": "election", "result": "tie"},
            )

    def _resolve_day(self) -> None:
        votes: Dict[str, float] = {}
        for player in self.players.values():
            if not player.alive or player.nerd_revealed:
                continue
            action = self.actions.get(player.id)
            if action and action.action == ActionType.DAY_VOTE and action.target_id:
                weight = 1.5 if player.is_chief else 1
                votes[action.target_id] = votes.get(action.target_id, 0) + weight
        self.actions.clear()
        if not votes:
            self.add_log("白天无人投票，平票无人出局。")
            return
        max_votes = max(votes.values())
        top = [pid for pid, count in votes.items() if count == max_votes]
        if len(top) == 1:
            target = self.players[top[0]]
            target.alive = False
            self.add_log(f"{target.name} 被放逐。")
            self.log_event(
                "VOTE_RESULT",
                2,
                payload={"type": "day", "result": "exiled", "name": target.name},
            )
        else:
            self.add_log("白天投票平票，无人出局。")
            self.log_event(
                "VOTE_RESULT",
                2,
                payload={"type": "day", "result": "tie"},
            )

    def _resolve_night(self) -> None:
        self.wolf_target = self._pending_wolf_target()
        self.witch_save_target = None
        self.witch_poison_target = None
        self._resolve_cupid()

        for action in self.actions.values():
            if action.action == ActionType.WITCH_SAVE:
                self.witch_save_target = action.target_id
            if action.action == ActionType.WITCH_POISON:
                self.witch_poison_target = action.target_id

        deaths: List[PlayerState] = []
        protected_target = None
        for player_id, action in self.actions.items():
            player = self.players.get(player_id)
            if not player:
                continue
            if action.action == ActionType.GUARD_PROTECT:
                protected_target = action.target_id
                self.last_guard_target = action.target_id

        if self.wolf_target and self.wolf_target != protected_target:
            if not (self.witch_save_target and self.witch_save_target == self.wolf_target):
                target = self.players.get(self.wolf_target)
                if target:
                    deaths.append(target)

        if self.witch_poison_target:
            target = self.players.get(self.witch_poison_target)
            if target and target.alive:
                deaths.append(target)

        for player_id, action in self.actions.items():
            player = self.players.get(player_id)
            if not player or action.action != ActionType.HUNTER_SHOOT:
                continue
            target = self.players.get(action.target_id)
            if target and target.alive:
                deaths.append(target)
                player.hunter_shot = True

        self._resolve_explorer(deaths)
        self._resolve_lovers(deaths)

        self.last_night_deaths = []
        unique_deaths = {}
        for player in deaths:
            unique_deaths[player.id] = player
        for player in unique_deaths.values():
            player.alive = False
            self.last_night_deaths.append(player.name)

        self.actions.clear()
        if not self.last_night_deaths:
            self.add_log("昨夜平安无事。")

    def _resolve_morning(self) -> None:
        for player_id, action in list(self.actions.items()):
            player = self.players.get(player_id)
            if not player:
                continue
            if action.action == ActionType.WHITE_WOLF_BOOM and player.role == Role.WHITE_WOLF:
                target = self.players.get(action.target_id)
                if target and target.alive:
                    target.alive = False
                    player.alive = False
                    player.white_wolf_exploded = True
                    self.special_state = True
                    self.add_log(f"{player.name} 自爆带走了 {target.name}。")
            if action.action == ActionType.RIDER_DUEL and player.role == Role.RIDER:
                target = self.players.get(action.target_id)
                if target and target.alive:
                    if target.kind == Kind.WEREWOLF:
                        target.alive = False
                        self.special_state = True
                        self.add_log(f"{player.name} 决斗成功，击杀 {target.name}。")
                    else:
                        player.alive = False
                        self.add_log(f"{player.name} 决斗失败，自身倒下。")
                    player.rider_duel_used = True
        self.actions.clear()
        self.morning_order = []
        self.morning_index = 0
        self.morning_started_at = None
        self.morning_speaker_id = None

    def _resolve_dusk(self) -> None:
        for player_id, action in list(self.actions.items()):
            player = self.players.get(player_id)
            if not player:
                continue
            if action.action == ActionType.HUNTER_SHOOT and player.role == Role.HUNTER:
                target = self.players.get(action.target_id)
                if target and target.alive:
                    target.alive = False
                    player.hunter_shot = True
                    self.add_log(f"{player.name} 肘击带走了 {target.name}。")
            if action.action == ActionType.NERD_REVEAL and player.role == Role.NERD:
                if not player.nerd_revealed:
                    player.nerd_revealed = True
                    player.alive = True
                    self.add_log(f"{player.name} 揭示身份，回到游戏。")
        self.actions.clear()

    def _resolve_explorer(self, deaths: List[PlayerState]) -> None:
        for player in list(deaths):
            if player.role == Role.EXPLORER and not player.explorer_bought:
                explorer_action = self.actions.get(player.id)
                if explorer_action and explorer_action.action == ActionType.EXPLORER_BUY:
                    player.explorer_bought = True
                    deaths.remove(player)
                    self.add_log(f"寻宝士使用了收买机会，{player.name} 幸存。")

    def _resolve_lovers(self, deaths: List[PlayerState]) -> None:
        for player in list(deaths):
            for lover_id in player.lover_ids:
                lover = self.players.get(lover_id)
                if lover and lover.alive:
                    lover.alive = False
                    deaths.append(lover)
                    self.add_log(f"情人殉情，{lover.name} 随 {player.name} 倒下。")

    def _check_victory(self) -> Optional[str]:
        game_mode = GameMode(game_mode=self.mode, num_players=len(self.players))
        over, winner = game_mode.check_victory(self)
        if over:
            if winner == "None":
                return "无人胜利"
            if isinstance(winner, Kind):
                return winner.value
            return str(winner)
        return None

    def _resolve_cupid(self) -> None:
        for player_id, action in self.actions.items():
            player = self.players.get(player_id)
            if not player or action.action != ActionType.CUPID_LINK:
                continue
            player_a = self.players.get(action.target_id)
            player_b = self.players.get(action.target_id_2)
            if not player_a or not player_b:
                continue
            player_a.lover_ids = [player_b.id]
            player_b.lover_ids = [player_a.id]
            if player_a.kind == player_b.kind:
                player.kind = player_a.kind
            else:
                player.kind = Kind.CUPID
                player_a.kind = Kind.CUPID
                player_b.kind = Kind.CUPID
            self.add_log(f"丘比特连接了 {player_a.name} 与 {player_b.name}。")

    def _end_game(self, winner: str) -> None:
        self.phase = Phase.END
        self.add_log(f"游戏结束：{winner}。")
        self.log_event("GAME_END", 2, payload={"winner": winner})

    def _valid_target(self, target_id: Optional[str]) -> bool:
        return bool(target_id and target_id in self.players and self.players[target_id].alive)

    def _phase_day_label(self) -> str:
        return f"第{self.day_count}天·{self.phase.value}"

    def _log_dawn(self) -> None:
        if self.last_night_deaths:
            names = "、".join(self.last_night_deaths)
            self.add_log(f"{self._phase_day_label()}：昨夜死亡 {names}。")
            self.log_event(
                "DEATH_ANNOUNCED",
                2,
                payload={"names": list(self.last_night_deaths)},
            )
        else:
            self.add_log(f"{self._phase_day_label()}：平安夜。")

    def _start_morning(self) -> None:
        players_in_order = [player for player in self.players.values() if player.alive]
        if not players_in_order:
            self.morning_order = []
            self.morning_index = 0
            self.morning_started_at = None
            self.morning_speaker_id = None
            return
        ordered = [players_in_order[0]] + list(reversed(players_in_order[1:]))
        self.morning_order = [player.id for player in ordered]
        self.morning_index = 0
        self.morning_speaker_id = self.morning_order[0]
        self.morning_started_at = time.time()
        self.log_event(
            "TURN",
            1,
            actor=self.players[self.morning_speaker_id],
            payload={"kind": "speech"},
        )

    def _advance_morning_speaker(self) -> None:
        if not self.morning_order:
            self.morning_speaker_id = None
            self.morning_started_at = None
            return
        self.morning_index += 1
        if self.morning_index >= len(self.morning_order):
            self.morning_speaker_id = None
            self.morning_started_at = None
            return
        self.morning_speaker_id = self.morning_order[self.morning_index]
        self.morning_started_at = time.time()
        self.log_event(
            "TURN",
            1,
            actor=self.players[self.morning_speaker_id],
            payload={"kind": "speech"},
        )

    def _check_morning_timeout(self) -> None:
        if not self.morning_started_at or not self.morning_speaker_id:
            return
        if time.time() - self.morning_started_at >= 120:
            speaker = self.players.get(self.morning_speaker_id)
            if speaker:
                self.add_log(f"{speaker.name} 发言超时，轮到下一位。")
            self._advance_morning_speaker()

    def _required_action_players(self) -> set:
        required = set()
        if self.phase == Phase.BEFORE_ELECTION:
            for player in self.players.values():
                if player.alive:
                    required.add(player.id)
        elif self.phase == Phase.ELECTION:
            for player in self.players.values():
                if player.alive and not player.is_police:
                    required.add(player.id)
        elif self.phase == Phase.NIGHT:
            for player in self.players.values():
                if not player.alive:
                    if player.role == Role.HUNTER and not player.hunter_shot:
                        required.add(player.id)
                    continue
                if player.role in (Role.WEREWOLF, Role.WHITE_WOLF, Role.SEER, Role.GUARD):
                    required.add(player.id)
                if player.role == Role.CUPID and not player.cupid_linked:
                    required.add(player.id)
                if player.role == Role.WITCH and not (player.witch_saved and player.witch_poisoned):
                    required.add(player.id)
                if player.role == Role.EXPLORER and self._is_explorer_target(player):
                    required.add(player.id)
        elif self.phase == Phase.MORNING:
            if self.morning_speaker_id:
                required.add(self.morning_speaker_id)
        elif self.phase == Phase.DAY:
            for player in self.players.values():
                if player.alive and not player.nerd_revealed:
                    required.add(player.id)
        elif self.phase == Phase.DUSK:
            for player in self.players.values():
                if player.role == Role.HUNTER and not player.alive and not player.hunter_shot:
                    required.add(player.id)
                if player.role == Role.NERD and not player.alive and not player.nerd_revealed:
                    required.add(player.id)
        return required

    def _is_explorer_target(self, explorer: PlayerState) -> bool:
        pending_target = self._pending_wolf_target()
        if not pending_target:
            return False
        return explorer.id == pending_target and not explorer.explorer_bought

    def _pending_wolf_target(self) -> Optional[str]:
        for action in self.actions.values():
            if action.action == ActionType.WOLF_KILL and action.target_id:
                return action.target_id
        return None

    def maybe_auto_advance(self) -> None:
        if self.phase not in (
            Phase.BEFORE_ELECTION,
            Phase.ELECTION,
            Phase.NIGHT,
            Phase.DAWN,
            Phase.MORNING,
            Phase.DAY,
            Phase.DUSK,
        ):
            return
        if self.phase == Phase.MORNING:
            self._check_morning_timeout()
            if not self.morning_speaker_id:
                self.advance()
            return
        required = self._required_action_players()
        if not required:
            self.advance()
            return
        if required.issubset(self.actions.keys()):
            self.advance()
    def available_actions_for(self, player: Optional[PlayerState]) -> List[dict]:
        if not player:
            return []
        actions: List[dict] = []
        if self.phase == Phase.BEFORE_ELECTION:
            actions.append(self._action_entry(ActionType.RAISE_HAND, "举手竞选"))
            actions.append(self._action_entry(ActionType.POLICE_SKIP, "弃权"))
            return actions
        if self.phase == Phase.ELECTION:
            if player.is_police or not player.alive:
                return []
            actions.append(self._action_entry(ActionType.ELECTION_VOTE, "投票选警长", 1))
            actions.append(self._action_entry(ActionType.ELECTION_SKIP, "弃权"))
            return actions
        if self.phase == Phase.NIGHT:
            if not player.alive:
                if player.role == Role.HUNTER and not player.hunter_shot:
                    actions.append(self._action_entry(ActionType.HUNTER_SHOOT, "肘击带走", 1))
                return actions
            if player.role in (Role.WEREWOLF, Role.WHITE_WOLF):
                actions.append(self._action_entry(ActionType.WOLF_KILL, "猎杀", 1))
                actions.append(self._action_entry(ActionType.PASS, "跳过"))
            if player.role == Role.SEER:
                actions.append(self._action_entry(ActionType.SEER_CHECK, "预言查验", 1))
                actions.append(self._action_entry(ActionType.PASS, "跳过"))
            if player.role == Role.GUARD:
                actions.append(self._action_entry(ActionType.GUARD_PROTECT, "守护", 1))
                actions.append(self._action_entry(ActionType.PASS, "跳过"))
            if player.role == Role.WITCH:
                pending_target = self._pending_wolf_target()
                if not player.witch_saved and pending_target:
                    actions.append(
                        self._action_entry(ActionType.WITCH_SAVE, "治疗", 1, [pending_target])
                    )
                if not player.witch_poisoned:
                    actions.append(self._action_entry(ActionType.WITCH_POISON, "毒害", 1))
                actions.append(self._action_entry(ActionType.PASS, "跳过"))
            if player.role == Role.CUPID and not player.cupid_linked:
                actions.append(self._action_entry(ActionType.CUPID_LINK, "连接情侣", 2))
                actions.append(self._action_entry(ActionType.PASS, "跳过"))
            if player.role == Role.EXPLORER and self._is_explorer_target(player):
                actions.append(self._action_entry(ActionType.EXPLORER_BUY, "收买", 0))
                actions.append(self._action_entry(ActionType.PASS, "跳过"))
            return actions
        if self.phase == Phase.MORNING:
            if not player.alive:
                return []
            if self.morning_speaker_id != player.id:
                return []
            actions.append(self._action_entry(ActionType.MORNING_SPEAK, "提交发言", 0))
            actions.append(self._action_entry(ActionType.MORNING_SKIP, "结束发言", 0))
            if player.role == Role.WHITE_WOLF and not player.white_wolf_exploded:
                actions.append(self._action_entry(ActionType.WHITE_WOLF_BOOM, "自爆带走", 1))
            if player.role == Role.RIDER and not player.rider_duel_used:
                actions.append(self._action_entry(ActionType.RIDER_DUEL, "决斗", 1))
            return actions
        if self.phase == Phase.DAY:
            if not player.alive or player.nerd_revealed:
                return []
            actions.append(self._action_entry(ActionType.DAY_VOTE, "投票", 1))
            actions.append(self._action_entry(ActionType.DAY_SKIP, "弃权"))
            return actions
        if self.phase == Phase.DUSK:
            if player.role == Role.HUNTER and not player.alive and not player.hunter_shot:
                actions.append(self._action_entry(ActionType.HUNTER_SHOOT, "肘击", 1))
            if player.role == Role.NERD and not player.alive and not player.nerd_revealed:
                actions.append(self._action_entry(ActionType.NERD_REVEAL, "自爆留场", 0))
            actions.append(self._action_entry(ActionType.PASS, "跳过"))
        return actions

    def _action_entry(
        self,
        action_id: str,
        label: str,
        target_count: int = 0,
        allowed_targets: Optional[List[str]] = None,
    ) -> dict:
        targets = allowed_targets if allowed_targets is not None else self._default_targets()
        return {
            "id": action_id,
            "label": label,
            "target_count": target_count,
            "targets": targets,
        }

    def _default_targets(self) -> List[str]:
        return [player.id for player in self.players.values() if player.alive]

    def payload(self, viewer_id: Optional[str]) -> dict:
        viewer_player = self.player_for_owner(viewer_id) if viewer_id else None
        remaining = None
        if self.phase == Phase.MORNING and self.morning_started_at:
            remaining = max(0, int(120 - (time.time() - self.morning_started_at)))
        current_turn = None
        if self.phase == Phase.MORNING and self.morning_speaker_id:
            current_turn = {
                "type": "speech",
                "player_id": self.morning_speaker_id,
                "remaining": remaining,
            }
        return {
            "phase": self.phase.value,
            "phase_code": self.phase.name,
            "day": self.day_count,
            "mode": self.mode.name,
            "modes": [{"code": mode.name, "label": mode.value} for mode in Mode],
            "host_id": self.host_user_id,
            "state": {
                "day": self.day_count,
                "phase": self.phase.value,
                "phase_code": self.phase.name,
                "current_turn": current_turn,
            },
            "viewer": {
                "user_id": viewer_id,
                "player_id": viewer_player.id if viewer_player else None,
                "is_host": self.is_host(viewer_id),
            },
            "viewer_role": viewer_player.display_role() if viewer_player else "",
            "viewer_kind": viewer_player.kind.value if viewer_player and viewer_player.kind else "",
            "viewer_notes": viewer_player.notes if viewer_player else [],
            "morning": {
                "speaker_id": self.morning_speaker_id,
                "remaining": remaining,
            },
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "alive": player.alive,
                    "is_chief": player.is_chief,
                    "is_police": player.is_police,
                    "avatar_url": player.avatar_url,
                }
                for player in self.players.values()
            ],
            "available_actions": self.available_actions_for(viewer_player),
            "events": [event.to_dict() for event in self.events],
            "limits": {"min_players": 3, "max_players": 9},
        }

    def to_json(self, viewer_id: Optional[str]) -> str:
        return json.dumps(self.payload(viewer_id), ensure_ascii=False)
