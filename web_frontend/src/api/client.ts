export type ChatStep = {
  id: string;
  message_id: string;
  step_index: number;
  step_type: string;
  title: string;
  status: 'running' | 'completed' | 'failed';
  summary: string;
  mcp_name?: string | null;
  mcp_input?: string | null;
  mcp_output?: string | null;
  llm_output?: string;
  error?: string | null;
  duration_ms?: number | null;
  created_at: string;
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  selected_skill?: string | null;
  web_search_enabled: boolean;
  trace_open: boolean;
  created_at: string;
  steps?: ChatStep[];
  stream_base?: string;
  stream_text?: string;
  answer_started?: boolean;
  is_streaming?: boolean;
};

export type ChatSession = {
  id: string;
  title: string;
  summary: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  last_mode?: string | null;
  last_web_search_enabled: boolean;
  messages?: ChatMessage[];
};

export type ChatStreamEvent =
  | 'message_created'
  | 'step_started'
  | 'step_completed'
  | 'result_ready'
  | 'answer_delta'
  | 'answer_completed'
  | 'error';

const API_BASE = import.meta.env.VITE_API_BASE || '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  listSessions: () => request<ChatSession[]>('/api/sessions'),
  createSession: (title?: string) =>
    request<ChatSession>('/api/sessions', { method: 'POST', body: JSON.stringify({ title }) }),
  getSession: (sessionId: string) => request<ChatSession>(`/api/sessions/${sessionId}`),
  updateSession: (sessionId: string, payload: Partial<Pick<ChatSession, 'title' | 'summary' | 'is_pinned'>>) =>
    request<ChatSession>(`/api/sessions/${sessionId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteSession: (sessionId: string) => request<void>(`/api/sessions/${sessionId}`, { method: 'DELETE' }),
  chat: (session_id: string, message: string, web_search_enabled: boolean) =>
    request<{ user_message: ChatMessage; assistant_message: ChatMessage }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ session_id, message, web_search_enabled }),
    }),
  chatStream: async (
    session_id: string,
    message: string,
    web_search_enabled: boolean,
    onEvent: (
      event: ChatStreamEvent,
      data: ChatMessage | ChatStep | { message: string } | { content: string } | { delta: string },
    ) => void,
  ) => {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, message, web_search_enabled }),
    });
    if (!response.ok) {
      throw new Error(await response.text() || `HTTP ${response.status}`);
    }
    if (!response.body) {
      throw new Error('当前浏览器不支持流式响应');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, '\n');
      let boundary = buffer.indexOf('\n\n');
      while (boundary >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const event = block.split('\n').find((line) => line.startsWith('event: '))?.slice(7) as ChatStreamEvent | undefined;
        const data = block.split('\n').filter((line) => line.startsWith('data: ')).map((line) => line.slice(6)).join('\n');
        if (event && data) {
          onEvent(event, JSON.parse(data));
        }
        boundary = buffer.indexOf('\n\n');
      }
      if (done) break;
    }
  },
};
