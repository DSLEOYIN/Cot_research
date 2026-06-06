import { FormEvent, useState } from 'react';
import { ChatSession } from '../api/client';

type Props = {
  session: ChatSession;
  onCancel: () => void;
  onConfirm: (title: string) => void;
};

export function RenameDialog({ session, onCancel, onConfirm }: Props) {
  const [title, setTitle] = useState(session.title);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (title.trim()) onConfirm(title.trim());
  }

  return (
    <div className="dialog-overlay">
      <form className="dialog" onSubmit={submit}>
        <h2>重命名对话</h2>
        <input value={title} maxLength={30} onChange={(event) => setTitle(event.target.value)} />
        <div className="dialog-actions">
          <button type="button" onClick={onCancel}>取消</button>
          <button className="primary" type="submit">确认</button>
        </div>
      </form>
    </div>
  );
}
