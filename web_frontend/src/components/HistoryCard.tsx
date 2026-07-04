import { ChatSession } from '../api/client';

type Props = {
  session: ChatSession;
  active: boolean;
  onSelect: (sessionId: string) => void;
  onRename: (session: ChatSession) => void;
  onDelete: (session: ChatSession) => void;
  onTogglePin: (session: ChatSession) => void;
};

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export function HistoryCard({ session, active, onSelect, onRename, onDelete, onTogglePin }: Props) {
  const hasPendingAction = session.pending_action_status === 'pending_confirmation';
  const summaryText = hasPendingAction ? (session.pending_action_message || session.summary || '待确认动作') : (session.summary || '暂无对话内容');

  return (
    <div className="history-card-item">
      <button className={`history-card ${active ? 'active' : ''}`} type="button" onClick={() => onSelect(session.id)}>
        <div className="history-card-top">
          <span className="history-card-title-wrap">
            {session.is_pinned && <img className="history-card-pin-indicator" src="/assets/icons/history-pin.svg" alt="" />}
            <span className="history-card-title">{session.title}</span>
            {hasPendingAction && <span className="history-card-status">待确认动作</span>}
          </span>
          <span className="history-card-time">{formatTime(session.updated_at)}</span>
        </div>
        <span className="history-card-content">{summaryText}</span>
      </button>
      <div className="history-card-actions">
        <button className="history-card-action" type="button" title={session.is_pinned ? '取消置顶' : '置顶'} onClick={() => onTogglePin(session)}>
          <img className="history-card-action-icon" src={session.is_pinned ? '/assets/icons/history-unpin.svg' : '/assets/icons/history-pin.svg'} alt="" />
        </button>
        <button className="history-card-action" type="button" title="重命名" onClick={() => onRename(session)}>✎</button>
        <button className="history-card-action" type="button" title="删除" data-action="delete" onClick={() => onDelete(session)}>×</button>
      </div>
    </div>
  );
}
