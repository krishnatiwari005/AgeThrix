import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router-dom";

import { ErrorMessage, StateMessage } from "../components/StateMessage";
import { renderComponent } from "../components/registry";
import { agentsApi } from "../services/api";

export function AgentWorkspace() {
  const { slug = "" } = useParams();
  const location = useLocation();
  const query = useQuery({ queryKey: ["agent", slug], queryFn: () => agentsApi.bySlug(slug).then(({ data }) => data) });
  if (query.isLoading) return <main className="workspace-page"><div className="loading-bar" /></main>;
  if (query.isError) return <main className="workspace-page"><ErrorMessage error={query.error} onRetry={() => void query.refetch()} /></main>;
  const agent = query.data!;
  return <main className="workspace-page"><div className="workspace-header"><div><Link className="back-link" to="/dashboard">← Agethrix Hub</Link><span className="eyebrow">AGETHRIX CLOUD · AGENT WORKSPACE</span><h1>{agent.name}</h1><p>{agent.description || "Your personal AI workspace."}</p></div><Link className="button button-secondary" to="/settings">Settings</Link></div><div className="workspace-grid">{renderComponent("ChatPanel", { agentId: agent.id, newVisit: location.key !== "default", visitKey: location.key })}<div className="workspace-side">{renderComponent("ModelInfo")}<StateMessage title="Agethrix Memory" message="Memory controls will appear when memory is enabled in the agent spec." /></div>{renderComponent("DocumentList")}</div></main>;
}
