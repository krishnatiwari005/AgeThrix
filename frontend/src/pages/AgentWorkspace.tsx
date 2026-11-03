import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router-dom";

import { ErrorMessage, StateMessage } from "../components/StateMessage";
import { renderComponent } from "../components/registry";
import { agentsApi } from "../services/api";

export function AgentWorkspace() {
  const { slug = "" } = useParams();
  const location = useLocation();
  const [focusMode, setFocusMode] = useState(false);
  const query = useQuery({ queryKey: ["agent", slug], queryFn: () => agentsApi.bySlug(slug).then(({ data }) => data) });
  if (query.isLoading) return <main className="workspace-page"><div className="loading-bar" /></main>;
  if (query.isError) return <main className="workspace-page"><ErrorMessage error={query.error} onRetry={() => void query.refetch()} /></main>;
  const agent = query.data!;
  return <main className={`workspace-page ${focusMode ? "focus-mode" : ""}`}><div className="workspace-header"><div><Link className="back-link" to="/dashboard">← Agethrix Hub</Link><div className="workspace-kicker"><span className="agent-avatar">✦</span><span className="eyebrow">AGETHRIX CLOUD · AGENT WORKSPACE</span><span className="status status-active">{agent.status}</span></div><h1>{agent.name}</h1><p>{agent.description || "Your personal AI workspace."}</p></div><div className="workspace-actions"><button className="button button-secondary" onClick={() => setFocusMode((enabled) => !enabled)}>{focusMode ? "Show console" : "Focus chat"}</button><Link className="button button-secondary" to="/settings">Settings</Link></div></div><div className="workspace-grid">{renderComponent("ChatPanel", { agentId: agent.id, newVisit: location.key !== "default", visitKey: location.key })}<div className="workspace-side">{renderComponent("ModelInfo", { modelName: agent.model_name, status: agent.status })}<StateMessage title="Agethrix Memory" message="Memory controls will appear when memory is enabled in the agent spec." /></div>{renderComponent("DocumentList")}</div></main>;
}
