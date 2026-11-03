import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/dashboard"><span className="brand-mark">A</span><span>AGETHRIX</span></NavLink>
        <nav className="nav-links">
          <NavLink to="/dashboard">Agents</NavLink>
          <NavLink to="/settings">Settings</NavLink>
          <button className="button button-ghost" onClick={() => { void logout(); navigate("/"); }}>Log out</button>
        </nav>
        <span className="user-chip">{user?.email}</span>
      </header>
      <Outlet />
      <footer className="app-footer">Powered by Agethrix · BUILD · PERSONALIZE · DEPLOY</footer>
    </div>
  );
}
