import React, { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from "recharts";
import { ActivityCalendar } from "react-activity-calendar";
import { Tooltip as ReactTooltip } from "react-tooltip";
import "react-tooltip/dist/react-tooltip.css";
import { Code, Flame, CalendarDays, Activity, PieChart as PieChartIcon, History, ChevronRight } from "lucide-react";

const COLORS = ["#f7a01a", "#8a2be2", "#00C49F", "#FFBB28", "#FF8042"];

export default function StatsDashboard({ token, api }) {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await api("/dashboard/stats", {}, token);
        setStats(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, [token, api]);

  if (loading) return <div className="empty-state" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
    <Activity className="animate-spin" style={{ margin: '0 auto 16px', color: 'var(--primary)', animation: 'spin 2s linear infinite' }} size={32} />
    <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    <div style={{fontWeight: 500}}>Loading your analytics...</div>
  </div>;
  
  if (error) return <div className="alert error">{error}</div>;
  if (!stats) return <div className="empty-state">No stats available.</div>;

  const thisWeekCount = (stats.daily_activity || [])
    .slice(-7)
    .reduce((sum, day) => sum + day.count, 0);

  const currentYear = new Date().getFullYear();
  const last5Years = Array.from({length: 5}, (_, i) => (currentYear - i).toString());
  
  const dataYears = stats.daily_activity?.length > 0 
    ? stats.daily_activity.map(item => item.date.split('-')[0])
    : [];

  const availableYears = [...new Set([...last5Years, ...dataYears])].sort().reverse();

  const generateYearData = (yearStr) => {
    const days = [];
    const year = parseInt(yearStr);
    const todayStr = new Date().toISOString().split('T')[0];
    
    for (let month = 0; month < 12; month++) {
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        // Render ALL 365 days of the year, even future dates, to fill the entire width
        days.push({ date: dateStr, count: 0, level: 0 });
      }
    }
    // If no days were generated (e.g. somehow future year?), just push today so calendar doesn't crash
    if (days.length === 0) {
      days.push({ date: todayStr, count: 0, level: 0 });
    }
    return days;
  };

  const activityData = generateYearData(selectedYear);
  if (stats.daily_activity?.length > 0) {
    const activityMap = new Map(stats.daily_activity.map(item => [item.date, item]));
    activityData.forEach(day => {
      if (activityMap.has(day.date)) {
        day.count = activityMap.get(day.date).count;
        day.level = activityMap.get(day.date).level;
      }
    });
  }

  const pieData = stats.platform_counts?.length > 0 ? stats.platform_counts : [{ name: "No Data", value: 1 }];
  const pieColors = stats.platform_counts?.length > 0 ? COLORS : ["#e2e8f0"];

  const cardStyle = { background: 'rgba(255, 255, 255, 0.8)', padding: '24px', borderRadius: '20px', border: '1px solid rgba(0, 0, 0, 0.08)', boxShadow: '0 8px 32px rgba(0, 0, 0, 0.04)', transition: 'transform 0.3s ease, box-shadow 0.3s ease', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' };
  const sectionStyle = { background: 'rgba(255, 255, 255, 0.8)', padding: '28px', borderRadius: '20px', border: '1px solid rgba(0, 0, 0, 0.08)', boxShadow: '0 8px 32px rgba(0, 0, 0, 0.04)' };
  const gradientText = { color: 'var(--primary)', display: 'inline-block' };

  return (
    <div className="stats-container" style={{ animation: 'fadeIn 0.5s ease-out' }}>
      <header className="topbar" style={{ marginBottom: '32px' }}>
        <div>
          <p className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', fontSize: '13px', marginBottom: '8px' }}><Activity size={16}/> Analytics Hub</p>
          <h1 style={{ fontSize: '32px', fontWeight: '800', letterSpacing: '-0.5px', margin: 0 }}>Stats & <span style={gradientText}>Consistency</span></h1>
        </div>
      </header>

      <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', marginBottom: '32px' }}>
        <div className="stat-card" style={cardStyle} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.08)' }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(0,0,0,0.04)' }}>
          <div style={{ position: 'absolute', right: '-20px', top: '-20px', opacity: 0.03, transform: 'rotate(15deg)', color: '#000' }}><Code size={120} /></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'rgba(247, 160, 26, 0.1)', padding: '10px', borderRadius: '12px', color: 'var(--primary)' }}><Code size={24} /></div>
            <div className="label" style={{ fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.5px' }}>Problems Published</div>
          </div>
          <div className="value" style={{ fontSize: '48px', fontWeight: '800', color: '#1a1c29', lineHeight: 1 }}>{stats.total_posts}</div>
        </div>

        <div className="stat-card" style={cardStyle} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.08)' }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(0,0,0,0.04)' }}>
          <div style={{ position: 'absolute', right: '-20px', top: '-20px', opacity: 0.03, transform: 'rotate(15deg)', color: '#000' }}><Flame size={120} /></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'rgba(247, 160, 26, 0.1)', padding: '10px', borderRadius: '12px', color: 'var(--primary)' }}><Flame size={24} /></div>
            <div className="label" style={{ fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.5px' }}>Current Streak</div>
          </div>
          <div className="value" style={{ fontSize: '48px', fontWeight: '800', color: '#1a1c29', lineHeight: 1 }}>{stats.current_streak} <span style={{fontSize: '32px'}}>🔥</span></div>
        </div>

        <div className="stat-card" style={cardStyle} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.08)' }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(0,0,0,0.04)' }}>
          <div style={{ position: 'absolute', right: '-20px', top: '-20px', opacity: 0.03, transform: 'rotate(15deg)', color: '#000' }}><CalendarDays size={120} /></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'rgba(247, 160, 26, 0.1)', padding: '10px', borderRadius: '12px', color: 'var(--primary)' }}><CalendarDays size={24} /></div>
            <div className="label" style={{ fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.5px' }}>This Week</div>
          </div>
          <div className="value" style={{ fontSize: '48px', fontWeight: '800', color: '#1a1c29', lineHeight: 1 }}>{thisWeekCount}</div>
        </div>
      </div>

      <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '24px', marginBottom: '24px' }}>
        <div className="section" style={sectionStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', margin: 0, flexShrink: 0, whiteSpace: 'nowrap' }}><Activity size={20} color="var(--primary)"/> Consistency Heatmap</h2>
              <select 
                value={selectedYear} 
                onChange={(e) => setSelectedYear(e.target.value)}
                style={{ width: 'auto', minWidth: '90px', padding: '6px 12px', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.1)', background: '#fff', fontSize: '14px', fontWeight: 600, outline: 'none', cursor: 'pointer', color: '#1a1c29', flexShrink: 0 }}
              >
                {availableYears.map(yr => (
                  <option key={yr} value={yr}>{yr}</option>
                ))}
              </select>
          </div>
          <div style={{ overflowX: 'auto', paddingBottom: '10px', display: 'flex', justifyContent: 'center' }}>
            <ActivityCalendar 
              data={activityData} 
              theme={{
                  light: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'],
                  dark: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']
              }}
              colorScheme="light"
              renderBlock={(block, activity) => {
                  const tooltipText = `${activity.count} publications on ${new Date(activity.date).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'})}`;
                  return React.cloneElement(block, {
                      'data-tooltip-id': 'heatmap-tooltip',
                      'data-tooltip-content': tooltipText,
                      title: tooltipText
                  });
              }}
              labels={{
                  legend: { less: 'Less', more: 'More' },
                  months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                  totalCount: '{{count}} publications in the last year'
              }}
            />
            <ReactTooltip id="heatmap-tooltip" style={{ background: '#fff', color: '#1a1c29', border: '1px solid rgba(0,0,0,0.1)', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', padding: '8px 12px', zIndex: 9999, fontSize: '13px', fontWeight: 500 }} />
          </div>
        </div>
        
        <div className="section" style={sectionStyle}>
          <h2 style={{ marginBottom: '24px', fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}><PieChartIcon size={20} color="var(--primary)"/> Platform Breakdown</h2>
          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
            <PieChart>
                <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                >
                {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} stroke="rgba(255,255,255,0.5)" strokeWidth={2} />
                ))}
                </Pie>
                <RechartsTooltip 
                    contentStyle={{ background: '#ffffff', border: '1px solid rgba(0,0,0,0.1)', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                    itemStyle={{ color: '#1a1c29', fontWeight: 600 }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
            </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="section" style={sectionStyle}>
        <h2 style={{ marginBottom: '24px', fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}><History size={20} color="var(--primary)"/> Recent Activity</h2>
        <div className="history-list">
          {stats.recent && stats.recent.length > 0 ? (
            stats.recent.map((item, idx) => (
              <div key={idx} style={{ padding: '16px', borderBottom: '1px solid rgba(0, 0, 0, 0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', transition: 'all 0.2s ease', borderRadius: '12px', cursor: 'pointer' }} onMouseEnter={(e) => {e.currentTarget.style.background = 'rgba(0, 0, 0, 0.02)'; e.currentTarget.style.transform = 'translateX(4px)'}} onMouseLeave={(e) => {e.currentTarget.style.background = 'transparent'; e.currentTarget.style.transform = 'translateX(0)'}}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ background: 'rgba(247, 160, 26, 0.1)', color: 'var(--primary)', padding: '10px', borderRadius: '50%' }}>
                    <Code size={20} />
                  </div>
                  <div>
                      <div style={{ fontWeight: '700', fontSize: '15px', color: '#1a1c29' }}>{item.title}</div>
                      <div style={{ fontSize: '13px', color: 'var(--primary)', marginTop: '4px', fontWeight: 600 }}>Published to {item.platforms.join(', ')}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>
                    {new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                  <ChevronRight size={16} color="var(--text-muted)" />
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.02)', borderRadius: '12px' }}>
              <History size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
              <p style={{ fontWeight: 500 }}>No recent activity.</p>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>Publish your first problem to see it here!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
