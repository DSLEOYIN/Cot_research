import { ChatSession } from '../api/client';
import { HistoryCard } from './HistoryCard';

type Props = {
  sessions: ChatSession[];
  activeSessionId?: string;
  onNew: () => void;
  onSelect: (sessionId: string) => void;
  onRename: (session: ChatSession) => void;
  onDelete: (session: ChatSession) => void;
  onTogglePin: (session: ChatSession) => void;
};

export function HistoryPanel({ sessions, activeSessionId, onNew, onSelect, onRename, onDelete, onTogglePin }: Props) {
  const pinned = sessions.filter((item) => item.is_pinned);
  const recent = sessions.filter((item) => !item.is_pinned);

  return (
    <aside className="history-panel">
      <div className="history-panel-header">
        <div>
          <div className="history-panel-title">历史对话</div>
          <div className="history-panel-subtitle">查看最近的提问记录</div>
        </div>
        <button className="history-panel-action" type="button" title="新建对话" onClick={onNew}>＋</button>
      </div>
      <div className="history-scroll">
        {pinned.length > 0 && (
          <section className="history-section">
            <div className="history-section-label">置顶</div>
            {pinned.map((session) => (
              <HistoryCard key={session.id} session={session} active={session.id === activeSessionId} onSelect={onSelect} onRename={onRename} onDelete={onDelete} onTogglePin={onTogglePin} />
            ))}
          </section>
        )}
        <section className="history-section">
          <div className="history-section-label">最近</div>
          {recent.length === 0 && <div className="history-empty">暂无历史会话</div>}
          {recent.map((session) => (
            <HistoryCard key={session.id} session={session} active={session.id === activeSessionId} onSelect={onSelect} onRename={onRename} onDelete={onDelete} onTogglePin={onTogglePin} />
          ))}
        </section>
      </div>
    </aside>
  );
}
