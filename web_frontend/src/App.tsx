import { useEffect, useMemo, useRef, useState } from 'react';
import { api, ChatMessage, ChatSession } from './api/client';
import { ChatHeader } from './components/ChatHeader';
import { ChatInput } from './components/ChatInput';
import { DeleteDialog } from './components/DeleteDialog';
import { HistoryPanel } from './components/HistoryPanel';
import { MessageList } from './components/MessageList';
import { RenameDialog } from './components/RenameDialog';
import { AppShell } from './components/AppShell';
import { initialMcps, initialSkills, McpDefinition, SkillDefinition } from './managementData';
import { useWorkspaceRoute } from './useWorkspaceRoute';
import { SkillsPage } from './pages/SkillsPage';
import { SkillDetailPage } from './pages/SkillDetailPage';
import { McpsPage } from './pages/McpsPage';
import { McpDetailPage } from './pages/McpDetailPage';
import { SkillCenterPage } from './pages/SkillCenterPage';
import { SkillShowcasePage } from './pages/SkillShowcasePage';
import { AdminNav } from './components/AdminNav';

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
  const [skills, setSkills] = useState<SkillDefinition[]>(initialSkills);
  const [mcps, setMcps] = useState<McpDefinition[]>(initialMcps);
  const [managementNotice, setManagementNotice] = useState('');
  const [skillTryText, setSkillTryText] = useState('');
  const bootstrapped = useRef(false);
  const { path, navigate } = useWorkspaceRoute();

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

  async function refreshSessionList(nextActiveId?: string) {
    const nextSessions = await api.listSessions();
    setSessions(nextSessions);
    const target = nextSessions.find((item) => item.id === (nextActiveId || activeId));
    if (target) {
      setActiveSession((current) => current?.id === target.id ? { ...current, ...target } : current);
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
      content: '',
      selected_skill: null,
      web_search_enabled: webSearchEnabled,
      trace_open: true,
      created_at: new Date().toISOString(),
      steps: [],
      stream_base: '',
      stream_text: '',
      answer_started: false,
      is_streaming: true,
    };
    setMessages((items) => [...items, optimisticUser, optimisticAssistant]);

    try {
      await api.chatStream(activeSession.id, text, webSearchEnabled, (event, data) => {
        if (event === 'message_created') {
          const userMessage = data as ChatMessage;
          setMessages((items) => items.map((item) => item.id === optimisticUser.id ? userMessage : item));
        }
        if (event === 'step_started') {
          const step = data as NonNullable<ChatMessage['steps']>[number];
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id && !item.answer_started
              ? { ...item, steps: [...(item.steps || []).filter((existing) => existing.status !== 'running'), step] }
              : item
          )));
        }
        if (event === 'step_completed') {
          const step = data as NonNullable<ChatMessage['steps']>[number];
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? { ...item, steps: [...(item.steps || []).filter((existing) => existing.status !== 'running'), step] }
              : item
          )));
        }
        if (event === 'preview_ready') {
          const preview = data as { content: string };
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...item,
                  content: preview.content,
                  stream_base: preview.content,
                }
              : item
          )));
        }
        if (event === 'result_ready') {
          const result = data as { content: string };
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...item,
                  content: result.content,
                  stream_base: result.content,
                  answer_started: true,
                  steps: (item.steps || []).filter((existing) => existing.status !== 'running'),
                }
              : item
          )));
        }
        if (event === 'answer_delta') {
          const result = data as { delta: string };
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...item,
                  answer_started: true,
                  content: `${item.content || ''}${result.delta}`,
                  stream_text: `${item.stream_text || ''}${result.delta}`,
                }
              : item
          )));
        }
        if (event === 'answer_completed') {
          const assistantMessage = data as ChatMessage;
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...assistantMessage,
                  id: item.id,
                  stream_base: item.stream_base,
                  stream_text: item.stream_text,
                  answer_started: true,
                  is_streaming: false,
                }
              : item
          )));
        }
        if (event === 'error') {
          const streamError = data as { message: string };
          throw new Error(streamError.message);
        }
      });
      await refreshSessionList(activeSession.id);
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
  const showcaseSkillName = path.startsWith('/skills/') ? decodeURIComponent(path.slice('/skills/'.length)) : '';
  const adminSkillName = path.startsWith('/admin/skills/') ? decodeURIComponent(path.slice('/admin/skills/'.length)) : '';
  const mcpName = path.startsWith('/admin/mcps/') ? decodeURIComponent(path.slice('/admin/mcps/'.length)) : '';
  const selectedShowcaseSkill = skills.find((skill) => skill.name === showcaseSkillName);
  const selectedSkill = skills.find((skill) => skill.name === adminSkillName);
  const selectedMcp = mcps.find((mcp) => mcp.name === mcpName);
  const notifyManagement = (text: string) => {
    setManagementNotice(text);
    window.setTimeout(() => setManagementNotice(''), 2400);
  };
  const updateSkill = (next: SkillDefinition) => setSkills((items) => items.map((item) => item.name === next.name ? next : item));
  const updateMcp = (next: McpDefinition) => setMcps((items) => items.map((item) => item.name === next.name ? next : item));
  const installSkill = (name: string) => {
    setSkills((items) => items.map((item) => item.name === name ? { ...item, installed: true } : item));
    notifyManagement('Skill 已安装到你的助手');
  };
  const trySkill = (example: string) => {
    setSkillTryText(example);
    navigate('/chat');
  };

  let page = (
    <div className={`chat-workspace app-shell ${historyCollapsed ? 'history-collapsed' : ''}`}>
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
          initialText={skillTryText}
        />
      </section>
      {renameTarget && <RenameDialog session={renameTarget} onCancel={() => setRenameTarget(null)} onConfirm={renameSession} />}
      {deleteTarget && <DeleteDialog session={deleteTarget} onCancel={() => setDeleteTarget(null)} onConfirm={deleteSession} />}
    </div>
  );

  if (path === '/skills') page = <SkillCenterPage skills={skills} onNavigate={navigate} onInstall={installSkill} />;
  if (selectedShowcaseSkill) page = <SkillShowcasePage skill={selectedShowcaseSkill} onNavigate={navigate} onInstall={installSkill} onTry={trySkill} />;
  if (path === '/admin/skills') page = <><AdminNav path={path} onNavigate={navigate} /><SkillsPage skills={skills} onNavigate={navigate} onCreate={() => notifyManagement('新建 Skill 向导将在下一步接入，当前已展示完整管理原型')} /></>;
  if (selectedSkill) page = <><AdminNav path={path} onNavigate={navigate} /><SkillDetailPage skill={selectedSkill} onNavigate={navigate} onUpdate={updateSkill} /></>;
  if (path === '/admin/mcps') page = <><AdminNav path={path} onNavigate={navigate} /><McpsPage mcps={mcps} skills={skills} onNavigate={navigate} onCreate={() => notifyManagement('接入 MCP 向导将在下一步接入，当前已展示完整管理原型')} onHealthCheck={() => { setMcps((items) => items.map((item) => item.status === 'disabled' ? item : { ...item, health: 'healthy', updatedAt: '刚刚' })); notifyManagement('全部健康检查已完成'); }} /></>;
  if (selectedMcp) page = <><AdminNav path={path} onNavigate={navigate} /><McpDetailPage mcp={selectedMcp} skills={skills} onNavigate={navigate} onUpdate={updateMcp} /></>;

  return (
    <AppShell path={path} onNavigate={navigate}>
      {page}
      {managementNotice && <div className="prototype-toast">{managementNotice}</div>}
    </AppShell>
  );
}

export default App;
