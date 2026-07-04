import { useLayoutEffect, useRef, WheelEvent } from 'react';
import { ChatMessage } from '../api/client';
import { MessageBubble } from './MessageBubble';

type Props = {
  messages: ChatMessage[];
  emptyHint: boolean;
  onAction: (text: string) => void;
};

export function MessageList({ messages, emptyHint, onAction }: Props) {
  const listRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const userPausedRef = useRef(false);
  const streamingActiveRef = useRef(false);
  const activeStreamingIdRef = useRef<string | null>(null);
  const latestStreamingId = [...messages].reverse().find((message) => message.is_streaming)?.id || null;

  function scrollToBottom() {
    const list = listRef.current;
    if (!streamingActiveRef.current) return;
    if (!list || userPausedRef.current) return;
    list.scrollTop = list.scrollHeight;
  }

  function handleWheel(event: WheelEvent<HTMLDivElement>) {
    if (!latestStreamingId) return;
    if (event.deltaY < 0) {
      userPausedRef.current = true;
    } else {
      const list = listRef.current;
      if (list && list.scrollHeight - list.scrollTop - list.clientHeight < 96) {
        userPausedRef.current = false;
      }
    }
  }

  useLayoutEffect(() => {
    if (latestStreamingId && latestStreamingId !== activeStreamingIdRef.current) {
      userPausedRef.current = false;
    }
    streamingActiveRef.current = Boolean(latestStreamingId);
    activeStreamingIdRef.current = latestStreamingId;
    scrollToBottom();
  }, [messages, latestStreamingId]);

  useLayoutEffect(() => {
    const content = contentRef.current;
    if (!content) return;
    const observer = new ResizeObserver(scrollToBottom);
    observer.observe(content);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="message-list" ref={listRef} onWheel={handleWheel}>
      <div className="message-list-content" ref={contentRef}>
        {emptyHint && (
          <div className="message ai">
            <div className="msg-avatar ai-avatar"><img src="/assets/assistant-avatar.png" alt="" /></div>
            <div className="msg-content welcome">
              你好，我是广汽集团 AI 助手。可以查询内部业务数据、做同环比分析，也可以在开启联网后结合公开资料进行综合分析。
            </div>
          </div>
        )}
        {messages.map((message) => <MessageBubble key={message.id} message={message} onAction={onAction} />)}
      </div>
    </div>
  );
}
