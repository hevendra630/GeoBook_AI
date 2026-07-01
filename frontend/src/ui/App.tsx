import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { setAuthToken } from "../lib/api";
import { ChatPage } from "./ChatPage";
import { AuthPage } from "./AuthPage";
import { MainLayout } from "./MainLayout";
import { api } from "../lib/api";

type View = "chat" | "business";

function getStoredToken(): string | null {
  return localStorage.getItem("token");
}

setAuthToken(getStoredToken());

function AppContent() {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [view, setView] = useState<View>("chat");
  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => localStorage.getItem("chat_session_id"));
  const navigate = useNavigate();

  const [isDark, setIsDark] = useState(() => {
    return document.documentElement.classList.contains("dark");
  });

  const toggleTheme = () => {
    setIsDark(prev => {
        const next = !prev;
        if (next) {
            document.documentElement.classList.add("dark");
            localStorage.setItem("theme", "dark");
        } else {
            document.documentElement.classList.remove("dark");
            localStorage.setItem("theme", "light");
        }
        return next;
    });
  };

  useEffect(() => {
    setAuthToken(token);
    if (token) {
      localStorage.setItem("token", token);
      if (window.location.pathname === "/") {
        navigate("/chat");
      }
    } else {
      localStorage.removeItem("token");
      navigate("/");
    }
  }, [token, navigate]);

  const handleLogin = (newToken: string) => {
    setAuthToken(newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    setToken(null);
    setActiveSessionId(null);
    localStorage.removeItem("chat_session_id");
  };

  return (
    <Routes>
      <Route
        path="/"
        element={
          token ? <Navigate to="/chat" replace /> : <AuthPage onLogin={handleLogin} />
        }
      />
      <Route
        path="/chat"
        element={
          token ? (
            <MainLayout 
              onLogout={handleLogout} 
              view={view} 
              setView={setView}
              activeSessionId={activeSessionId}
              isDark={isDark}
              toggleTheme={toggleTheme}
              onSelectSession={(id: string | null) => {
                setActiveSessionId(id);
                if (id) {
                    localStorage.setItem("chat_session_id", id);
                } else {
                    localStorage.removeItem("chat_session_id");
                }
              }}
            >
              {view === "chat" ? (
                <ChatPage 
                  token={token} 
                  sessionId={activeSessionId}
                  onSessionChange={(id: string | null) => {
                    setActiveSessionId(id);
                    if (id) localStorage.setItem("chat_session_id", id);
                  }}
                />
              ) : (
                <BusinessRegister token={token} />
              )}
            </MainLayout>
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

function BusinessRegister({ token }: { token: string | null }) {
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({
    name: "Downtown Dental",
    category: "dental",
    address: "123 Main St",
    latitude: 40.7128,
    longitude: -74.006,
    phone: "+1 555-0100",
    email: "hello@downtowndental.com",
    description: "Dental clinic with appointment availability.",
    availability: [{ weekday: 1, start_time: "09:00", end_time: "17:00", slot_minutes: 30 }],
  });

  async function submit() {
    setBusy(true);
    setMsg(null);
    setError(null);
    try {
      await api.post("/api/businesses", form);
      setMsg("Business registered successfully.");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to register business");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col p-6 overflow-y-auto custom-scrollbar">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Register a Business</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">Add your business to the AI search pool.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <Field label="Business Name">
            <input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-white"
            />
          </Field>
          <Field label="Category">
            <select
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary-500/50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-white"
            >
              {["restaurant", "school", "hospital", "police", "bus_stop", "dental", "clinic", "salon"].map(
                (c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ),
              )}
            </select>
          </Field>
          <Field label="Full Address">
            <input
              value={form.address}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary-500/50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-white"
            />
          </Field>
        </div>
        <div className="space-y-4">
          <Field label="Contact Phone">
            <input
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary-500/50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-white"
            />
          </Field>
          <Field label="Business Email">
            <input
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary-500/50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-white"
            />
          </Field>
          <Field label="Latitude / Longitude">
            <div className="flex gap-2">
              <input
                type="number"
                value={form.latitude}
                onChange={(e) => setForm((f) => ({ ...f, latitude: Number(e.target.value) }))}
                className="w-1/2 rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary-500/50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-white"
              />
              <input
                type="number"
                value={form.longitude}
                onChange={(e) => setForm((f) => ({ ...f, longitude: Number(e.target.value) }))}
                className="w-1/2 rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-primary-500/50 dark:border-slate-800 dark:bg-slate-950/40 dark:text-white"
              />
            </div>
          </Field>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-800/50">
        {msg && <div className="mb-4 text-sm text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-2xl">{msg}</div>}
        {error && <div className="mb-4 text-sm text-red-400 bg-red-500/10 border border-red-500/20 p-4 rounded-2xl">{error}</div>}
        
        <button
          className="w-full md:w-auto min-w-[200px] rounded-2xl bg-primary-600 px-6 py-4 text-sm font-bold text-white shadow-glow hover:bg-primary-500 transition-all disabled:opacity-50"
          disabled={busy}
          onClick={submit}
        >
          {busy ? "Processing..." : "Complete Registration"}
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: any }) {
  return (
    <div className="space-y-2">
      <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 ml-1">{label}</div>
      {children}
    </div>
  );
}
