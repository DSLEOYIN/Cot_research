import { FormEvent, useEffect, useState } from 'react';

type Props = {
  disabled: boolean;
  webSearchEnabled: boolean;
  onWebSearchChange: (enabled: boolean) => void;
  onSend: (text: string) => void;
  initialText?: string;
};

export function ChatInput({ disabled, webSearchEnabled, onWebSearchChange, onSend, initialText = '' }: Props) {
  const [text, setText] = useState('');
  const placeholderText = '发消息、发起流程或输入 / 选择技能';

  useEffect(() => {
    if (initialText) setText(initialText);
  }, [initialText]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText('');
  }

  return (
    <form className="input-area" onSubmit={submit}>
      <div className="input-shell">
        <div className="input-row">
          <input
            value={text}
            disabled={disabled}
            onChange={(event) => setText(event.target.value)}
            placeholder={placeholderText}
          />
          <button className="send-btn" type="submit" disabled={disabled || !text.trim()} title="发送" aria-label="发送消息">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3.4 20.4 21 12 3.4 3.6l.2 6.4 12.4 2-12.4 2-.2 6.4Z" />
            </svg>
          </button>
        </div>
        <div className="input-tools">
          <button
            className={`network-search-toggle ${webSearchEnabled ? 'active' : ''}`}
            type="button"
            aria-pressed={webSearchEnabled}
            title={webSearchEnabled ? '关闭联网搜索' : '开启联网搜索'}
            onClick={() => onWebSearchChange(!webSearchEnabled)}
          >
            <svg className="network-search-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="8" cy="8" r="5.25" stroke="currentColor" strokeWidth="1.2" />
              <path d="M2.75 8h10.5M8 2.75c1.45 1.38 2.25 3.23 2.25 5.25S9.45 11.87 8 13.25M8 2.75C6.55 4.13 5.75 5.98 5.75 8S6.55 11.87 8 13.25" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>联网搜索</span>
            <span className="network-search-state">{webSearchEnabled ? 'ON' : 'OFF'}</span>
          </button>
        </div>
      </div>
    </form>
  );
}
