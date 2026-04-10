import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LogIn, UserPlus, Mail, Lock, ArrowRight, Loader2, Bot } from "lucide-react";
import { api, setAuthToken } from "../lib/api";

export function AuthPage({ onLogin }: { onLogin: (token: string) => void }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("password123");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);

    try {
      if (isLogin) {
        const form = new URLSearchParams();
        form.set("username", email);
        form.set("password", password);
        const res = await api.post("/api/auth/login", form, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
        const token = res.data.access_token;
        setAuthToken(token);
        onLogin(token);
      } else {
        await api.post("/api/auth/register", { email, password });
        setIsLogin(true);
        setError("Registration successful! Please log in.");
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? (isLogin ? "Login failed" : "Registration failed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4 transition-colors">
      {}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary-600/10 dark:bg-primary-600/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 dark:bg-indigo-600/20 rounded-full blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="mb-8 text-center">
          <div className="flex flex-col items-center gap-4 mb-4">
            <div className="inline-flex h-20 w-20 items-center justify-center rounded-2xl bg-white shadow-[0_4px_24px_rgba(0,0,0,0.05)] dark:bg-white/5 p-2 dark:shadow-glow border border-slate-200 dark:border-white/10 overflow-hidden">
              <img src="/logo.svg" alt="GeoBook AI Logo" className="w-full h-full object-contain dark:invert" />
            </div>
            <div className="text-center">
              <h1 className="text-4xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-500 dark:from-white dark:to-slate-400">GeoBook AI</h1>
              <p className="mt-2 text-slate-500 dark:text-slate-400 font-medium tracking-wide italic">Intelligent Place Discovery & Booking</p>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white/80 dark:border-slate-800 dark:bg-slate-900/50 p-8 shadow-xl dark:shadow-2xl backdrop-blur-xl">
          <div className="flex bg-slate-100 dark:bg-slate-950/50 p-1 rounded-2xl mb-8 border border-slate-200 dark:border-slate-800">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isLogin ? "bg-white text-slate-900 shadow-sm dark:bg-primary-600 dark:text-white dark:shadow-glow" : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <LogIn size={16} /> Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all ${
                !isLogin ? "bg-white text-slate-900 shadow-sm dark:bg-primary-600 dark:text-white dark:shadow-glow" : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <UserPlus size={16} /> Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <AnimatePresence mode="wait">
              <motion.div
                key={isLogin ? "login" : "register"}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
              >
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300 ml-1">Email address</label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" size={18} />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="name@example.com"
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3.5 pl-12 pr-4 text-slate-900 outline-none transition-all focus:border-primary-500/50 focus:ring-2 focus:ring-primary-500/20 dark:border-slate-800 dark:bg-slate-950/50 dark:text-white dark:ring-primary-600"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300 ml-1">Password</label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" size={18} />
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3.5 pl-12 pr-4 text-slate-900 outline-none transition-all focus:border-primary-500/50 focus:ring-2 focus:ring-primary-500/20 dark:border-slate-800 dark:bg-slate-950/50 dark:text-white dark:ring-primary-600"
                        required
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`text-sm p-4 rounded-2xl border ${
                  error.includes("successful")
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                    : "bg-red-500/10 border-red-500/20 text-red-400"
                }`}
              >
                {error}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="group relative w-full overflow-hidden rounded-2xl bg-primary-600 py-3.5 font-bold text-white shadow-glow transition-all hover:bg-primary-500 active:scale-[0.98] disabled:opacity-70"
            >
              <div className="flex items-center justify-center gap-2">
                {busy ? (
                  <Loader2 className="animate-spin" size={20} />
                ) : (
                  <>
                    {isLogin ? "Sign In" : "Create Account"}
                    <ArrowRight className="transition-transform group-hover:translate-x-1" size={18} />
                  </>
                )}
              </div>
            </button>
          </form>
        </div>

        <p className="mt-8 text-center text-sm text-slate-500">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </motion.div>
    </div>
  );
}
