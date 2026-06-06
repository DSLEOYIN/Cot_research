import { useEffect, useMemo, useRef, useState } from 'react';
import { api, ChatMessage, ChatSession } from './api/client';
import { ChatHeader } from './components/ChatHeader';
import { ChatInput } from './components/ChatInput';
import { DeleteDialog } from './components/DeleteDialog';
import { HistoryPanel } from './components/HistoryPanel';
import { MessageList } from './components/MessageList';
import { RenameDialog } from './components/RenameDialog';

function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [renameTarget, setRenameTarget] = useState<ChatSession | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ChatSession | null>(null);
  const bootstrapped = useRef(false);

  const activeId = activeSession?.id;

  async function refreshSessions(nextActiveId?: string) {
    const nextSessions = await api.listSessions();
    setSessions(nextSessions);
    const target = nextSessions.find((item) => item.id === (nextActiveId || activeId)) || nextSessions[0] || null;
    if (target) {
      const detail = await api.getSession(target.id);
      setActiveSession(detail);
      setMessages(detail.messages || []);
      setWebSearchEnabled(detail.last_web_search_enabled || false);
    } else {
      setActiveSession(null);
      setMessages([]);
    }
  }

  async function createSession() {
    const session = await api.createSession('新对话');
    await refreshSessions(session.id);
  }

  useEffect(() => {
    if (bootstrapped.current) return;
    bootstrapped.current = true;
    refreshSessions().then(async () => {
      const latest = await api.listSessions();
      if (latest.length === 0) {
        await createSession();
      }
    }).catch((err) => setError(err.message));
  }, []);

  async function selectSession(sessionId: string) {
    const detail = await api.getSession(sessionId);
    setActiveSession(detail);
    setMessages(detail.messages || []);
    setWebSearchEnabled(detail.last_web_search_enabled || false);
  }

  async function sendMessage(text: string) {
    if (!activeSession || !text.trim()) return;
    setIsSending(true);
    setError('');
    const optimisticUser: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      session_id: activeSession.id,
      role: 'user',
      content: text,
      web_search_enabled: webSearchEnabled,
      trace_open: false,
      created_at: new Date().toISOString(),
    };
    const optimisticAssistant: ChatMessage = {
      id: `temp-assistant-${Date.now()}`,
      session_id: activeSession.id,
      role: 'assistant',
      content: '正在理解问题并调度执行链路...',
      selected_skill: null,
      web_search_enabled: webSearchEnabled,
      trace_open: true,
      created_at: new Date().toISOString(),
      steps: [{ id: 'running', message_id: 'running', step_index: 1, step_type: 'running', title: '运行中', status: 'running', summary: '正在执行 Skill 与 MCP 链路', created_at: new Date().toISOString() }],
    };
    setMessages((items) => [...items, optimisticUser, optimisticAssistant]);

    try {
      await api.chatStream(activeSession.id, text, webSearchEnabled, (event, data) => {
        if (event === 'message_created') {
          const userMessage = data as ChatMessage;
          setMessages((items) => items.map((item) => item.id === optimisticUser.id ? userMessage : item));
        }
        if (event === 'step_completed') {
          const step = data as NonNullable<ChatMessage['steps']>[number];
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? { ...item, steps: [...(item.steps || []).filter((existing) => existing.id !== 'running'), step] }
              : item
          )));
        }
        if (event === 'answer_completed') {
          const assistantMessage = data as ChatMessage;
          setMessages((items) => items.map((item) => item.id === optimisticAssistant.id ? assistantMessage : item));
        }
        if (event === 'error') {
          const streamError = data as { message: string };
          throw new Error(streamError.message);
        }
      });
      await refreshSessions(activeSession.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : '请求失败';
      setError(message);
      setMessages((items) => items.map((item) => (
        item.id === optimisticAssistant.id
          ? { ...item, content: `请求失败：${message}`, steps: [{ ...(item.steps?.[0] as any), status: 'failed', title: '执行错误', summary: message, error: message }] }
          : item
      )));
    } finally {
      setIsSending(false);
    }
  }

  async function renameSession(title: string) {
    if (!renameTarget) return;
    await api.updateSession(renameTarget.id, { title });
    setRenameTarget(null);
    await refreshSessions(renameTarget.id);
  }

  async function togglePin(session: ChatSession) {
    await api.updateSession(session.id, { is_pinned: !session.is_pinned });
    await refreshSessions(session.id);
  }

  async function deleteSession() {
    if (!deleteTarget) return;
    await api.deleteSession(deleteTarget.id);
    setDeleteTarget(null);
    await refreshSessions();
  }

  const emptyHint = useMemo(() => messages.length === 0, [messages]);

  return (
    <main className={`app-shell ${historyCollapsed ? 'history-collapsed' : ''}`}>
      <HistoryPanel
        sessions={sessions}
        activeSessionId={activeSession?.id}
        onNew={createSession}
        onSelect={selectSession}
        onRename={setRenameTarget}
        onDelete={setDeleteTarget}
        onTogglePin={togglePin}
      />
      <section className="assistant-panel-page">
        <ChatHeader
          session={activeSession}
          historyCollapsed={historyCollapsed}
          onToggleHistory={() => setHistoryCollapsed((collapsed) => !collapsed)}
          onNew={createSession}
        />
        {error && <div className="api-error">{error}</div>}
        <MessageList messages={messages} emptyHint={emptyHint} />
        <ChatInput
          disabled={isSending || !activeSession}
          webSearchEnabled={webSearchEnabled}
          onWebSearchChange={setWebSearchEnabled}
          onSend={sendMessage}
        />
      </section>
      {renameTarget && (
        <RenameDialog session={renameTarget} onCancel={() => setRenameTarget(null)} onConfirm={renameSession} />
      )}
      {deleteTarget && (
        <DeleteDialog session={deleteTarget} onCancel={() => setDeleteTarget(null)} onConfirm={deleteSession} />
      )}
    </main>
  );
}

export default App;
