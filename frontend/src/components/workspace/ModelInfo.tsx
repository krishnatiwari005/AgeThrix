export function ModelInfo({ modelName, status }: { modelName?: string | null; status?: string }) {
  const isReady = Boolean(modelName);
  return <section className="workspace-card model-card">
    <div className="model-card-heading">
      <div>
        <span className="eyebrow">AGETHRIX CLOUD · RUNTIME</span>
        <h2>Active model</h2>
      </div>
      <span className={`status ${isReady ? "status-active" : ""}`}>{isReady ? "live" : status || "pending"}</span>
    </div>
    <div className="model-name">{modelName || "Model pending"}</div>
    <p className="muted">{isReady ? "This is the model currently powering your agent responses." : "Complete the build to activate a model for this workspace."}</p>
    <div className="model-meta">
      <span><i className="model-dot" />Provider</span>
      <strong>Groq</strong>
    </div>
  </section>;
}
