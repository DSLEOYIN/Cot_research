type Props = { path: string; onNavigate: (path: string) => void };

export function AdminNav({ path, onNavigate }: Props) {
  return <div className="admin-nav">
    <div><strong>系统管理</strong><span>面向系统维护与运维人员</span></div>
    <nav>
      <button className={path.startsWith('/admin/skills') ? 'active' : ''} type="button" onClick={() => onNavigate('/admin/skills')}>Skill 管理</button>
      <button className={path.startsWith('/admin/mcps') ? 'active' : ''} type="button" onClick={() => onNavigate('/admin/mcps')}>MCP 管理</button>
    </nav>
  </div>;
}
