import { ChatPanel } from "./workspace/ChatPanel";
import { DocumentList } from "./workspace/DocumentList";
import { ModelInfo } from "./workspace/ModelInfo";

export const componentRegistry = { ChatPanel, DocumentList, ModelInfo };
export function renderComponent(id: string, props?: { agentId?: string; newVisit?: boolean; visitKey?: string }) {
  const Component = componentRegistry[id as keyof typeof componentRegistry];
  return Component ? <Component key={id} {...props} /> : null;
}
