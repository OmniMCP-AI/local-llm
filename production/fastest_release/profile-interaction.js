const selector = "a[data-run-id]";

for (const cohort of document.querySelectorAll("[data-cohort]")) {
  const preview = cohort.querySelector("[data-profile-preview]");
  if (!preview) continue;
  const links = [...cohort.querySelectorAll(selector)];

  function showPreview(event) {
    const link = event.target.closest(selector);
    if (link) preview.textContent = link.dataset.preview;
  }

  function clearPreview(event) {
    const link = event.target.closest(selector);
    if (link && !link.contains(event.relatedTarget)) {
      const focused = document.activeElement?.closest(selector);
      preview.textContent = focused && cohort.contains(focused) && focused !== link ? focused.dataset.preview : "";
    }
  }

  cohort.addEventListener("pointerover", showPreview);
  cohort.addEventListener("pointerout", clearPreview);
  cohort.addEventListener("focusin", showPreview);
  cohort.addEventListener("focusout", clearPreview);
  cohort.addEventListener("click", (event) => {
    const link = event.target.closest(selector);
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const drawer = document.getElementById(`run-${link.dataset.runId}`);
    if (!drawer) return;
    event.preventDefault();
    for (const item of document.querySelectorAll(".run-drawer")) item.open = item === drawer;
    for (const item of document.querySelectorAll(selector)) item.dataset.selected = String(item.dataset.runId === link.dataset.runId);
    history.replaceState(null, "", link.getAttribute("href"));
    drawer.querySelector("summary").focus();
  });
}
