import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, 
  MapPin, 
  Navigation, 
  Star, 
  Phone, 
  ExternalLink, 
  Info, 
  CheckCircle2, 
  Loader2,
  Search,
  Calendar,
  Clock
} from "lucide-react";
import { api } from "../lib/api";
import { getBrowserLocation } from "../lib/geolocation";
import type { ChatResponse, ClientLocation, PlaceResult } from "../lib/types";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
  ts: number;
  payload?: ChatResponse;
};

function formatDistance(meters?: number | null) {
  if (meters == null) return "";
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
}

function osmEmbedUrl(lat: number, lon: number) {
  return `https://www.openstreetmap.org/export/embed.html?marker=${lat},${lon}&layer=mapnik&zoom=14`;
}

export function ChatPage({ token, sessionId, onSessionChange }: { token: string | null; sessionId: string | null; onSessionChange: (id: string | null) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      role: "assistant",
      text: "How can I help you today? I can find nearby hospitals, restaurants, schools, and more. Try asking 'Find the nearest dentist' or 'Book a dental appointment tomorrow at 10am'.",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [clientLocation, setClientLocation] = useState<ClientLocation | null>(null);
  const [selected, setSelected] = useState<PlaceResult | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    getBrowserLocation().then(setClientLocation);
  }, []);

  useEffect(() => {
    if (sessionId) {
      
      api.get(`/api/chat/sessions/${sessionId}`)
        .then(res => {
            if (res.data.messages && res.data.messages.length > 0) {
                setMessages(res.data.messages);
            } else {
                setMessages([{ role: "assistant", text: "How can I help you today? I can find nearby hospitals, restaurants, schools, and more.", ts: Date.now() }]);
            }
        })
        .catch(err => {
            console.error("Failed to load session history", err);
            onSessionChange(null);
            setMessages([{ role: "assistant", text: "Welcome back! Start typing to start a new chat.", ts: Date.now() }]);
        });
    } else {
        setMessages([{ role: "assistant", text: "How can I help you today? I can find nearby hospitals, restaurants, schools, and more.", ts: Date.now() }]);
    }
    
  }, [sessionId]);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages.length]);

  const lastAssistant = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant")?.payload,
    [messages],
  );

  async function send() {
    if (!input.trim() || busy) return;
    
    const userMsg = input.trim();
    setSelected(null);
    setMessages((m) => [...m, { role: "user", text: userMsg, ts: Date.now() }]);
    setInput("");

    setBusy(true);
    try {
      let currentLoc = clientLocation;
      if (!currentLoc) {
        currentLoc = await getBrowserLocation();
        if (currentLoc) setClientLocation(currentLoc);
      }

      const res = await api.post<ChatResponse>("/api/chat", {
        message: userMsg,
        client_location: currentLoc,
        session_id: sessionId,
      });

      if (res.data.session_id && res.data.session_id !== sessionId) {
        onSessionChange(res.data.session_id);
      }

      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: res.data.assistant_message,
          ts: Date.now(),
          payload: res.data,
        },
      ]);
      
      if (res.data.results?.length) {
        setSelected(res.data.results[0]);
      }
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: e?.response?.data?.detail ?? "Something went wrong. Please try again.",
          ts: Date.now(),
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full w-full">
      {}
      <section className="flex flex-1 flex-col border-r border-slate-200 dark:border-slate-800/50 min-w-0">
        <header className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800/50 p-4">
          <div className="flex items-center gap-3">
            <div className={`h-2.5 w-2.5 rounded-full ${clientLocation ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "bg-slate-300 dark:bg-slate-600"}`} />
            <div className="text-sm font-medium text-slate-600 dark:text-slate-200">
              {clientLocation ? "Location active" : "Detecting location..."}
            </div>
          </div>
          <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">
            Chat Session
          </div>
        </header>

        <div ref={listRef} className="flex-1 space-y-6 overflow-y-auto p-6 custom-scrollbar">
          <AnimatePresence initial={false}>
            {messages.map((m, idx) => (
              <motion.div
                key={m.ts + idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className={`max-w-[85%] rounded-2xl flex flex-col ${
                  m.role === "user" 
                    ? "bg-primary-600 text-white shadow-glow px-5 py-3.5" 
                    : "bg-white text-slate-800 border border-slate-200 dark:bg-slate-800/50 dark:text-slate-100 dark:border-slate-700/50 px-5 py-3.5 shadow-sm dark:shadow-none"
                }`}>
                  <span className="text-[15px] leading-relaxed whitespace-pre-wrap">{m.text}</span>
                  
                  {m.role === "assistant" && m.payload?.booking && (
                    <div className="mt-4 border-t border-emerald-500/20 pt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle2 size={18} className="text-emerald-400" />
                        <span className="text-sm font-bold text-emerald-400 uppercase tracking-wide">Booking Confirmed</span>
                      </div>
                      <div className="space-y-1.5 rounded-xl bg-emerald-500/5 border border-emerald-500/10 p-3">
                        <div className="flex items-center gap-2 text-xs text-emerald-100/80">
                          <Clock size={14} />
                          <span>{new Date(m.payload.booking.start_at).toLocaleString()}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-emerald-100/80">
                          <MapPin size={14} />
                          <span>Appointment ID: {m.payload.booking.appointment_id}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {busy && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="bg-white text-slate-800 border border-slate-200 dark:bg-slate-800/50 dark:border-slate-700/50 px-5 py-3.5 rounded-2xl shadow-sm dark:shadow-none">
                <Loader2 size={18} className="animate-spin text-primary-500 dark:text-primary-400" />
              </div>
            </motion.div>
          )}
        </div>

        <div className="p-4 border-t border-slate-200 bg-slate-50/50 dark:border-slate-800/50 dark:bg-slate-900/20">
          <div className="relative flex items-center">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              placeholder="Ask anything..."
              className="w-full rounded-2xl border border-slate-300 bg-white py-4 pl-5 pr-14 text-[15px] text-slate-900 outline-none ring-primary-500/30 transition-all focus:border-primary-500/50 focus:ring-4 dark:border-slate-700/50 dark:bg-slate-950/50 dark:text-white"
              disabled={busy}
            />
            <button
              onClick={send}
              disabled={busy || !input.trim()}
              className="absolute right-2 flex h-10 w-10 items-center justify-center rounded-xl bg-primary-600 text-white shadow-glow transition-all hover:bg-primary-500 active:scale-95 disabled:opacity-50 disabled:shadow-none"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </section>

      {}
      <aside className="hidden w-96 flex-col overflow-hidden lg:flex xl:w-[440px]">
        {}
        <div className="border-b border-slate-200 dark:border-slate-800/50 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Navigation size={18} className="text-primary-500 dark:text-primary-400" />
            <h3 className="text-sm font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">Map View</h3>
          </div>
          <div className="relative h-60 w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 ring-1 ring-black/5 dark:border-slate-800 dark:bg-slate-950 dark:ring-white/5 shadow-inner">
            {selected ? (
              <iframe
                title="Map Preview"
                className="h-full w-full"
                src={selected.latitude != null && selected.longitude != null 
                  ? osmEmbedUrl(selected.latitude, selected.longitude)
                  : `https://www.google.com/maps?q=${encodeURIComponent(selected.maps_url ?? "")}&output=embed`
                }
                loading="lazy"
              />
            ) : (
              <div className="flex h-full flex-col items-center justify-center p-6 text-center">
                <div className="mb-3 rounded-full bg-slate-200 p-3 ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/5">
                  <MapPin size={24} className="text-slate-500 dark:text-slate-600" />
                </div>
                <p className="text-xs font-medium text-slate-500">Select a location from results to view on map</p>
              </div>
            )}
          </div>
          {selected && (
            <a 
              href={selected.maps_url ?? "#"} 
              target="_blank" 
              rel="noreferrer"
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50 dark:text-white dark:hover:bg-slate-700 transition-colors shadow-sm"
            >
              <ExternalLink size={14} /> Open in Google Maps
            </a>
          )}
        </div>

        {}
        <div className="flex flex-1 flex-col overflow-hidden p-6 pt-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Search size={18} className="text-primary-500 dark:text-primary-400" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">Local Results</h3>
            </div>
            {lastAssistant?.results && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
                {lastAssistant.results.length} found
              </span>
            )}
          </div>
          
          <div className="flex-1 space-y-3 overflow-y-auto pr-1 custom-scrollbar">
            {lastAssistant?.results?.map((r, i) => (
              <button
                key={`${i}-${r.name}`}
                onClick={() => setSelected(r)}
                className={`group relative w-full overflow-hidden rounded-2xl border p-4 text-left transition-all ${
                  selected?.name === r.name 
                    ? "border-primary-500/50 bg-primary-500/5 shadow-glow" 
                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800/50 dark:bg-slate-900/20 dark:hover:border-slate-700 dark:hover:bg-white/5"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="font-bold text-sm text-slate-800 group-hover:text-slate-900 dark:text-slate-100 dark:group-hover:text-white transition-colors">{r.name}</div>
                  <div className="shrink-0 text-[11px] font-bold text-primary-500 dark:text-primary-400 uppercase">{formatDistance(r.distance_meters)}</div>
                </div>
                <p className="mt-1.5 text-xs text-slate-500 line-clamp-1">{r.address}</p>
                
                <div className="mt-3 flex flex-wrap gap-2">
                  {r.rating && (
                    <div className="flex items-center gap-1 rounded-lg bg-yellow-500/10 px-2 py-0.5 text-[10px] font-bold text-yellow-500 border border-yellow-500/20">
                      <Star size={10} fill="currentColor" /> {r.rating}
                    </div>
                  )}
                  {r.phone && (
                    <div className="flex items-center gap-1 rounded-lg bg-primary-500/10 px-2 py-0.5 text-[10px] font-bold text-primary-400 border border-primary-500/20">
                      <Phone size={10} /> Contact
                    </div>
                  )}
                  {r.business_id && (
                    <div className="flex items-center gap-1 rounded-lg bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                      <Calendar size={10} /> Bookable
                    </div>
                  )}
                </div>
              </button>
            ))}
            
            {(!lastAssistant?.results || lastAssistant.results.length === 0) && (
              <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-50/50 rounded-3xl border border-dashed border-slate-300 dark:bg-slate-950/20 dark:border-slate-800">
                <Info size={24} className="mb-2 text-slate-400 dark:text-slate-700" />
                <p className="text-xs text-slate-500">Your search results will appear here</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
