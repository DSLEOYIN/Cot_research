import { FormEvent, useState } from 'react';

type Props = {
  error: string;
  onLogin: (username: string, password: string) => void;
};

export function LoginPage({ error, onLogin }: Props) {
  const [username, setUsername] = useState('platform_admin');
  const [password, setPassword] = useState('admin123');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onLogin(username, password);
  };

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-brand-mark">AI</div>
        <span>广汽集团 AI 一体化平台</span>
        <h1>账号登录</h1>
        <p>登录后按账号、角色和组织计算 Skill 权限。当前为 mock 演示账号。</p>
        <form onSubmit={submit}>
          <label>
            <span>账号</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label>
            <span>密码</span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          {error && <div className="login-error">{error}</div>}
          <button className="primary-action" type="submit">登录</button>
        </form>
        <div className="login-demo-users">
          <strong>演示账号</strong>
          <button type="button" onClick={() => { setUsername('platform_admin'); setPassword('admin123'); }}>平台管理员 / admin123</button>
          <button type="button" onClick={() => { setUsername('chen_sales'); setPassword('sales123'); }}>销售员工 / sales123</button>
          <button type="button" onClick={() => { setUsername('lin_dev'); setPassword('dev123'); }}>AI 开发者 / dev123</button>
        </div>
      </section>
    </main>
  );
}
