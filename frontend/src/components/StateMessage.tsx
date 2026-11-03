export function StateMessage({ title, message, action }: { title: string; message: string; action?: React.ReactNode }) {
  return <section className="state-card"><h2>{title}</h2><p>{message}</p>{action}</section>;
}

export function ErrorMessage({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : "Something went wrong. Please try again.";
  return <StateMessage title="We hit a snag" message={message} action={onRetry && <button className="button button-secondary" onClick={onRetry}>Retry</button>} />;
}
