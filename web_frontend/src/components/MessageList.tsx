import { ChatMessage } from '../api/client';
import { MessageBubble } from './MessageBubble';

type Props = {
  messages: ChatMessage[];
  emptyHint: boolean;
};

export function MessageList({ messages, emptyHint }: Props) {
  return (
    <div className="message-list">
      {emptyHint && (
        <div className="message ai">
          <div className="msg-avatar ai-avatar"><img src="/assets/assistant-avatar.png" alt="" /></div>
          <div className="msg-content welcome">
            你好，我是广汽国际 AI 助手。可以查询内部业务数据、做同环比分析，也可以在开启联网后结合公开资料进行综合分析。
          </div>
        </div>
      )}
      {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
    </div>
  );
}
