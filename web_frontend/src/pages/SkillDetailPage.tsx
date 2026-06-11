import { useState } from 'react';
import { SkillDefinition } from '../managementData';
import { DetailTabs, PageHeader, PrototypeToast, StatusBadge } from '../components/ManagementUi';

type Props = { skill: SkillDefinition; onNavigate: (path: string) => void; onUpdate: (skill: SkillDefinition) => void };

export function SkillDetailPage({ skill, onNavigate, onUpdate }: Props) {
  const [tab, setTab] = useState('概览');
  const [toast, setToast] = useState('');
  const [testInput, setTestInput] = useState(skill.examples[0] || '');
  const [testResult, setTestResult] = useState('');
  const notify = (text: string) => { setToast(text); window.setTimeout(() => setToast(''), 2200); };
  const toggle = () => { onUpdate({ ...skill, status: skill.status === 'enabled' ? 'disabled' : 'enabled' }); notify('Skill 状态已在原型中更新'); };
  const moveStep = (index: number, direction: number) => {
    const target = index + direction;
    if (target < 0 || target >= skill.steps.length) return;
    const steps = [...skill.steps]; [steps[index], steps[target]] = [steps[target], steps[index]];
    onUpdate({ ...skill, steps }); notify('工作流顺序已更新');
  };

  return <section className="management-page detail-page">
    <button className="back-link" type="button" onClick={() => onNavigate('/admin/skills')}>← 返回 Skill 列表</button>
    <PageHeader eyebrow={skill.category} title={skill.displayName} description={skill.description} actions={<><StatusBadge status={skill.status} /><button className="secondary-action" type="button" onClick={toggle}>{skill.status === 'enabled' ? '停用' : '启用'}</button><button className="primary-action" type="button" onClick={() => notify('配置已保存到原型状态')}>保存配置</button></>} />
    <DetailTabs tabs={['概览', '工作流', 'Schema', '测试']} active={tab} onChange={setTab} />
    {tab === '概览' && <div className="detail-grid">
      <article className="panel-card span-2"><h3>能力概览</h3><div className="definition-grid"><div><span>唯一标识</span><code>{skill.name}</code></div><div><span>输出类型</span><strong>{skill.outputType}</strong></div><div><span>工作流步骤</span><strong>{skill.steps.length}</strong></div><div><span>最近更新</span><strong>{skill.updatedAt}</strong></div></div></article>
      <article className="panel-card"><h3>示例问题</h3>{skill.examples.map((example) => <p className="example-item" key={example}>{example}</p>)}</article>
      <article className="panel-card"><h3>MCP 依赖</h3><div className="dependency-list">{skill.mcpTools.map((mcpName) => <button key={mcpName} type="button" onClick={() => onNavigate(`/admin/mcps/${mcpName}`)}><span className="health-dot healthy" />{mcpName}<b>→</b></button>)}</div></article>
    </div>}
    {tab === '工作流' && <div className="workflow-editor">
      <div className="section-toolbar"><div><h3>纵向工作流</h3><p>步骤按顺序调用 MCP，并通过变量引用传递结果。</p></div><button className="primary-action" type="button" onClick={() => { onUpdate({ ...skill, steps: [...skill.steps, { name: `new_step_${skill.steps.length + 1}`, description: '新工作流步骤', mcp: 'llm', arguments: '{{input.query}}' }] }); notify('已添加步骤'); }}>＋ 添加步骤</button></div>
      {skill.steps.map((item, index) => <article className="workflow-editor-step" key={`${item.name}-${index}`}><div className="step-number">{index + 1}</div><div className="step-main"><div><h4>{item.description}</h4><code>{item.name}</code></div><button type="button" onClick={() => onNavigate(`/admin/mcps/${item.mcp}`)}>{item.mcp} ↗</button><pre>{item.arguments}</pre></div><div className="step-actions"><button type="button" onClick={() => moveStep(index, -1)}>↑</button><button type="button" onClick={() => moveStep(index, 1)}>↓</button></div></article>)}
    </div>}
    {tab === 'Schema' && <div className="detail-grid"><article className="panel-card"><h3>输入字段</h3><div className="schema-field"><strong>query</strong><span>string · 必填</span><p>用户的自然语言查询</p></div></article><article className="panel-card code-card"><h3>原始配置</h3><pre>{JSON.stringify({ name: skill.name, category: skill.category, mcpTools: skill.mcpTools, inputSchema: { type: 'object', required: ['query'] } }, null, 2)}</pre></article></div>}
    {tab === '测试' && <div className="test-console"><div className="test-input"><h3>Skill 测试</h3><p>输入问题，验证路由、工作流步骤和输出结构。</p><textarea value={testInput} onChange={(event) => setTestInput(event.target.value)} /><button className="primary-action" type="button" onClick={() => setTestResult(`测试完成：${skill.displayName} 已依次执行 ${skill.steps.length} 个步骤，所有依赖 MCP 返回正常。`)}>运行测试</button></div><div className="test-output"><h3>运行结果</h3>{testResult ? <><span className="result-success">✓ 执行成功</span><p>{testResult}</p><div className="mini-timeline">{skill.steps.map((item) => <span key={item.name}>✓ {item.description}<small>{item.mcp}</small></span>)}</div></> : <div className="empty-console">等待运行测试</div>}</div></div>}
    <PrototypeToast text={toast} />
  </section>;
}
