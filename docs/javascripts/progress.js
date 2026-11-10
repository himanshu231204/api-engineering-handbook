// Progress tracker: remembers which chapters a learner has ticked on progress.md.
// Per-viewer convenience only — stored in this browser's localStorage, never sent anywhere.
(function () {
  var KEY = "hb-progress-v1";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; }
  }
  function save(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode: ignore */ }
  }

  function init() {
    // Only the progress page carries data-total; part pages have a static bar.
    var box = document.querySelector(".hb-progress[data-total]");
    if (!box) return;
    var state = load();
    var items = document.querySelectorAll(".md-typeset .task-list-item");
    var total = items.length;

    function refresh() {
      var done = 0;
      items.forEach(function (li) { if (li.querySelector("input").checked) done++; });
      box.querySelector(".hb-progress-done").textContent = done;
      box.querySelector(".hb-progress-bar span").style.width = (total ? (100 * done / total) : 0) + "%";
    }

    items.forEach(function (li) {
      var link = li.querySelector("a");
      var input = li.querySelector("input");
      if (!link || !input) return;
      var id = link.getAttribute("href");
      input.disabled = false;
      input.checked = !!state[id];
      input.addEventListener("change", function () {
        state[id] = input.checked;
        if (!input.checked) delete state[id];
        save(state);
        refresh();
      });
    });
    refresh();
  }

  // Material's instant navigation swaps pages without a full reload.
  if (typeof document$ !== "undefined") { document$.subscribe(init); }
  else { document.addEventListener("DOMContentLoaded", init); }
})();
