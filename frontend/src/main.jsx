import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:10000";
const TOKEN_KEY = "leetlog_dashboard_token";

const defaultSettings = {
  linkedin_access_token: "",
  linkedin_person_urn: "",
  devto_api_key: "",
  whatsapp_number: "",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Kolkata",
  reminder_time: "09:00",
  is_whatsapp_enabled: false,
  ai_provider: "gemini",
  gemini_api_key: "",
  openai_api_key: "",
  perplexity_api_key: "",
  publish_platforms: ["devto"]
};

function normalizeSettings(settings) {
  return {
    ...defaultSettings,
    ...settings,
    linkedin_access_token: settings?.linkedin_access_token || "",
    linkedin_person_urn: settings?.linkedin_person_urn || "",
    devto_api_key: settings?.devto_api_key || "",
    whatsapp_number: settings?.whatsapp_number || "",
    gemini_api_key: settings?.gemini_api_key || "",
    openai_api_key: settings?.openai_api_key || "",
    perplexity_api_key: settings?.perplexity_api_key || "",
    publish_platforms: settings?.publish_platforms?.length ? settings.publish_platforms : ["devto"]
  };
}

async function api(path, options = {}, token) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || "Request failed.");
  }
  return data;
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [settings, setSettings] = useState(defaultSettings);
  const [connected, setConnected] = useState({});
  const [mode, setMode] = useState("login");
  const [authForm, setAuthForm] = useState({ name: "", email: "", password: "" });
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  const completion = useMemo(() => {
    const checks = [
      connected.ai_provider,
      connected.devto,
      connected.linkedin,
      connected.whatsapp
    ];
    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
  }, [connected]);

  useEffect(() => {
    if (!token) return;

    Promise.all([
      api("/auth/me", {}, token),
      api("/settings/integrations", {}, token)
    ])
      .then(([profile, integrationSettings]) => {
        setUser(profile);
        setSettings(normalizeSettings(integrationSettings));
        setConnected(integrationSettings.connected || {});
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      });
  }, [token]);

  async function submitAuth(event) {
    event.preventDefault();
    setIsBusy(true);
    setError("");
    setNotice("");

    try {
      const path = mode === "register" ? "/auth/register" : "/auth/login";
      const payload = mode === "register"
        ? authForm
        : { email: authForm.email, password: authForm.password };
      const data = await api(path, { method: "POST", body: JSON.stringify(payload) });
      localStorage.setItem(TOKEN_KEY, data.token);
      setToken(data.token);
      setUser(data.user);
      setNotice("Welcome to your dashboard.");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsBusy(false);
    }
  }

  async function saveSettings(event) {
    event.preventDefault();
    setIsBusy(true);
    setError("");
    setNotice("");

    try {
      const payload = {
        ...settings,
        linkedin_access_token: settings.linkedin_access_token || null,
        linkedin_person_urn: settings.linkedin_person_urn || null,
        devto_api_key: settings.devto_api_key || null,
        whatsapp_number: settings.whatsapp_number || null,
        gemini_api_key: settings.gemini_api_key || null,
        openai_api_key: settings.openai_api_key || null,
        perplexity_api_key: settings.perplexity_api_key || null
      };
      const data = await api(
        "/settings/integrations",
        { method: "PUT", body: JSON.stringify(payload) },
        token
      );
      setSettings(normalizeSettings(data));
      setConnected(data.connected || {});
      setNotice("Settings saved.");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsBusy(false);
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setSettings(defaultSettings);
    setConnected({});
    setNotice("");
    setError("");
  }

  if (!token || !user) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <div className="brand-mark">LL</div>
          <h1>LeetLog AI</h1>
          <p className="muted">Create an account to manage publishing, reminders, and social integrations from one place.</p>

          <div className="segmented" role="tablist" aria-label="Authentication mode">
            <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">Log in</button>
            <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">Create account</button>
          </div>

          <form onSubmit={submitAuth} className="stack">
            {mode === "register" && (
              <label>
                Name
                <input value={authForm.name} onChange={(event) => setAuthForm({ ...authForm, name: event.target.value })} placeholder="Ada Lovelace" />
              </label>
            )}
            <label>
              Email
              <input type="email" required value={authForm.email} onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })} placeholder="you@example.com" />
            </label>
            <label>
              Password
              <input type="password" required minLength={8} value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} placeholder="At least 8 characters" />
            </label>
            {error && <p className="alert error">{error}</p>}
            {notice && <p className="alert success">{notice}</p>}
            <button className="primary" disabled={isBusy}>{isBusy ? "Working..." : mode === "register" ? "Create account" : "Log in"}</button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">LL</div>
          <div>
            <strong>LeetLog AI</strong>
            <span>Onboarding</span>
          </div>
        </div>
        <nav>
          <a className="active" href="#settings">Settings</a>
          <a href="#publishing">Publishing</a>
          <a href="#reminders">Reminders</a>
        </nav>
        <button className="ghost" onClick={logout}>Log out</button>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Workspace</p>
            <h1>Settings and integrations</h1>
          </div>
          <div className="profile-pill">{user.name}</div>
        </header>

        <section className="status-band">
          <div>
            <p className="eyebrow">Onboarding progress</p>
            <h2>{completion}% connected</h2>
          </div>
          <div className="meter" aria-label={`${completion}% connected`}>
            <span style={{ width: `${completion}%` }} />
          </div>
        </section>

        <form id="settings" onSubmit={saveSettings} className="settings-grid">
          <IntegrationCard title="AI Provider" connected={connected.ai_provider}>
            <label>
              Provider
              <select value={settings.ai_provider} onChange={(event) => setSettings({ ...settings, ai_provider: event.target.value })}>
                <option value="gemini">Gemini</option>
                <option value="openai">OpenAI</option>
                <option value="perplexity">Perplexity</option>
              </select>
            </label>
            <label>
              Gemini API key
              <input type="password" value={settings.gemini_api_key} onChange={(event) => setSettings({ ...settings, gemini_api_key: event.target.value })} />
            </label>
            <label>
              OpenAI API key
              <input type="password" value={settings.openai_api_key} onChange={(event) => setSettings({ ...settings, openai_api_key: event.target.value })} />
            </label>
            <label>
              Perplexity API key
              <input type="password" value={settings.perplexity_api_key} onChange={(event) => setSettings({ ...settings, perplexity_api_key: event.target.value })} />
            </label>
          </IntegrationCard>

          <IntegrationCard title="Publishing" connected={connected.devto}>
            <label>
              Dev.to API key
              <input type="password" value={settings.devto_api_key} onChange={(event) => setSettings({ ...settings, devto_api_key: event.target.value })} />
            </label>
            <fieldset>
              <legend>Default targets</legend>
              {["devto", "hashnode", "medium", "webhook"].map((platform) => (
                <label className="check-row" key={platform}>
                  <input
                    type="checkbox"
                    checked={settings.publish_platforms.includes(platform)}
                    onChange={(event) => {
                      const next = event.target.checked
                        ? [...settings.publish_platforms, platform]
                        : settings.publish_platforms.filter((item) => item !== platform);
                      setSettings({ ...settings, publish_platforms: next.length ? next : ["devto"] });
                    }}
                  />
                  {platform}
                </label>
              ))}
            </fieldset>
          </IntegrationCard>

          <IntegrationCard title="LinkedIn" connected={connected.linkedin}>
            <label>
              Access token
              <input type="password" value={settings.linkedin_access_token} onChange={(event) => setSettings({ ...settings, linkedin_access_token: event.target.value })} />
            </label>
            <label>
              Person URN
              <input value={settings.linkedin_person_urn} onChange={(event) => setSettings({ ...settings, linkedin_person_urn: event.target.value })} placeholder="urn:li:person:123456" />
            </label>
          </IntegrationCard>

          <IntegrationCard title="WhatsApp Reminder" connected={connected.whatsapp}>
            <label className="toggle-row">
              <input type="checkbox" checked={settings.is_whatsapp_enabled} onChange={(event) => setSettings({ ...settings, is_whatsapp_enabled: event.target.checked })} />
              Enable reminders
            </label>
            <label>
              WhatsApp number
              <input value={settings.whatsapp_number} onChange={(event) => setSettings({ ...settings, whatsapp_number: event.target.value })} placeholder="+911234567890" />
            </label>
            <label>
              Reminder time
              <input type="time" value={settings.reminder_time} onChange={(event) => setSettings({ ...settings, reminder_time: event.target.value })} />
            </label>
            <label>
              Timezone
              <input value={settings.timezone} onChange={(event) => setSettings({ ...settings, timezone: event.target.value })} />
            </label>
          </IntegrationCard>

          <div className="save-row">
            {error && <p className="alert error">{error}</p>}
            {notice && <p className="alert success">{notice}</p>}
            <button className="primary" disabled={isBusy}>{isBusy ? "Saving..." : "Save settings"}</button>
          </div>
        </form>
      </section>
    </main>
  );
}

function IntegrationCard({ title, connected, children }) {
  return (
    <section className="integration-card">
      <header>
        <h2>{title}</h2>
        <span className={connected ? "badge connected" : "badge"}>{connected ? "Connected" : "Needs setup"}</span>
      </header>
      <div className="stack">{children}</div>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
