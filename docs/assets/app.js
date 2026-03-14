const LOCAL_HOSTS = new Set(["127.0.0.1", "localhost"]);

function getDashboardSources() {
  const live = [{ url: "/api/dashboard", mode: "live" }];
  const statics = [
    { url: "./data/dashboard.json", mode: "static" },
    { url: "data/dashboard.json", mode: "static" },
  ];
  return LOCAL_HOSTS.has(window.location.hostname) ? [...live, ...statics] : [...statics, ...live];
}

async function fetchDashboard() {
  let lastError = null;
  for (const source of getDashboardSources()) {
    try {
      const response = await fetch(source.url, { cache: "no-store" });
      if (!response.ok) {
        lastError = new Error(`Failed to load dashboard from ${source.url}`);
        continue;
      }
      const data = await response.json();
      return { data, mode: source.mode };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("Failed to load dashboard");
}

function renderCard(item) {
  const published = item.published_at ? new Date(item.published_at).toLocaleString() : "Unknown time";
  return `
    <a class="card" href="${item.url || "#"}" target="_blank" rel="noreferrer">
      <div class="card-meta">
        <span>${item.source_name}</span>
        <span class="bucket bucket-${item.bucket}">${item.bucket}</span>
      </div>
      <h4>${item.title}</h4>
      <p>${item.snippet || ""}</p>
      <div class="card-foot">
        <span>${published}</span>
      </div>
    </a>
  `;
}

function renderMiniCard(item) {
  const published = item.published_at ? new Date(item.published_at).toLocaleDateString() : "Unknown";
  const reason = item.metadata?.filter_reason || "";
  return `
    <a class="mini-card" href="${item.url || "#"}" target="_blank" rel="noreferrer">
      <div class="card-meta">
        <span>${item.source_name}</span>
        <span class="bucket bucket-${item.bucket}">${item.bucket}</span>
      </div>
      <h4>${item.title}</h4>
      <p>${item.snippet || ""}</p>
      ${reason ? `<div class="reason">${reason}</div>` : ""}
      <div class="card-foot">
        <span>${published}</span>
      </div>
    </a>
  `;
}

function renderBoard(boardId, payload) {
  const root = document.getElementById(boardId);
  const delivery = payload.published || [];
  if (!delivery.length) {
    root.innerHTML = `<div class="empty">No finance-qualified items published yet.</div>`;
    return;
  }
  root.innerHTML = delivery.map(renderCard).join("");
}

function renderReviewBoard(boardId, payload) {
  const root = document.getElementById(boardId);
  const review = payload.review || [];
  if (!review.length) {
    root.innerHTML = `<div class="empty compact">No review items.</div>`;
    return;
  }
  root.innerHTML = review.slice(0, 6).map(renderMiniCard).join("");
}

function renderBoardStatus(elementId, payload) {
  const root = document.getElementById(elementId);
  const published = (payload.published || []).length;
  const review = (payload.review || []).length;
  root.textContent = published ? `Published ${published}` : `Preview ${review}`;
}

function renderFailures(failures) {
  const root = document.getElementById("failures");
  if (!failures.length) {
    root.innerHTML = "<li>No current failures.</li>";
    return;
  }
  root.innerHTML = failures
    .map((failure) => `<li><strong>${failure.source_name || failure.source_id}</strong> <span>${failure.error}</span></li>`)
    .join("");
}

async function refreshPipeline() {
  const button = document.getElementById("refresh-button");
  if (button.dataset.mode === "static") {
    return;
  }
  button.disabled = true;
  button.textContent = "Refreshing…";
  try {
    await fetch("/api/refresh", { method: "POST" });
    setTimeout(load, 2000);
  } finally {
    setTimeout(() => {
      button.disabled = false;
      button.textContent = "Refresh Pipeline";
    }, 2500);
  }
}

function setRefreshMode(mode) {
  const button = document.getElementById("refresh-button");
  button.dataset.mode = mode;
  if (mode === "static") {
    button.disabled = true;
    button.textContent = "Static Snapshot";
    button.title = "GitHub Pages serves a static snapshot. Refresh locally, then export and push.";
    return;
  }
  button.disabled = false;
  button.textContent = "Refresh Pipeline";
  button.title = "";
}

async function load() {
  try {
    const { data, mode } = await fetchDashboard();
    setRefreshMode(mode);
    document.getElementById("total-delivery").textContent = data.stats.total_delivery_items;
    document.getElementById("total-review").textContent = data.stats.total_review_items;
    document.getElementById("total-failures").textContent = data.stats.total_failures;
    document.getElementById("provider-status").textContent = data.provider_ready
      ? `live · ${data.provider}`
      : `preview · ${data.provider}`;

    renderBoard("direct_rss", data.boards.direct_rss);
    renderBoard("fast_news_and_leaks", data.boards.fast_news_and_leaks);
    renderBoard("long_form", data.boards.long_form);
    renderReviewBoard("direct_rss_review", data.boards.direct_rss);
    renderReviewBoard("fast_news_and_leaks_review", data.boards.fast_news_and_leaks);
    renderReviewBoard("long_form_review", data.boards.long_form);
    renderBoardStatus("direct-status", data.boards.direct_rss);
    renderBoardStatus("fast-status", data.boards.fast_news_and_leaks);
    renderBoardStatus("long-status", data.boards.long_form);
    document.getElementById("review-status").textContent = `Queue ${data.stats.total_review_items}`;
    renderFailures(data.failures || []);
  } catch (error) {
    console.error(error);
  }
}

document.getElementById("refresh-button").addEventListener("click", refreshPipeline);
load();
