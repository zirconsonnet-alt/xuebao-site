(() => {
  const stateCycle = {
    "-1": 1,
    "1": 0,
    "0": -1,
  };

  function setStateClass(cell, value) {
    cell.dataset.state = String(value);
    cell.classList.remove("state-unknown", "state-true", "state-false");
    if (value === 1) {
      cell.classList.add("state-true");
    } else if (value === 0) {
      cell.classList.add("state-false");
    } else {
      cell.classList.add("state-unknown");
    }
  }

  function syncState() {
    const board = document.getElementById("board");
    if (!board) return;
    const size = Number(board.dataset.size || 5);
    const matrix = Array.from({ length: size }, () => Array(size).fill(-1));
    board.querySelectorAll(".bingo-cell").forEach((cell) => {
      const row = Number(cell.dataset.row);
      const col = Number(cell.dataset.col);
      const value = Number(cell.dataset.state);
      if (!Number.isNaN(row) && !Number.isNaN(col)) {
        matrix[row][col] = Number.isNaN(value) ? -1 : value;
      }
    });
    const stateInput = document.getElementById("state-json");
    if (stateInput) {
      stateInput.value = JSON.stringify(matrix);
    }
  }

  function handleCellClick(event) {
    const cell = event.target.closest(".bingo-cell");
    if (!cell) return;
    const current = cell.dataset.state || "-1";
    const next = stateCycle[current] ?? -1;
    setStateClass(cell, next);
    syncState();
  }

  document.addEventListener("click", handleCellClick);

  document.addEventListener("contextmenu", (event) => {
    const cell = event.target.closest(".bingo-cell");
    if (!cell) return;
    event.preventDefault();
    setStateClass(cell, 0);
    syncState();
  });

  document.addEventListener("htmx:afterSwap", (event) => {
    if (!event.target) return;
    if (event.target.id === "board" || event.target.id === "game") {
      syncState();
    }
  });

  window.addEventListener("load", syncState);
})();
