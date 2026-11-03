import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ErrorMessage, StateMessage } from "../components/StateMessage";
import { agentsApi, type Agent } from "../services/api";

function statusClass(status: string) { return `status status-${status}`; }
export function AgentsPage() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["agents"], queryFn: () => agentsApi.list().then(({ data }) => data) });
  const remove = useMutation({ mutationFn: (id: string) => agentsApi.remove(id), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }) });
  if (query.isLoading) return <main className="page"><div className="loading-bar" /></main>;
  if (query.isError) return <main className="page"><ErrorMessage error={query.error} onRetry={() => void query.refetch()} /></main>;
  const agents = query.data || [];
  return <main className="page"><div className="page-heading"><div><span className="eyebrow">AGETHRIX HUB</span><h1>Your agents</h1><p className="muted">Build focused AI collaborators for the work you care about.</p></div><Link className="button button-primary" to="/agents/new">+ Build Your Agent</Link></div>{agents.length === 0 ? <StateMessage title="Your first agent starts here" message="Describe the assistant you have in mind and Agethrix Studio will turn the idea into a workspace." action={<Link className="button button-primary" to="/agents/new">Create your first agent</Link>} /> : <div className="agent-grid">{agents.map((agent: Agent) => <article className="agent-card" key={agent.id}><div className="card-top"><span className={statusClass(agent.status)}>{agent.status.replace("_", " ")}</span><button className="icon-button" aria-label={`Delete ${agent.name}`} onClick={() => window.confirm(`Delete ${agent.name}?`) && remove.mutate(agent.id)}>×</button></div><h2>{agent.name}</h2><p>{agent.description || "No description yet."}</p><div className="agent-meta"><span>/{agent.slug}</span><span>{agent.access_mode}</span></div><div className="card-actions">{agent.status === "active" ? <Link className="button button-primary" to={`/agent/${agent.slug}`}>Open workspace</Link> : <Link className="button button-secondary" to={`/agents/${agent.id}/build`}>View build</Link>}</div></article>)}</div>}</main>;
}
