type Props = {
  path: string;
  collapsed: boolean;
  onNavigate: (path: string) => void;
  onToggle: () => void;
};

const items = [
  { path: '/chat', label: 'AI 助手', icon: '✦' },
  { path: '/skills', label: '能力中心', icon: '◇' },
  { path: '/admin', label: '平台治理', icon: '⌘' },
];
// Admin routes live under /admin, with catalogs at /admin/skills and /admin/mcps.

export function GlobalNav({ path, collapsed, onNavigate, onToggle }: Props) {
  return (
    <aside className={`global-nav ${collapsed ? 'collapsed' : ''}`}>
      <div className="global-brand">
        <div className="global-brand-mark">C</div>
        {!collapsed && <div><strong>AI 一体化平台</strong><span>能力工作台</span></div>}
      </div>
      <nav className="global-nav-items">
        {items.map((item) => (
          <button key={item.path} type="button" aria-label={item.label} title={collapsed ? item.label : undefined} className={path.startsWith(item.path) ? 'active' : ''} onClick={() => onNavigate(item.path)}>
            <i>{item.icon}</i>{!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>
      <div className="global-nav-foot">
        {!collapsed && <div className="system-health"><span /><div><strong>平台运行正常</strong><small>13 项集团能力已接入</small></div></div>}
        <button className="nav-collapse" type="button" onClick={onToggle} title={collapsed ? '展开导航' : '收起导航'}>{collapsed ? '›' : '‹'}</button>
      </div>
    </aside>
  );
}
