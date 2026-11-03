import { Link } from "react-router-dom";

export function LandingPage() {
  return <main className="marketing-page">
    <div className="landing-brand"><span className="brand-mark">A</span><span>AGETHRIX</span></div>
    <div className="hero">
      <span className="eyebrow">AGETHRIX STUDIO · BUILD · PERSONALIZE · DEPLOY</span>
      <h1>Your Ideas. Your Agents. Your Intelligence.</h1>
      <p className="hero-copy">Turn your ideas into intelligent AI agents. Describe what you need, personalize their capabilities and deploy your own AI workspace with Agethrix.</p>
      <div className="hero-actions"><Link className="button button-primary" to="/register">Build Your Agent</Link><Link className="button button-secondary" to="/login">Explore Agethrix</Link></div>
    </div>
    <div className="feature-grid"><article><strong>01</strong><h3>Agethrix Studio</h3><p>Describe your idea and build your own AI agent.</p></article><article><strong>02</strong><h3>Agethrix Cloud</h3><p>Deploy and access personal agents through unique URLs.</p></article><article><strong>03</strong><h3>Agethrix Memory</h3><p>Give agents isolated, persistent and intelligent context.</p></article><article><strong>04</strong><h3>Agethrix Hub</h3><p>Manage all your AI agents from one focused dashboard.</p></article></div>
    <footer className="marketing-footer">Agethrix — From Intent to Intelligence.</footer>
  </main>;
}
