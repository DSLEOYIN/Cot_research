import { ReactNode, useState } from 'react';
import { GlobalNav } from './GlobalNav';

type Props = { path: string; onNavigate: (path: string) => void; children: ReactNode };

export function AppShell({ path, onNavigate, children }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const modeLabel = path.startsWith('/admin')
    ? path === '/admin' ? '系统管理工作台 · 生成、测试、审核、发布全链路原型' : '系统管理原型 · 配置操作仅在当前页面生效'
    : path.startsWith('/skills')
      ? path === '/skills/library' ? '企业 Skill 商店 · 内部审核能力' : '我的 Skill · 已安装能力'
      : 'ChatBI 智能工作台';
  return (
    <main className={`workspace-shell ${collapsed ? 'nav-collapsed' : ''}`}>
      <GlobalNav path={path} collapsed={collapsed} onNavigate={onNavigate} onToggle={() => setCollapsed((value) => !value)} />
      <div className="workspace-content">
        <div className="prototype-mode prototype-mode-hidden" aria-hidden="true">{modeLabel}</div>
        {children}
      </div>
    </main>
  );
}
