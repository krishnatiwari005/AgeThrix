import axios from "axios";

export type User = { id: string; name: string; email: string; email_verified: boolean };
export type TokenResponse = { access_token: string; token_type: string };
export type Agent = {
  id: string;
  name: string;
  description: string | null;
  slug: string;
  status: string;
  access_mode: string;
  model_name: string | null;
  created_at: string;
  updated_at: string;
};
export type Credential = {
  id: string;
  provider: "groq" | "huggingface";
  last4: string;
  status: string;
  last_validated_at: string | null;
};
export type BuildStatus = {
  deployment_id: string;
  status: "queued" | "awaiting_credentials" | "failed" | "active";
  stage: string;
  progress: number;
  safe_error: string | null;
  updated_at?: string;
};
export type ChatResponse = { message: string };
export type ConversationMessage = { id: string; role: "user" | "agent"; content: string; created_at: string };
export type ConversationThread = { id: string; title: string; created_at: string; updated_at: string };

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  withCredentials: true,
});

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as typeof error.config & { _retried?: boolean };
    if (error.response?.status !== 401 || original?._retried || original?.url?.includes("/auth/")) {
      return Promise.reject(error);
    }
    original._retried = true;
    refreshPromise ??= refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
    const token = await refreshPromise;
    if (!token) return Promise.reject(error);
    accessToken = token;
    original.headers.Authorization = `Bearer ${token}`;
    return api(original);
  },
);

function csrfToken() {
  return document.cookie.split("; ").find((cookie) => cookie.startsWith("csrf_token="))?.split("=")[1];
}

async function refreshAccessToken() {
  try {
    const response = await api.post<TokenResponse>("/auth/refresh", undefined, {
      headers: { "X-CSRF-Token": csrfToken() || "" },
    });
    return response.data.access_token;
  } catch {
    return null;
  }
}

export const authApi = {
  register: (name: string, email: string, password: string) =>
    api.post<TokenResponse>("/auth/register", { name, email, password }),
  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { email, password }),
  me: () => api.get<User>("/auth/me"),
  logout: () => api.post("/auth/logout", undefined, { headers: { "X-CSRF-Token": csrfToken() || "" } }),
};

export const agentsApi = {
  list: () => api.get<Agent[]>("/agents"),
  create: (payload: { name: string; description?: string; access_mode: "private" | "public" }) =>
    api.post<Agent>("/agents", payload),
  get: (id: string) => api.get<Agent>(`/agents/${id}`),
  build: (id: string, prompt: string) => api.post<BuildStatus>(`/agents/${id}/build`, { prompt }),
  resumeBuild: (id: string) => api.post<BuildStatus>(`/agents/${id}/build/resume`),
  buildStatus: (id: string) => api.get<BuildStatus>(`/agents/${id}/build-status`),
  bySlug: (slug: string) => api.get<Agent>(`/agents/by-slug/${slug}`),
  update: (id: string, payload: Partial<Pick<Agent, "name" | "description" | "access_mode">>) =>
    api.patch<Agent>(`/agents/${id}`, payload),
  remove: (id: string) => api.delete(`/agents/${id}`),
  chat: (id: string, message: string) => api.post<ChatResponse>(`/agents/${id}/chat`, { message }),
  messages: (id: string) => api.get<ConversationMessage[]>(`/agents/${id}/messages`),
  threads: (id: string) => api.get<ConversationThread[]>(`/agents/${id}/threads`),
  createThread: (id: string, clientKey?: string) => api.post<ConversationThread>(`/agents/${id}/threads`, undefined, { params: clientKey ? { client_key: clientKey } : undefined }),
  deleteThread: (id: string, threadId: string) => api.delete(`/agents/${id}/threads/${threadId}`),
  messagesForThread: (id: string, threadId: string) => api.get<ConversationMessage[]>(`/agents/${id}/messages`, { params: { thread_id: threadId } }),
  chatInThread: (id: string, threadId: string, message: string) => api.post<ChatResponse>(`/agents/${id}/chat`, { message, thread_id: threadId }),
};

export const credentialsApi = {
  get: (provider: "groq" | "huggingface") => api.get<Credential>(`/credentials/${provider}`),
  save: (provider: "groq" | "huggingface", api_key: string) =>
    api.post<Credential>(`/credentials/${provider}`, { api_key }),
  validate: (provider: "groq" | "huggingface") =>
    api.post<Credential>(`/credentials/${provider}/validate`),
  remove: (provider: "groq" | "huggingface") => api.delete(`/credentials/${provider}`),
};

export default api;
