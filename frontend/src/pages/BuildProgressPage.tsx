import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { ErrorMessage, StateMessage } from "../components/StateMessage";
import { agentsApi } from "../services/api";

const stages = ["understanding", "designing", "configuring_models", "installing_capabilities", "activating"];
export function BuildProgressPage() {
  const { agentId = "" } = useParams();
  const query = useQuery({ queryKey: ["build", agentId], queryFn: () => agentsApi.buildStatus(agentId).then(({ data }) => data), refetchInterval: (data) => data.state.data?.status === "active" || data.state.data?.status === "failed" || data.state.data?.status === "awaiting_credentials" ? false : 2000 });
  const resume = useMutation({ mutationFn: () => agentsApi.resumeBuild(agentId), onSuccess: () => void query.refetch() });
  if (query.isLoading) return <main className="page"><div className="loading-bar" /></main>;
  if (query.isError) return <main className="page"><ErrorMessage error={query.error} onRetry={() => void query.refetch()} /></main>;
  const build = query.data!;
  const activeStage = stages.indexOf(build.stage);
  return <main className="page narrow-page"><Link className="back-link" to="/dashboard">← Back to Agethrix Hub</Link><div className="build-hero"><span className="eyebrow">AGETHRIX CLOUD · AGENT BUILD</span><h1>{build.status === "active" ? "Your workspace is ready" : build.status === "awaiting_credentials" ? "One credential is needed" : build.status === "failed" ? "The build needs attention" : "Creating your workspace"}</h1><p className="muted">{build.status === "awaiting_credentials" ? "Add the required provider credential, then resume this build." : build.safe_error || "Agethrix Studio is configuring your agent and checking each capability."}</p></div><div className="panel progress-panel"><div className="progress-track"><span style={{ width: `${build.progress}%` }} /></div><div className="stage-list">{stages.map((stage, index) => <div className={`stage ${index <= activeStage && build.status !== "failed" ? "stage-done" : ""}`} key={stage}><span className="stage-dot">{index <= activeStage ? "✓" : index + 1}</span><span>{stage.replaceAll("_", " ")}</span></div>)}</div></div>{build.status === "awaiting_credentials" && <StateMessage title="Connect your Groq key" message="Your key is encrypted and never shown again. Open Settings to add it, then return here to resume." action={<span className="hero-actions"><Link className="button button-secondary" to="/settings">Open settings</Link><button className="button button-primary" onClick={() => resume.mutate()} disabled={resume.isPending}>{resume.isPending ? "Resuming…" : "Resume build"}</button></span>} />}{build.status === "active" && <StateMessage title="Ready to explore" message="Your agent has passed its initial setup." action={<Link className="button button-primary" to="/dashboard">Go to Agethrix Hub</Link>} />}</main>;
}
