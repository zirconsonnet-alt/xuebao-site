(() => {
  const page = document.querySelector('.page');
  if (!page) return;

  const roomPath = page.dataset.roomPath || '';
  const assetPath = page.dataset.assetPath || '';
  const loggedIn = page.dataset.loggedIn === 'true';
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${window.location.host}${roomPath}/ws`);

  const phaseLabel = document.getElementById('phaseLabel');
  const statusLine = document.getElementById('statusLine');
  const joinBtn = document.getElementById('joinBtn');
  const leaveBtn = document.getElementById('leaveBtn');
  const startBtn = document.getElementById('startBtn');
  const resetBtn = document.getElementById('resetBtn');
  const joinName = document.getElementById('joinName');
  const hostControls = document.getElementById('hostControls');
  const modeSelect = document.getElementById('modeSelect');
  const playerRing = document.getElementById('playerRing');
  const currentState = document.getElementById('currentState');
  const keyTimeline = document.getElementById('keyTimeline');
  const fullLog = document.getElementById('fullLog');
  const logSearch = document.getElementById('logSearch');
  const logFilterKey = document.getElementById('logFilterKey');
  const logFilterAll = document.getElementById('logFilterAll');
  const logFilterSpeech = document.getElementById('logFilterSpeech');
  const logFilterSystem = document.getElementById('logFilterSystem');
  const actionHint = document.getElementById('actionHint');
  const actionButtons = document.getElementById('actionButtons');
  const roleLine = document.getElementById('roleLine');
  const notesBox = document.getElementById('notesBox');
  const playerDetail = document.getElementById('playerDetail');

  function sendMessage(payload) {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }

  let latestState = null;
  let lastPhaseCode = null;
  let pendingAction = null;
  let hasActed = false;
  let selectableTargets = new Set();
  let morningTimer = null;
  let lastMorningSpeakerId = null;
  let logFilter = 'key';
  let logKeyword = '';
  let pendingActionId = null;

  function setStatus(text) {
    if (statusLine) statusLine.textContent = text;
  }

  function render(state) {
    latestState = state;
    const phaseCode = state.phase_code || '';
    if (phaseCode && phaseCode !== lastPhaseCode) {
      pendingAction = null;
      selectableTargets = new Set();
      hasActed = false;
      lastPhaseCode = phaseCode;
      lastMorningSpeakerId = null;
      if (morningTimer) {
        clearTimeout(morningTimer);
        morningTimer = null;
      }
    }

    if (page) {
      const isLobby = phaseCode === 'LOBBY';
      page.classList.toggle('is-lobby', isLobby);
      page.classList.toggle('is-game', !isLobby);
    }

    const phaseText = state.phase_code ? `${state.phase}` : state.phase;
    if (phaseLabel) {
      const dayNumber = state.day || 1;
      phaseLabel.textContent = `${phaseText} · 第 ${dayNumber} 天`;
    }

    if (modeSelect && state.modes) {
      modeSelect.innerHTML = '';
      state.modes.forEach((mode) => {
        const option = document.createElement('option');
        option.value = mode.code;
        option.textContent = mode.label;
        if (state.mode === mode.code) option.selected = true;
        modeSelect.appendChild(option);
      });
    }

    const isHost = state.viewer && state.viewer.is_host;
    if (hostControls) {
      hostControls.style.display = isHost ? 'flex' : 'none';
    }

    if (joinBtn) {
      joinBtn.disabled = !loggedIn || (state.viewer && state.viewer.player_id);
    }
    if (leaveBtn) {
      leaveBtn.disabled = !state.viewer || !state.viewer.player_id;
    }

    if (!loggedIn) {
      setStatus('请先登录后加入房间。');
    } else if (state.viewer && state.viewer.player_id) {
      setStatus(isHost ? '你是房主，可开始游戏。' : '已加入房间。');
    } else {
      setStatus('加入房间后可行动。');
    }

    renderPlayers(state);

    renderLogPanel(state);

    renderActions(state);
  }

  function renderActions(state) {
    if (!actionHint || !actionButtons || !roleLine) return;
    actionButtons.innerHTML = '';
    const actions = state.available_actions || [];
    const filteredActions = actions.filter((action) => action.target_count <= 1);
    const hasUnsupported = actions.some((action) => action.target_count > 1);
    const inRoom = state.viewer && state.viewer.player_id;
    const phaseCode = state.phase_code || '';
    const morningInfo = state.morning || {};
    const speakerId = morningInfo.speaker_id;
    const remaining = morningInfo.remaining;

    const viewerRole = state.viewer_role || '';
    const viewerKind = state.viewer_kind || '';
    if (viewerRole && viewerKind) {
      roleLine.textContent = `你的身份：${viewerRole} · ${viewerKind}`;
    } else if (viewerRole) {
      roleLine.textContent = `你的身份：${viewerRole}`;
    } else {
      roleLine.textContent = '身份未分配';
    }

    if (notesBox) {
      const notes = state.viewer_notes || [];
      notesBox.innerHTML = '';
      if (!inRoom) {
        notesBox.textContent = '加入房间后查看秘密线索。';
      } else if (notes.length) {
        const title = document.createElement('strong');
        title.textContent = '秘密线索';
        const list = document.createElement('ul');
        notes.forEach((note) => {
          const item = document.createElement('li');
          item.textContent = note;
          list.appendChild(item);
        });
        notesBox.appendChild(title);
        notesBox.appendChild(list);
      } else {
        notesBox.textContent = '暂无秘密线索。';
      }
    }

    if (!inRoom) {
      actionHint.textContent = '加入房间后可行动。';
      pendingAction = null;
      selectableTargets = new Set();
      updateSelectableTargets();
      return;
    }

    if (phaseCode === 'END') {
      actionHint.textContent = '游戏结束，可返回大厅。';
      const backBtn = document.createElement('button');
      backBtn.type = 'button';
      backBtn.className = 'primary';
      backBtn.textContent = '返回大厅';
      backBtn.onclick = () => {
        sendMessage({ type: 'back_to_lobby' });
      };
      actionButtons.appendChild(backBtn);
      pendingAction = null;
      selectableTargets = new Set();
      updateSelectableTargets();
      return;
    }

    if (phaseCode === 'MORNING') {
      if (speakerId !== lastMorningSpeakerId) {
        if (morningTimer) {
          clearTimeout(morningTimer);
          morningTimer = null;
        }
        lastMorningSpeakerId = speakerId;
      }
      const speaker = (state.players || []).find((p) => p.id === speakerId);
      const isSpeaker = speakerId && state.viewer && state.viewer.player_id === speakerId;
      const timeHint = typeof remaining === 'number' ? `（剩余 ${remaining}s）` : '';
      if (!isSpeaker) {
        actionHint.textContent = speaker ? `等待 ${speaker.name} 发言${timeHint}` : '等待发言开始。';
        pendingAction = null;
        selectableTargets = new Set();
        updateSelectableTargets();
        return;
      }
      actionHint.textContent = `轮到你发言${timeHint}`;
      const speechBox = document.createElement('div');
      speechBox.className = 'speech-box';
      const textarea = document.createElement('textarea');
      textarea.placeholder = '输入发言内容，最多 200 字';
      textarea.maxLength = 200;
      speechBox.appendChild(textarea);
      const controls = document.createElement('div');
      controls.className = 'speech-controls';
      const speakBtn = document.createElement('button');
      speakBtn.type = 'button';
      speakBtn.className = 'primary';
      speakBtn.textContent = '提交发言';
      speakBtn.onclick = () => {
        const text = textarea.value.trim();
        if (!text) return;
        submitAction('morning_speak', null, text);
        textarea.value = '';
      };
      const skipBtn = document.createElement('button');
      skipBtn.type = 'button';
      skipBtn.className = 'ghost';
      skipBtn.textContent = '结束发言';
      skipBtn.onclick = () => {
        submitAction('morning_skip', null, null);
      };
      controls.appendChild(speakBtn);
      controls.appendChild(skipBtn);
      speechBox.appendChild(controls);
      actionButtons.appendChild(speechBox);

      const targetActions = filteredActions.filter((action) => action.target_count === 1);
      targetActions.forEach((action) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'ghost';
        button.textContent = action.label;
        button.onclick = () => {
          pendingAction = action;
          selectableTargets = new Set(action.targets || []);
          actionHint.textContent = '请选择目标玩家。';
          updateSelectableTargets();
        };
        actionButtons.appendChild(button);
      });

      if (typeof remaining === 'number' && remaining > 0) {
        morningTimer = setTimeout(() => {
          submitAction('morning_skip', null, null);
        }, remaining * 1000);
      }
      updateSelectableTargets();
      return;
    }

    if (!filteredActions.length) {
      actionHint.textContent = hasUnsupported
        ? '当前阶段包含双目标行动，暂不支持。'
        : '当前阶段无法行动。';
      pendingAction = null;
      selectableTargets = new Set();
      updateSelectableTargets();
      return;
    }

    if (hasActed) {
      actionHint.textContent = '已行动，等待其他玩家。';
      pendingAction = null;
      selectableTargets = new Set();
      updateSelectableTargets();
      return;
    }

    actionHint.textContent = pendingAction
      ? '请选择目标玩家。'
      : '选择行动并执行。';

    filteredActions.forEach((action, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = index === 0 ? 'primary' : 'ghost';
      button.textContent = action.label;
      button.disabled = hasActed;
      button.onclick = () => {
        if (hasActed) return;
        if (action.target_count >= 1) {
          pendingAction = action;
          selectableTargets = new Set(action.targets || []);
          actionHint.textContent = '请选择目标玩家。';
          updateSelectableTargets();
        } else {
          submitAction(action.id, null);
        }
      };
      actionButtons.appendChild(button);
    });
    updateSelectableTargets();
  }

  function renderLogPanel(state) {
    renderCurrentState(state);
    renderKeyTimeline(state);
    renderFullLog(state);
  }

  function renderCurrentState(state) {
    if (!currentState) return;
    const roomState = state.state || {};
    const dayNumber = roomState.day ?? state.day ?? 0;
    const phaseText = roomState.phase || state.phase || '';
    const currentTurn = roomState.current_turn;
    let turnLine = '当前行动：等待玩家操作';
    if (currentTurn && currentTurn.type === 'speech') {
      const speaker = (state.players || []).find((p) => p.id === currentTurn.player_id);
      const name = speaker ? speaker.name : '未知玩家';
      const remain = typeof currentTurn.remaining === 'number' ? `（剩余 ${currentTurn.remaining}s）` : '';
      turnLine = `当前行动：轮到 ${name} 发言${remain}`;
    }
    currentState.innerHTML = '';
    const title = document.createElement('div');
    title.className = 'current-state__title';
    title.textContent = `Day ${dayNumber} · ${phaseText}`;
    const turn = document.createElement('div');
    turn.className = 'current-state__turn';
    turn.textContent = turnLine;
    const actions = document.createElement('div');
    actions.className = 'current-state__actions';
    const keyBtn = document.createElement('button');
    keyBtn.className = 'ghost';
    keyBtn.type = 'button';
    keyBtn.dataset.logFilter = 'key';
    keyBtn.textContent = '只看关键';
    const allBtn = document.createElement('button');
    allBtn.className = 'ghost';
    allBtn.type = 'button';
    allBtn.dataset.logFilter = 'all';
    allBtn.textContent = '展开全部';
    actions.appendChild(keyBtn);
    actions.appendChild(allBtn);
    currentState.appendChild(title);
    currentState.appendChild(turn);
    currentState.appendChild(actions);
    currentState.querySelectorAll('[data-log-filter]').forEach((btn) => {
      btn.onclick = () => setLogFilter(btn.dataset.logFilter);
    });
  }

  function renderKeyTimeline(state) {
    if (!keyTimeline) return;
    const events = (state.events || []).filter((ev) => ev.priority >= 2);
    keyTimeline.innerHTML = '';
    if (!events.length) {
      const empty = document.createElement('div');
      empty.className = 'log-empty';
      empty.textContent = '暂无关键事件。';
      keyTimeline.appendChild(empty);
      return;
    }
    events.forEach((event) => {
      const node = renderEventItem(event, state);
      node.classList.add('event-key');
      keyTimeline.appendChild(node);
    });
  }

  function renderFullLog(state) {
    if (!fullLog) return;
    const events = (state.events || []).slice().sort((a, b) => a.seq - b.seq);
    const filtered = events.filter((ev) => matchLogFilter(ev) && matchLogKeyword(ev));
    fullLog.innerHTML = '';
    if (!filtered.length) {
      const empty = document.createElement('div');
      empty.className = 'log-empty';
      empty.textContent = '暂无日志。';
      fullLog.appendChild(empty);
      return;
    }
    const dayGroups = [];
    let dayGroup = null;
    let phaseGroup = null;
    filtered.forEach((event) => {
      if (!dayGroup || dayGroup.day !== event.day) {
        dayGroup = { day: event.day, phases: [] };
        dayGroups.push(dayGroup);
        phaseGroup = null;
      }
      if (!phaseGroup || phaseGroup.phase !== event.phase) {
        phaseGroup = { phase: event.phase, events: [] };
        dayGroup.phases.push(phaseGroup);
      }
      phaseGroup.events.push(event);
    });
    const latestDay = Math.max(...dayGroups.map((g) => g.day));
    dayGroups.forEach((group) => {
      const dayDetails = document.createElement('details');
      dayDetails.open = group.day === latestDay;
      const daySummary = document.createElement('summary');
      daySummary.textContent = `Day ${group.day}`;
      dayDetails.appendChild(daySummary);
      group.phases.forEach((phaseBlock, index) => {
        const phaseDetails = document.createElement('details');
        phaseDetails.open = group.day === latestDay && index === group.phases.length - 1;
        const phaseSummary = document.createElement('summary');
        phaseSummary.textContent = phaseBlock.phase;
        phaseDetails.appendChild(phaseSummary);
        phaseBlock.events.forEach((event) => {
          phaseDetails.appendChild(renderEventItem(event, state));
        });
        dayDetails.appendChild(phaseDetails);
      });
      fullLog.appendChild(dayDetails);
    });
  }

  function renderEventItem(event, state) {
    const item = document.createElement('div');
    item.className = `event-item priority-${event.priority}`;
    let title = '';
    let detail = '';
    if (event.type === 'PLAYER_JOIN') {
      const names = (event.payload && event.payload.names) || [];
      title = '玩家加入';
      detail = names.join('、');
    } else if (event.type === 'SPEECH') {
      title = `${event.actor_name || '玩家'} 发言`;
      detail = event.payload && event.payload.text ? event.payload.text : '';
      item.classList.add('event-speech');
    } else if (event.type === 'TURN') {
      title = '轮到发言';
      detail = event.actor_name || '';
    } else if (event.type === 'DEATH_ANNOUNCED') {
      title = '昨夜死亡';
      detail = ((event.payload && event.payload.names) || []).join('、');
    } else if (event.type === 'VOTE_RESULT') {
      const info = event.payload || {};
      if (info.result === 'chief') {
        title = '警长选举';
        detail = `警长：${info.name || '未知'}`;
      } else if (info.result === 'exiled') {
        title = '投票结果';
        detail = `放逐：${info.name || '未知'}`;
      } else {
        title = '投票结果';
        detail = '平票';
      }
    } else if (event.type === 'GAME_START') {
      title = '游戏开始';
      detail = event.payload && event.payload.mode ? `模式：${event.payload.mode}` : '';
    } else if (event.type === 'GAME_END') {
      title = '游戏结束';
      detail = event.payload && event.payload.winner ? `胜利：${event.payload.winner}` : '';
    } else if (event.type === 'PHASE_CHANGE') {
      title = '阶段变化';
      const info = event.payload || {};
      detail = `${info.from || ''} → ${info.to || ''}`.trim();
    } else if (event.type === 'SYSTEM') {
      title = '系统';
      detail = event.payload && event.payload.message ? event.payload.message : '';
      item.classList.add('event-system');
    } else {
      title = event.type;
      detail = event.payload && event.payload.message ? event.payload.message : '';
    }
    const titleEl = document.createElement('div');
    titleEl.className = 'event-title';
    titleEl.textContent = title;
    item.appendChild(titleEl);
    if (detail) {
      const detailEl = document.createElement('div');
      detailEl.className = 'event-detail';
      detailEl.textContent = detail;
      item.appendChild(detailEl);
    }
    return item;
  }

  function eventText(event) {
    const base = `${event.type} ${(event.actor_name || '')}`.trim();
    const payloadText = event.payload && typeof event.payload === 'object'
      ? JSON.stringify(event.payload)
      : '';
    return `${base} ${payloadText}`.toLowerCase();
  }

  function matchLogFilter(event) {
    if (logFilter === 'key') return event.priority >= 2;
    if (logFilter === 'speech') return event.type === 'SPEECH';
    if (logFilter === 'system') return event.type === 'SYSTEM';
    return true;
  }

  function matchLogKeyword(event) {
    if (!logKeyword) return true;
    return eventText(event).includes(logKeyword);
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'error') {
      setStatus(`操作失败：${data.message}`);
      return;
    }
    if (data.type === 'action_result') {
      if (!data.ok) {
        setStatus(`操作失败：${data.message}`);
        pendingActionId = null;
        return;
      }
      if (pendingActionId && latestState) {
        if (latestState.phase_code !== 'MORNING' || pendingActionId === 'morning_skip') {
          hasActed = true;
          if (actionHint) {
            actionHint.textContent = '已行动，等待其他玩家。';
          }
        }
      }
      pendingActionId = null;
      return;
    }
    if (data.type === 'joined') {
      setStatus('已加入房间。');
      return;
    }
    if (data.phase) {
      render(data);
    }
  };

  window.addEventListener('resize', () => {
    if (latestState) {
      renderPlayers(latestState);
      updateSelectableTargets();
    }
  });

  if (joinBtn) {
    joinBtn.onclick = () => {
      sendMessage({
        type: 'join',
        display_name: joinName ? joinName.value.trim() : '',
      });
    };
  }

  if (leaveBtn) {
    leaveBtn.onclick = () => {
      sendMessage({ type: 'leave' });
    };
  }

  if (startBtn) {
    startBtn.onclick = () => {
      sendMessage({ type: 'start', mode: modeSelect ? modeSelect.value : undefined });
    };
  }

  if (resetBtn) {
    resetBtn.onclick = () => {
      sendMessage({ type: 'reset' });
    };
  }

  function setLogFilter(nextFilter) {
    logFilter = nextFilter;
    if (logFilterKey) logFilterKey.classList.toggle('is-active', logFilter === 'key');
    if (logFilterAll) logFilterAll.classList.toggle('is-active', logFilter === 'all');
    if (logFilterSpeech) logFilterSpeech.classList.toggle('is-active', logFilter === 'speech');
    if (logFilterSystem) logFilterSystem.classList.toggle('is-active', logFilter === 'system');
    if (latestState) renderFullLog(latestState);
  }

  if (logFilterKey) {
    logFilterKey.onclick = () => setLogFilter('key');
  }
  if (logFilterAll) {
    logFilterAll.onclick = () => setLogFilter('all');
  }
  if (logFilterSpeech) {
    logFilterSpeech.onclick = () => setLogFilter('speech');
  }
  if (logFilterSystem) {
    logFilterSystem.onclick = () => setLogFilter('system');
  }
  if (logSearch) {
    logSearch.oninput = (event) => {
      logKeyword = (event.target.value || '').trim().toLowerCase();
      if (latestState) renderFullLog(latestState);
    };
  }
  setLogFilter(logFilter);

  function renderPlayers(state) {
    if (!playerRing) return;
    playerRing.innerHTML = '';
    const players = state.players || [];
    if (!players.length) return;

    const ringSize = playerRing.clientWidth || 320;
    const itemSize = 86;
    const radius = Math.max(0, ringSize / 2 - itemSize / 2 - 8);
    const showPolice = state.phase_code === 'BEFORE_ELECTION' || state.phase_code === 'ELECTION';

    players.forEach((player, index) => {
      const angle = (Math.PI * 2 * index) / players.length - Math.PI / 2;
      const x = ringSize / 2 + radius * Math.cos(angle) - itemSize / 2;
      const y = ringSize / 2 + radius * Math.sin(angle) - itemSize / 2;
      const isSelectable = pendingAction && selectableTargets.has(player.id);
      const card = document.createElement('div');
      card.className = `player-orbit${player.alive ? '' : ' is-dead'}${isSelectable ? ' is-selectable' : ''}`;
      card.style.left = `${x}px`;
      card.style.top = `${y}px`;
      card.dataset.playerId = player.id;
      card.dataset.playerName = player.name;
      card.dataset.playerAlive = player.alive ? '存活' : '已淘汰';
      card.dataset.playerPolice = showPolice && player.is_police ? '上警' : '';
      card.dataset.playerChief = player.is_chief ? '警长' : '';
      const avatar = document.createElement('img');
      avatar.src = player.avatar_url || (assetPath + '/assets/avatar_default.svg');
      avatar.alt = 'avatar';
      card.appendChild(avatar);
      card.onmouseenter = (event) => {
        if (!playerDetail) return;
        const target = event.currentTarget;
        const rect = target.getBoundingClientRect();
        const hostRect = playerRing.getBoundingClientRect();
        const tags = [target.dataset.playerChief, target.dataset.playerPolice].filter(Boolean).join(' · ');
        playerDetail.innerHTML = '';
        const name = document.createElement('div');
        name.className = 'detail-name';
        name.textContent = target.dataset.playerName;
        const status = document.createElement('div');
        status.className = 'detail-status';
        status.textContent = target.dataset.playerAlive;
        playerDetail.appendChild(name);
        playerDetail.appendChild(status);
        if (tags) {
          const tagEl = document.createElement('div');
          tagEl.className = 'detail-tags';
          tagEl.textContent = tags;
          playerDetail.appendChild(tagEl);
        }
        playerDetail.style.left = `${rect.right - hostRect.left + 12}px`;
        playerDetail.style.top = `${rect.top - hostRect.top}px`;
        playerDetail.classList.remove('hidden');
      };
      card.onmouseleave = () => {
        if (playerDetail) {
          playerDetail.classList.add('hidden');
        }
      };
      card.onclick = () => {
        if (!pendingAction || hasActed) return;
        if (!selectableTargets.has(player.id)) return;
        submitAction(pendingAction.id, player.id);
      };
      playerRing.appendChild(card);
    });
  }

  function updateSelectableTargets() {
    if (!playerRing) return;
    const cards = playerRing.querySelectorAll('.player-orbit');
    cards.forEach((card) => {
      const id = card.dataset.playerId;
      const selectable = pendingAction && selectableTargets.has(id);
      card.classList.toggle('is-selectable', Boolean(selectable));
    });
    if (!pendingAction && playerDetail) {
      playerDetail.classList.add('hidden');
    }
  }

  function submitAction(actionId, targetId, text) {
    if (!latestState || !latestState.viewer || !latestState.viewer.player_id) {
      setStatus('请先加入房间。');
      return;
    }
    pendingActionId = actionId;
    sendMessage({
      type: 'action',
      player_id: latestState.viewer.player_id,
      action: actionId,
      target_id: targetId,
      target_id_2: null,
      text: text || null,
    });
    pendingAction = null;
    selectableTargets = new Set();
    updateSelectableTargets();
  }
})();
