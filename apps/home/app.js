(() => {
  const body = document.body;
  if (!body) return;
  requestAnimationFrame(() => {
    body.classList.add("is-loaded");
  });
})();
