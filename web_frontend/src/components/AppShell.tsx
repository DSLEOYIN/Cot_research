import { ReactNode, useState } from 'react';
import { GlobalNav } from './GlobalNav';
import { AccountPermissionProfile } from '../api/client';

type Props = {
  path: string;
  currentAccount: AccountPermissionProfile;
  onLogout: () => void;
  onNavigate: (path: string) => void;
  children: ReactNode;
};

export function AppShell({ path, currentAccount, onLogout, onNavigate, children }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const modeLabel = path.startsWith('/admin')
    ? path === '/admin' ? '平台治理工作台 · 组织、权限、编排、运营一体化原型' : '平台治理原型 · 当前操作仅在前端原型内生效'
    : path.startsWith('/skills')
      ? path === '/skills/library' ? '集团能力目录 · 已认证业务能力' : '能力中心 · 已开通与推荐能力'
      : '集团 AI 助手工作台';
  return (
    <main className={`workspace-shell ${collapsed ? 'nav-collapsed' : ''}`}>
      <GlobalNav path={path} collapsed={collapsed} onNavigate={onNavigate} onToggle={() => setCollapsed((value) => !value)} />
      <div className="workspace-content">
        <div className="prototype-mode">
          <span>{modeLabel}</span>
          <strong>{currentAccount.displayName} · {currentAccount.organizationName} · {currentAccount.roleNames.join(' / ')}</strong>
          <button type="button" onClick={onLogout}>退出登录</button>
        </div>
        {children}
      </div>
    </main>
  );
}
