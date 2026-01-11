(() => {
  function getInput() {
    return document.getElementById("expression");
  }

  function needsSeparator(text) {
    if (!text.length) {
      return false;
    }
    const last = text[text.length - 1];
    return /\d/.test(last) || last === ")";
  }

  function insertValue(value) {
    const input = getInput();
    if (!input) return;
    const separator = needsSeparator(input.value) ? " " : "";
    input.value = `${input.value}${separator}${value}`.trimStart();
    input.focus();
  }

  function clearExpression() {
    const input = getInput();
    if (!input) return;
    input.value = "";
    input.focus();
  }

  function backspaceExpression() {
    const input = getInput();
    if (!input) return;
    input.value = input.value.slice(0, -1);
    input.focus();
  }

  document.addEventListener("click", (event) => {
    const insertButton = event.target.closest("[data-insert]");
    if (insertButton) {
      insertValue(insertButton.dataset.insert || "");
      return;
    }

    const card = event.target.closest(".card");
    if (card && card.dataset.value) {
      insertValue(card.dataset.value);
      return;
    }

    if (event.target.closest("#clear")) {
      clearExpression();
      return;
    }

    if (event.target.closest("#undo")) {
      backspaceExpression();
    }
  });

  document.addEventListener("htmx:afterSwap", (event) => {
    if (!event.target) return;
    if (event.target.id === "game") {
      const input = getInput();
      if (input) {
        input.focus();
      }
    }
  });
})();
