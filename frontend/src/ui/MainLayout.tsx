import { ReactNode, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  PlusCircle,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Bot,
  Search,
  History,
  Building2,
  MessageCircle,
  Sun,
  Moon,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

interface ChatSessionMeta {
  id: string;
  title: string;
  updated_at: string;
}

interface MainLayoutProps {
  children: ReactNode;
  onLogout: () => void;
  view: "chat" | "business";
  setView: (v: "chat" | "business") => void;
  activeSessionId: string | null;
  onSelectSession: (id: string | null) => void;
  isDark: boolean;
  toggleTheme: () => void;
}

export function MainLayout({ children, onLogout, view, setView, activeSessionId, onSelectSession, isDark, toggleTheme }: MainLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [sessions, setSessions] = useState<ChatSessionMeta[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    
    api.get<ChatSessionMeta[]>("/api/chat/sessions")
      .then(res => setSessions(res.data))
      .catch(err => console.error("Could not fetch sessions", err));
  }, [activeSessionId]);

  const handleLogout = () => {
    onLogout();
    navigate("/");
  };

  return (
    <div className="flex h-screen w-full bg-slate-50 text-slate-800 dark:bg-slate-950 dark:text-slate-100 overflow-hidden font-['Outfit'] transition-colors">
      {}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 80 : 280 }}
        className="relative z-20 flex flex-col border-r border-slate-200 bg-white/60 dark:border-slate-800/50 dark:bg-slate-900/30 backdrop-blur-xl transition-all"
      >
        {}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-10 z-30 flex h-6 w-6 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors shadow-sm"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>

        {}
        <div className={`flex items-center justify-between p-6 ${collapsed ? "flex-col gap-4" : "gap-3"}`}>
          <div className="flex items-center gap-3 w-full">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-600 shadow-glow p-2">
              <img src="/logo.svg" alt="GeoBook AI Logo" className="w-full h-full object-contain dark:invert" />
            </div>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="font-bold text-xl tracking-tight"
              >
                Geobook AI
              </motion.div>
            )}
          </div>
          
          <button 
            onClick={toggleTheme} 
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>

        {}
        <nav className="flex-1 space-y-1 px-4 overflow-y-auto custom-scrollbar">
          {!collapsed && <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2 ml-2">Main Menu</div>}
          
          <NavItem
            icon={<MessageSquare size={20} />}
            label="Chat Assistant"
            active={view === "chat" && !activeSessionId}
            onClick={() => { setView("chat"); onSelectSession(null); }}
            collapsed={collapsed}
          />
          <NavItem
            icon={<Building2 size={20} />}
            label="Business Portal"
            active={view === "business"}
            onClick={() => setView("business")}
            collapsed={collapsed}
          />

          {!collapsed && (
            <>
              <div className="flex items-center justify-between mt-6 mb-2 ml-2 pr-2">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Previous Chats</div>
              </div>
              <div className="space-y-1">
                {sessions.length === 0 ? (
                  <div className="px-3 py-2 text-xs text-slate-500">
                    Your chat history will appear here.
                  </div>
                ) : (
                  sessions.map(s => (
                    <NavItem
                      key={s.id}
                      icon={<MessageCircle size={18} />}
                      label={s.title || "New Chat"}
                      active={view === "chat" && activeSessionId === s.id}
                      onClick={() => { setView("chat"); onSelectSession(s.id); }}
                      collapsed={collapsed}
                      className="!text-xs !py-2.5"
                    />
                  ))
                )}
              </div>
            </>
          )}
        </nav>

        {}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800/50">

          <NavItem
            icon={<LogOut size={20} />}
            label="Logout"
            active={false}
            onClick={handleLogout}
            collapsed={collapsed}
            className="text-red-500 hover:bg-red-50 hover:text-red-600 dark:text-red-400 dark:hover:bg-red-500/10 dark:hover:text-red-300"
          />
        </div>
      </motion.aside>

      {}
      <main className="relative flex-1 overflow-hidden transition-colors">
        {}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
          <div className="absolute -top-[10%] -right-[10%] w-[50%] h-[50%] bg-primary-600/5 dark:bg-primary-600/10 rounded-full blur-[120px]" />
          <div className="absolute -bottom-[10%] -left-[10%] w-[50%] h-[50%] bg-indigo-600/5 dark:bg-indigo-600/10 rounded-full blur-[120px]" />
        </div>

        {}
        <div className="relative z-10 flex h-full flex-col p-4 md:p-6 lg:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={view}
              initial={{ opacity: 0, y: 10, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.99 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="h-full rounded-3xl border border-slate-200 bg-white/70 dark:border-slate-800/50 dark:bg-slate-900/40 shadow-xl dark:shadow-2xl backdrop-blur-md overflow-hidden transition-colors"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

interface NavItemProps {
  icon: ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  collapsed: boolean;
  className?: string;
}

function NavItem({ icon, label, active, onClick, collapsed, className = "" }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={`group flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition-all ${
        active 
          ? "bg-primary-600 text-white shadow-glow" 
          : "text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-200"
      } ${collapsed ? "justify-center" : ""} ${className}`}
    >
      <div className="shrink-0 transition-transform group-hover:scale-110">{icon}</div>
      {!collapsed && <span>{label}</span>}
      {active && !collapsed && (
        <motion.div layoutId="active-nav" className="ml-auto h-1.5 w-1.5 rounded-full bg-white" />
      )}
    </button>
  );
}
