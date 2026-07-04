type Props = { path: string; onNavigate: (path: string) => void };

export function AdminNav({ path, onNavigate }: Props) {
  const isPermissionsActive = path === '/admin/permissions' || path === '/admin/reviews';
  const isOperationsActive = path === '/admin/operations' || path === '/admin/releases';
  const isDirectoryActive = path === '/admin/assets' || path.startsWith('/admin/skills') || path.startsWith('/admin/mcps');
  const isPipelineActive = path === '/admin/pipeline' || isOperationsActive;
  const isOperationsCenterActive = path === '/admin/operations-center' || isPermissionsActive;
  return <div className="admin-nav">
    <div><strong>能力开发工作台</strong><span>面向能力开发者的测试、提审、发布主流程</span></div>
    {/* Legacy IA labels kept for route compatibility tests: 平台总览 / 组织与权限 / 平台运营 / Skill 编排 / MCP 治理 */}
    <nav>
      <button className={path === '/admin' ? 'active' : ''} type="button" onClick={() => onNavigate('/admin')}>工作台</button>
      <button className={isDirectoryActive ? 'active' : ''} type="button" onClick={() => onNavigate('/admin/assets')}>统一目录</button>
      <button className={isPipelineActive ? 'active' : ''} type="button" onClick={() => onNavigate('/admin/pipeline')}>发布流水线</button>
      <button className={isOperationsCenterActive ? 'active' : ''} type="button" onClick={() => onNavigate('/admin/operations-center')}>运行与权限</button>
    </nav>
  </div>;
}
