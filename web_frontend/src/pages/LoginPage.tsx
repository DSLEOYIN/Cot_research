import { FormEvent, useState } from 'react';
import { EnvironmentStatus } from '../api/client';

type Props = {
  error: string;
  errorKind?: 'warning' | 'danger';
  environmentError: string;
  environmentStatus: EnvironmentStatus | null;
  onLogin: (username: string, password: string) => void;
};

const defaultDemoAccounts: EnvironmentStatus['demoAccounts'] = [
  { username: 'platform_admin', displayName: '平台管理员', passwordHint: 'admin123', canAccessAdmin: true },
  { username: 'chen_sales', displayName: '销售员工', passwordHint: 'sales123', canAccessAdmin: false },
  { username: 'lin_dev', displayName: 'AI 开发者', passwordHint: 'dev123', canAccessAdmin: true },
];

export function LoginPage({ error, errorKind = 'danger', environmentError, environmentStatus, onLogin }: Props) {
  const [username, setUsername] = useState('platform_admin');
  const [password, setPassword] = useState('admin123');
  const demoAccounts = environmentStatus?.demoAccounts?.length ? environmentStatus.demoAccounts : defaultDemoAccounts;

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
        <aside className="login-environment-panel">
          <h2>环境状态</h2>
          <dl>
            <div><dt>Mock API</dt><dd>{environmentStatus?.mockApiAvailable ? '可用' : '不可用'}</dd></div>
            <div><dt>演示模式</dt><dd>{environmentStatus?.isMockMode ? '已开启' : '未开启'}</dd></div>
            <div><dt>当前来源</dt><dd>{environmentError || '后端状态已同步'}</dd></div>
          </dl>
        </aside>
        <form onSubmit={submit}>
          <label>
            <span>账号</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label>
            <span>密码</span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          {error && <div className="login-error" data-kind={errorKind}>{error}</div>}
          <button className="primary-action" type="submit">登录</button>
        </form>
        <div className="login-demo-users">
          <strong>演示账号</strong>
          {demoAccounts.map((account) => (
            <button key={account.username} type="button" onClick={() => { setUsername(account.username); setPassword(account.passwordHint); }}>
              {account.displayName} / {account.passwordHint}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
