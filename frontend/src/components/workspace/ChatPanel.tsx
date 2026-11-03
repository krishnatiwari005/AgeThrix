import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { agentsApi, ConversationMessage, ConversationThread } from "../../services/api";

function formatInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

function AgentMessage({ text }: { text: string }) {
  return <div className="agent-message">{text.split(/\r?\n/).map((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) return <div className="message-spacer" key={index} />;
    if (/^#{1,3}\s/.test(trimmed)) {
      return <h3 key={index}>{formatInline(trimmed.replace(/^#{1,3}\s+/, ""))}</h3>;
    }
    if (/^[-*]\s/.test(trimmed)) {
      return <div className="message-list-item" key={index}>• {formatInline(trimmed.slice(2))}</div>;
    }
    return <p key={index}>{formatInline(trimmed)}</p>;
  })}</div>;
}

export function ChatPanel({ agentId, newVisit = false, visitKey = "" }: { agentId?: string; newVisit?: boolean; visitKey?: string }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "agent"; text: string }[]>([]);
  const [error, setError] = useState("");
  const [threadId, setThreadId] = useState("");
  const [creatingInitialThread, setCreatingInitialThread] = useState(false);
  const [threadError, setThreadError] = useState("");
  const initialCreationAttempted = useRef(false);
  const threads = useQuery({ queryKey: ["threads", agentId], queryFn: () => agentsApi.threads(agentId!).then(({ data }) => data), enabled: Boolean(agentId) });
  const history = useQuery({ queryKey: ["messages", agentId, threadId], queryFn: () => agentsApi.messagesForThread(agentId!, threadId).then(({ data }) => data), enabled: Boolean(agentId && threadId) });
  useEffect(() => {
    setThreadId("");
    setMessages([]);
    setThreadError("");
    setCreatingInitialThread(false);
    initialCreationAttempted.current = false;
  }, [agentId]);
  useEffect(() => {
    if (!threads.isSuccess || !agentId || threadId || creatingInitialThread || initialCreationAttempted.current) return;
    if (threads.data.length === 0) return;
    if (!newVisit || threads.data.length === 1 && threads.data[0].title === "New conversation") {
      setThreadId(threads.data[0].id);
      return;
    }
    initialCreationAttempted.current = true;
    setCreatingInitialThread(true);
    setThreadError("");
    void agentsApi.createThread(agentId, visitKey).then(({ data }) => {
      setThreadId(data.id);
      void threads.refetch();
    }).catch((reason: unknown) => {
      setThreadError(reason instanceof Error ? reason.message : "Could not create a new chat.");
    }).finally(() => setCreatingInitialThread(false));
  }, [agentId, creatingInitialThread, newVisit, threadId, threads.data, threads.isSuccess, threads.refetch]);
  useEffect(() => {
    if (history.isSuccess) setMessages(history.data.map((message: ConversationMessage) => ({ role: message.role, text: message.content })));
  }, [history.data, history.isSuccess]);
  const selectThread = (thread: ConversationThread) => {
    setThreadId(thread.id);
    setMessages([]);
    setError("");
  };
  const deleteThread = async (thread: ConversationThread) => {
    if (!agentId || !window.confirm(`Delete "${thread.title}"? This will permanently delete its messages.`)) return;
    try {
      await agentsApi.deleteThread(agentId, thread.id);
      const remaining = (await agentsApi.threads(agentId)).data;
      if (remaining.length > 0) {
        setThreadId(remaining[0].id);
        setMessages([]);
      } else {
        const replacement = (await agentsApi.createThread(agentId)).data;
        setThreadId(replacement.id);
        setMessages([]);
      }
      void threads.refetch();
    } catch (reason) {
      setThreadError(reason instanceof Error ? reason.message : "Could not delete this chat.");
    }
  };
  const newChat = async () => {
    if (!agentId) return;
    const { data } = await agentsApi.createThread(agentId);
    setThreadId(data.id);
    setMessages([]);
    void threads.refetch();
  };
  const send = async () => {
    const message = input.trim();
    if (!message || !agentId) return;
    let activeThreadId = threadId;
    if (!activeThreadId) {
      const { data } = await agentsApi.createThread(agentId);
      activeThreadId = data.id;
      setThreadId(activeThreadId);
      void threads.refetch();
    }
    setInput(""); setError(""); setMessages((items) => [...items, { role: "user", text: message }]);
    try {
      const { data } = await agentsApi.chatInThread(agentId, activeThreadId, message);
      setMessages((items) => [...items, { role: "agent", text: data.message }]);
      void threads.refetch();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The agent could not respond.");
    }
  };
  return <div className="chat-layout"><aside className="chat-sidebar"><div className="chat-sidebar-header"><div><span className="eyebrow">WORKSPACE</span><strong>Chats</strong></div><button className="button button-secondary" onClick={() => void newChat()}>+ New chat</button></div><div className="chat-thread-list">{threads.data?.map((thread) => <div className={`chat-thread-row ${thread.id === threadId ? "chat-thread-row-active" : ""}`} key={thread.id}><button className="chat-thread" onClick={() => selectThread(thread)}>{thread.title}</button><button className="chat-delete" aria-label={`Delete ${thread.title}`} title="Delete chat" onClick={() => void deleteThread(thread)}>×</button></div>)}{threads.data?.length === 0 && <p className="muted">No previous chats.</p>}</div><div className="sidebar-footer"><span className="pulse-dot" /> Agent online</div>{threadError && <p className="form-error">{threadError}</p>}</aside><section className="workspace-card chat-card"><div className="card-heading"><div><span className="eyebrow">LIVE CONVERSATION</span><h2>{threads.data?.find((thread) => thread.id === threadId)?.title || "New chat"}</h2></div><span className="status status-active">ready</span></div><div className={`chat-empty ${messages.length === 0 ? "chat-empty-state" : ""}`}>{messages.length === 0 ? <><span className="chat-orb">✦</span><p>Ask your agent a question to get started.</p><span className="chat-hint">Powered by your active runtime model</span></> : messages.map((message, index) => <div className={`chat-message chat-message-${message.role}`} key={`${message.role}-${index}`}><strong>{message.role === "user" ? "You" : "Agent"}</strong>{message.role === "agent" ? <AgentMessage text={message.text} /> : <p>{message.text}</p>}</div>)}</div>{error && <p className="form-note">{error}</p>}<div className="chat-input"><input value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void send(); }} placeholder="Ask your agent something" /><button className="button button-primary" onClick={() => void send()} disabled={!input.trim()}><span>Send</span><span className="send-arrow">↗</span></button></div></section></div>;
}
