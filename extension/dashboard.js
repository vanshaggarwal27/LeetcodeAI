document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.local.get({ publishHistory: [] }, (result) => {
    renderDashboard(result.publishHistory);
  });
});

function renderDashboard(history) {
  document.getElementById('totalPosts').textContent = history.length;
  document.getElementById('streakCount').textContent = calculateStreak(history) + ' 🔥';
  document.getElementById('thisWeek').textContent = countThisWeek(history);
  renderWeekGrid(history);
  renderPlatformBars(history);
  renderHistory(history);
}

function getDateStr(dateStr) {
  return new Date(dateStr).toISOString().slice(0, 10);
}

function calculateStreak(history) {
  if (!history.length) return 0;
  const uniqueDates = [...new Set(history.map(h => getDateStr(h.date)))].sort().reverse();
  let streak = 0;
  for (const dateStr of uniqueDates) {
    const diffDays = Math.floor(
      (new Date().setHours(0,0,0,0) - new Date(dateStr)) / 86400000
    );
    if (diffDays <= streak) streak++;
    else break;
  }
  return streak;
}

function countThisWeek(history) {
  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);
  return history.filter(h => new Date(h.date) >= weekAgo).length;
}

function renderWeekGrid(history) {
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const last7 = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return d;
  });
  const grid = document.getElementById('weekGrid');
  grid.innerHTML = last7.map(d => {
    const dateStr = d.toISOString().slice(0, 10);
    const count = history.filter(h => getDateStr(h.date) === dateStr).length;
    return `<div class="week-day">
      <div class="week-label">${days[d.getDay()]}</div>
      <div class="week-box ${count > 0 ? 'active' : ''}">${count || ''}</div>
    </div>`;
  }).join('');
}

function renderPlatformBars(history) {
  const container = document.getElementById('platformBars');
  const counts = {};
  history.forEach(h => (h.platforms || []).forEach(p => {
    counts[p] = (counts[p] || 0) + 1;
  }));
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    container.innerHTML = '<div class="empty-state">No platform data yet</div>';
    return;
  }
  const max = Math.max(...entries.map(e => e[1]));
  const colors = { devto:'#3b49df', hashnode:'#2962ff', medium:'#00ab6c', webhook:'#f7a01a' };
  container.innerHTML = entries.map(([name, count]) => `
    <div class="platform-bar">
      <span class="platform-name">${name}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width:${(count/max)*100}%;background:${colors[name]||'#f7a01a'}"></div>
      </div>
      <span class="bar-count">${count}</span>
    </div>`).join('');
}

function renderHistory(history) {
  const container = document.getElementById('historyList');
  if (!history.length) {
    container.innerHTML = '<div class="empty-state">No posts yet. Solve a problem and publish your first blog! 🚀</div>';
    return;
  }
  container.innerHTML = history.slice(0, 10).map(h => {
    const dateStr = new Date(h.date).toLocaleDateString('en-US',
      { month:'short', day:'numeric', year:'numeric' });
    return `<div class="history-item">
      <div>
        <div class="history-title">${h.title || 'Unknown Problem'}</div>
        <div class="history-platforms">📤 ${(h.platforms||[]).join(', ') || 'unknown'}</div>
      </div>
      <div class="history-date">${dateStr}</div>
    </div>`;
  }).join('');
}
