type Props = {
  path: string;
  collapsed: boolean;
  onNavigate: (path: string) => void;
  onToggle: () => void;
};

const items = [
  { path: '/chat', label: '智能问答', icon: '✦' },
  { path: '/skills', label: 'Skill 商店', icon: '◇' },
  { path: '/admin/skills', label: '系统管理', icon: '⌘' },
];

export function GlobalNav({ path, collapsed, onNavigate, onToggle }: Props) {
  return (
    <aside className={`global-nav ${collapsed ? 'collapsed' : ''}`}>
      <div className="global-brand">
        <div className="global-brand-mark">C</div>
        {!collapsed && <div><strong>ChatBI</strong><span>能力工作台</span></div>}
      </div>
      <nav className="global-nav-items">
        {items.map((item) => (
          <button key={item.path} type="button" aria-label={item.label} title={collapsed ? item.label : undefined} className={path.startsWith(item.path) ? 'active' : ''} onClick={() => onNavigate(item.path)}>
            <i>{item.icon}</i>{!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>
      <div className="global-nav-foot">
        {!collapsed && <div className="system-health"><span /><div><strong>系统运行正常</strong><small>13 项能力已接入</small></div></div>}
        <button className="nav-collapse" type="button" onClick={onToggle} title={collapsed ? '展开导航' : '收起导航'}>{collapsed ? '›' : '‹'}</button>
      </div>
    </aside>
  );
}
