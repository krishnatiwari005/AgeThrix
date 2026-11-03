import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const isLogin = mode === "login";
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await (isLogin ? login(email, password) : register(name, email, password)); navigate((location.state as { from?: string } | null)?.from || "/dashboard"); }
    catch { setError(isLogin ? "Invalid email or password." : "Unable to create your account."); }
    finally { setBusy(false); }
  }
  return <main className="auth-page"><div className="auth-card"><Link className="brand" to="/"><span className="brand-mark">A</span><span>AGETHRIX</span></Link><p className="brand-tagline">From Intent to Intelligence.</p><h1>{isLogin ? "Welcome back" : "Create your account"}</h1><p className="muted">{isLogin ? "Continue building your personal AI workspace." : "Start with a secure workspace for your agents."}</p><form onSubmit={submit}>{!isLogin && <label>Your name<input type="text" value={name} onChange={(event) => setName(event.target.value)} required maxLength={120} autoComplete="name" /></label>}<label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} autoComplete={isLogin ? "current-password" : "new-password"} /></label>{error && <p className="form-error">{error}</p>}<button className="button button-primary button-wide" disabled={busy}>{busy ? "Working…" : isLogin ? "Log in" : "Create account"}</button></form><p className="auth-switch">{isLogin ? "New here?" : "Already have an account?"} <Link to={isLogin ? "/register" : "/login"}>{isLogin ? "Create an account" : "Log in"}</Link></p></div></main>;
}
