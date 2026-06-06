import { ChatSession } from '../api/client';

type Props = {
  session: ChatSession;
  onCancel: () => void;
  onConfirm: () => void;
};

export function DeleteDialog({ session, onCancel, onConfirm }: Props) {
  return (
    <div className="dialog-overlay">
      <div className="dialog">
        <h2>删除对话</h2>
        <p>确定删除“{session.title}”吗？此操作不会影响其他会话。</p>
        <div className="dialog-actions">
          <button type="button" onClick={onCancel}>取消</button>
          <button className="danger" type="button" onClick={onConfirm}>删除</button>
        </div>
      </div>
    </div>
  );
}
