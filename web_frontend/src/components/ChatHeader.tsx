import { ChatSession } from '../api/client';

type Props = {
  session: ChatSession | null;
  historyCollapsed: boolean;
  onToggleHistory: () => void;
  onNew: () => void;
};

export function ChatHeader({ session, historyCollapsed, onToggleHistory, onNew }: Props) {
  return (
    <header className="chat-header">
      <div className="chat-header-title">
        <img src="/assets/assistant-avatar.png" alt="" />
        <div>
          <h1>广汽国际 AI 助手</h1>
          <p>{session?.title || '生产 Web 智能问答'}</p>
        </div>
      </div>
      <div className="chat-header-actions">
        <button
          className={`ghost-button history-toggle-button ${historyCollapsed ? '' : 'active'}`}
          type="button"
          onClick={onToggleHistory}
          title={historyCollapsed ? '展开历史对话' : '收起历史对话'}
          aria-label={historyCollapsed ? "展开历史对话" : "收起历史对话"}
          aria-expanded={!historyCollapsed}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 6h18M3 12h18M3 18h18M8 6v12" />
          </svg>
        </button>
        <button className="ghost-button" type="button" onClick={onNew} title="新建对话">＋</button>
        <span className="online-dot" />
        <span className="online-text">在线</span>
      </div>
    </header>
  );
}
