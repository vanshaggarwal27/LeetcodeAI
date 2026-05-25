const API_BASE_URL = "https://leetcodeai-backend.onrender.com";

const colors = { devto:'#3b49df', hashnode:'#2962ff', medium:'#00ab6c', webhook:'#f7a01a' };

document.addEventListener('DOMContentLoaded', () => {
  setLoading(true);
  fetchStatsFromBackend()
    .catch(() => {
      showBanner("Couldn't reach backend — showing local data.");
      return loadFromLocalStorage();
    })
    .finally(() => setLoading(false));
});

async function fetchStatsFromBackend() {
  const res = await fetch(`${API_BASE_URL}/dashboard/stats`);
  if (!res.ok) throw new Error('Bad response');
  const { total_posts, platform_counts, week_activity, recent } = await res.json();

  document.getElementById('totalPosts').textContent = total_posts;
  document.getElementById('thisWeek').textContent =
    Object.values(week_activity).reduce((a, b) => a + b, 0);
  document.getElementById('streakCount').textContent =
    calculateStreakFromWeekMap(week_activity) + ' 🔥';

  renderWeekGridFromMap(week_activity);
  renderPlatformBarsFromMap(platform_counts);
  renderHistory(recent);
}

function loadFromLocalStorage() {
  return new Promise(resolve => {
    chrome.storage.local.get({ publishHistory: [] }, ({ publishHistory }) => {
      renderDashboard(publishHistory);
      resolve();
    });
  });
}

// --- Loading / error UI ---
function setLoading(on) {
  document.getElementById('loadingBanner').style.display = on ? 'block' : 'none';
}
function showBanner(msg) {
  const el = document.getElementById('errorBanner');
  el.textContent = msg;
  el.style.display = 'block';
}

// --- Streak from week_activity map (keyed YYYY-MM-DD) ---
function calculateStreakFromWeekMap(weekMap) {
  let streak = 0;
  for (let i = 0; i < 7; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    if (weekMap[key]) streak++;
    else if (i > 0) break; 
  }
  return streak;
}

// --- Render from backend shapes ---
function renderWeekGridFromMap(weekMap) {
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const grid = document.getElementById('weekGrid');
  grid.innerHTML = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    const key = d.toISOString().slice(0, 10);
    const count = weekMap[key] || 0;
    return `<div class="week-day">
      <div class="week-label">${days[d.getDay()]}</div>
      <div class="week-box ${count > 0 ? 'active' : ''}">${count || ''}</div>
    </div>`;
  }).join('');
}

function renderPlatformBarsFromMap(counts) {
  const container = document.getElementById('platformBars');
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    container.innerHTML = '<div class="empty-state">No platform data yet</div>';
    return;
  }
  const max = Math.max(...entries.map(e => e[1]));
  container.innerHTML = entries.map(([name, count]) => `
    <div class="platform-bar">
      <span class="platform-name">${name}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width:${(count/max)*100}%;background:${colors[name]||'#f7a01a'}"></div>
      </div>
      <span class="bar-count">${count}</span>
    </div>`).join('');
}

// --- Local-storage fallback renders (original logic, streak bug fixed) ---
function renderDashboard(history) {
  document.getElementById('totalPosts').textContent = history.length;
  document.getElementById('streakCount').textContent = calculateStreak(history) + ' 🔥';
  document.getElementById('thisWeek').textContent = countThisWeek(history);
  renderWeekGrid(history);
  renderPlatformBars(history);
  renderHistory(history);
}

function getDateStr(d) { return new Date(d).toISOString().slice(0, 10); }

function calculateStreak(history) {
  if (!history.length) return 0;
  const uniqueDates = [...new Set(history.map(h => getDateStr(h.date)))].sort().reverse();
  let streak = 0;
  for (const dateStr of uniqueDates) {
    const diff = Math.floor((new Date().setHours(0,0,0,0) - new Date(dateStr)) / 86400000);
    if (diff === streak) streak++; 
    else break;
  }
  return streak;
}

function countThisWeek(history) {
  const ago = new Date(); ago.setDate(ago.getDate() - 7);
  return history.filter(h => new Date(h.date) >= ago).length;
}

function renderWeekGrid(history) {
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const grid = document.getElementById('weekGrid');
  grid.innerHTML = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (6 - i));
    const key = d.toISOString().slice(0, 10);
    const count = history.filter(h => getDateStr(h.date) === key).length;
    return `<div class="week-day">
      <div class="week-label">${days[d.getDay()]}</div>
      <div class="week-box ${count > 0 ? 'active' : ''}">${count || ''}</div>
    </div>`;
  }).join('');
}

function renderPlatformBars(history) {
  const counts = {};
  history.forEach(h => (h.platforms || []).forEach(p => { counts[p] = (counts[p] || 0) + 1; }));
  renderPlatformBarsFromMap(counts);
}

function renderHistory(history) {
  const container = document.getElementById('historyList');
  if (!history.length) {
    container.innerHTML = '<div class="empty-state">No posts yet. Solve a problem and publish your first blog! </div>';
    return;
  }
  container.innerHTML = history.slice(0, 10).map(h => {
    const dateStr = new Date(h.date).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
    return `<div class="history-item">
      <div>
        <div class="history-title">${h.title || 'Unknown Problem'}</div>
        <div class="history-platforms"> ${(h.platforms||[]).join(', ') || 'unknown'}</div>
      </div>
      <div class="history-date">${dateStr}</div>
    </div>`;
  }).join('');
}