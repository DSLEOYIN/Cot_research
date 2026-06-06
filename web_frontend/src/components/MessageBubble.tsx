import { ChatMessage } from '../api/client';
import { skillDisplayName } from '../skillLabels';
import { ResultRenderer } from './ResultRenderer';
import { ThoughtProcess } from './ThoughtProcess';

type Props = {
  message: ChatMessage;
};

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';
  return (
    <article className={`message ${isUser ? 'user' : 'ai'} ${!isUser && message.steps?.length ? 'workflow-message' : ''}`}>
      <div className={`msg-avatar ${isUser ? 'user-avatar' : 'ai-avatar'}`}>
        <img src={isUser ? '/assets/user-avatar.png' : '/assets/assistant-avatar.png'} alt="" />
      </div>
      <div>
        <div className={`msg-content ${!isUser && message.steps?.length ? 'workflow-content' : ''}`}>
          {!isUser && message.selected_skill && <div className="msg-mode-badge thinking">{skillDisplayName(message.selected_skill)}</div>}
          {!isUser && message.steps?.length ? <ThoughtProcess steps={message.steps} /> : null}
          <ResultRenderer content={message.content} />
        </div>
        <div className="msg-time">{new Date(message.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</div>
      </div>
    </article>
  );
}
