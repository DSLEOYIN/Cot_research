import { useState } from 'react';
import { ChatMessage } from '../api/client';
import { skillDisplayName } from '../skillLabels';
import { ResultRenderer } from './ResultRenderer';
import { ThoughtProcess } from './ThoughtProcess';
import { TypewriterResult } from './TypewriterResult';

type Props = {
  message: ChatMessage;
};

export function MessageBubble({ message }: Props) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const answerStarted = Boolean(message.answer_started);
  const streamBase = message.stream_base ?? message.content;
  const streamText = message.stream_text ?? '';

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
          {!isUser && message.steps?.length ? <ThoughtProcess steps={message.steps} collapseSignal={answerStarted} /> : null}
          {!isUser && answerStarted ? (
            <>
              {streamBase && <ResultRenderer content={streamBase} />}
              <TypewriterResult content={streamText} active={answerStarted} />
            </>
          ) : (
            <ResultRenderer content={message.content} />
          )}
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
