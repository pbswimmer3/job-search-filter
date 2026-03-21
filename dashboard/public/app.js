let expandedId = null;
let promoteTargetId = null;

// Tab switching
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const view = tab.dataset.tab;
    document.getElementById("qualified-view").style.display = view === "qualified" ? "" : "none";
    document.getElementById("unqualified-view").style.display = view === "unqualified" ? "" : "none";
    if (view === "unqualified") loadUnqualified();
  });
});

// Filters
const filterStatus = document.getElementById("filter-status");
const filterSource = document.getElementById("filter-source");
const filterLocation = document.getElementById("filter-location");
const filterRemote = document.getElementById("filter-remote");
const filterScore = document.getElementById("filter-score");
const filterScoreDisplay = document.getElementById("filter-score-display");

let locationDebounce = null;
filterStatus.addEventListener("change", loadQualified);
filterSource.addEventListener("change", loadQualified);
filterLocation.addEventListener("input", () => {
  clearTimeout(locationDebounce);
  locationDebounce = setTimeout(loadQualified, 400);
});
filterRemote.addEventListener("change", loadQualified);
filterScore.addEventListener("input", () => {
  filterScoreDisplay.textContent = filterScore.value;
  loadQualified();
});

function scoreBadgeClass(score) {
  if (score >= 80) return "score-high";
  if (score >= 60) return "score-mid";
  return "score-low";
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// Load qualified roles
async function loadQualified() {
  const params = new URLSearchParams();
  if (filterStatus.value) params.set("status", filterStatus.value);
  if (filterSource.value) params.set("source", filterSource.value);
  if (filterLocation.value.trim()) params.set("location", filterLocation.value.trim());
  if (filterRemote.checked) params.set("remote", "true");
  if (parseInt(filterScore.value) > 50) params.set("min_score", filterScore.value);

  const res = await fetch(`/api/qualified?${params}`);
  const roles = await res.json();
  const tbody = document.getElementById("qualified-body");
  const empty = document.getElementById("qualified-empty");

  if (roles.length === 0) {
    tbody.innerHTML = "";
    empty.style.display = "";
    return;
  }
  empty.style.display = "none";

  let html = "";
  for (const r of roles) {
    const isExpanded = expandedId === r.id;
    html += `<tr class="clickable-row ${isExpanded ? "expanded" : ""}" onclick="toggleRow(${r.id})">
      <td>${escapeHtml(r.company)}</td>
      <td class="truncate">${r.url ? `<a href="${escapeHtml(r.url)}" target="_blank" onclick="event.stopPropagation()">${escapeHtml(r.title)}</a>` : escapeHtml(r.title)}</td>
      <td><span class="score-badge ${scoreBadgeClass(r.score)}">${r.score}</span></td>
      <td><span class="source-tag">${escapeHtml(r.source)}</span></td>
      <td class="truncate">${escapeHtml(r.location)}</td>
      <td><span class="remote-badge ${r.remote ? "remote-yes" : "remote-no"}">${r.remote ? "YES" : "—"}</span></td>
      <td onclick="event.stopPropagation()">
        <select class="status-select" onchange="updateStatus(${r.id}, this.value)">
          ${["new", "applied", "interviewing", "offer", "rejected", "archived"]
            .map((s) => `<option value="${s}" ${r.status === s ? "selected" : ""}>${s}</option>`)
            .join("")}
        </select>
      </td>
      <td style="white-space:nowrap;color:#555;font-size:12px">${escapeHtml(r.date_found)}</td>
    </tr>`;

    if (isExpanded) {
      html += `<tr class="notes-row"><td colspan="8">
        <div class="notes-container">
          ${r.score_rationale ? `<div class="rationale">${escapeHtml(r.score_rationale)}</div>` : ""}
          <textarea placeholder="Notes..." onblur="updateNotes(${r.id}, this.value)">${escapeHtml(r.notes || "")}</textarea>
        </div>
      </td></tr>`;
    }
  }
  tbody.innerHTML = html;
}

// Load unqualified roles
async function loadUnqualified() {
  const res = await fetch("/api/unqualified");
  const roles = await res.json();
  const tbody = document.getElementById("unqualified-body");
  const empty = document.getElementById("unqualified-empty");

  if (roles.length === 0) {
    tbody.innerHTML = "";
    empty.style.display = "";
    return;
  }
  empty.style.display = "none";

  let html = "";
  for (const r of roles) {
    html += `<tr>
      <td>${escapeHtml(r.company)}</td>
      <td class="truncate">${r.url ? `<a href="${escapeHtml(r.url)}" target="_blank">${escapeHtml(r.title)}</a>` : escapeHtml(r.title)}</td>
      <td><span class="score-badge ${scoreBadgeClass(r.score)}">${r.score}</span></td>
      <td><span class="source-tag">${escapeHtml(r.source)}</span></td>
      <td class="truncate">${escapeHtml(r.location)}</td>
      <td><span class="remote-badge ${r.remote ? "remote-yes" : "remote-no"}">${r.remote ? "YES" : "—"}</span></td>
      <td style="white-space:nowrap;color:#555;font-size:12px">${escapeHtml(r.date_found)}</td>
      <td><button class="btn-promote" onclick="openPromoteModal(${r.id})">Promote</button></td>
    </tr>`;
  }
  tbody.innerHTML = html;
}

// Toggle row expansion
function toggleRow(id) {
  expandedId = expandedId === id ? null : id;
  loadQualified();
}

// Update status
async function updateStatus(id, status) {
  await fetch(`/api/qualified/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  loadStats();
}

// Update notes
async function updateNotes(id, notes) {
  await fetch(`/api/qualified/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
  });
}

// Promote modal
function openPromoteModal(id) {
  promoteTargetId = id;
  document.getElementById("promote-modal").classList.add("active");
}

function closePromoteModal() {
  promoteTargetId = null;
  document.getElementById("promote-modal").classList.remove("active");
}

async function confirmPromote() {
  if (!promoteTargetId) return;
  const score = parseInt(document.getElementById("promote-score").value);
  await fetch(`/api/unqualified/${promoteTargetId}/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ score }),
  });
  closePromoteModal();
  loadUnqualified();
  loadQualified();
  loadStats();
}

// Stats
async function loadStats() {
  const res = await fetch("/api/stats");
  const stats = await res.json();
  document.getElementById("stat-active").textContent = stats.total_active;
  document.getElementById("stat-applied").textContent = stats.applied;
  document.getElementById("stat-interviewing").textContent = stats.interviewing;
  document.getElementById("stat-avg-score").textContent = stats.avg_score;
}

// Initial load
loadStats();
loadQualified();

// Auto-refresh
setInterval(loadStats, 60000);
setInterval(() => {
  const activeTab = document.querySelector(".tab.active")?.dataset.tab;
  if (activeTab === "qualified") loadQualified();
  else loadUnqualified();
}, 300000);
