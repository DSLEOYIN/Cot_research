import { useState } from 'react';
import { ChatMessage } from '../api/client';
import { skillDisplayName } from '../skillLabels';
import { ResultRenderer } from './ResultRenderer';
import { ThoughtProcess } from './ThoughtProcess';

type Props = {
  message: ChatMessage;
  onAction: (text: string) => void;
};

export function MessageBubble({ message, onAction }: Props) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const answerStarted = Boolean(message.answer_started);
  const shouldCollapseThoughts = answerStarted || !message.is_streaming;
  const displayContent = message.content;
  const isActionSkillMessage = message.selected_skill === 'leave_request';
  const showsPendingConfirmation = isActionSkillMessage && message.content.includes('需确认后提交');

  async function copyMessage() {
    try {
      await navigator.clipboard.writeText(message.content);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = message.content;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      textarea.remove();
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <article className={`message ${isUser ? 'user' : 'ai'} ${!isUser && message.steps?.length ? 'workflow-message' : ''}`}>
      <div className={`msg-avatar ${isUser ? 'user-avatar' : 'ai-avatar'}`}>
        <img src={isUser ? '/assets/user-avatar.png' : '/assets/assistant-avatar.png'} alt="" />
      </div>
      <div>
        <div className={`msg-content ${!isUser && message.steps?.length ? 'workflow-content' : ''}`}>
          {!isUser && message.selected_skill && <div className="msg-mode-badge thinking">{skillDisplayName(message.selected_skill)}</div>}
          {!isUser && isActionSkillMessage && <div className="message-action-guard">
            <strong>需确认后提交</strong>
            <span>这是动作型能力。系统会先展示审批路径和影响范围，确认后才会继续提交。</span>
            {showsPendingConfirmation && <div className="message-action-buttons">
              <button type="button" className="primary-action compact-action" onClick={() => onAction('确认提交')}>确认提交</button>
              <button type="button" className="secondary-action compact-action" onClick={() => onAction('取消')}>取消</button>
            </div>}
          </div>}
          {!isUser && message.steps?.length ? <ThoughtProcess steps={message.steps} collapseSignal={shouldCollapseThoughts} /> : null}
          <ResultRenderer content={displayContent} />
        </div>
        <div className="message-meta">
          <button className="message-copy-button" type="button" onClick={copyMessage} aria-label="复制消息" title="复制消息">
            {copied ? '已复制' : (
              <>
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 8h11v11H8zM5 16H4V5h11v1" /></svg>
                <span>复制</span>
              </>
            )}
          </button>
          <div className="msg-time">{new Date(message.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
      </div>
    </article>
  );
}
