import { useMemo, useState } from 'react';
import { OperationsTask, SkillDefinition } from '../managementData';
import { DetailTabs, PageHeader, PrototypeToast, StatusBadge } from '../components/ManagementUi';

type Props = {
  skill: SkillDefinition;
  tasks: OperationsTask[];
  onNavigate: (path: string) => void;
  onUpdate: (skill: SkillDefinition) => void;
};

export function SkillDetailPage({ skill, tasks, onNavigate, onUpdate }: Props) {
  const [tab, setTab] = useState('引导流程');
  const [toast, setToast] = useState('');
  const [testInput, setTestInput] = useState(skill.examples[0] || '');
  const [testResult, setTestResult] = useState('');
  const [docDraft, setDocDraft] = useState({
    value: skill.tagline || skill.description,
    flow: `${skill.steps.map((item, index) => `${index + 1}. ${item.description} -> ${item.mcp}`).join('\n')}`,
    examples: `${skill.examples[0] || ''}\n---\n${skill.exampleOutput || skill.outputType}`,
  });
  const notify = (text: string) => { setToast(text); window.setTimeout(() => setToast(''), 2200); };
  const relatedTasks = useMemo(() => tasks.filter((task) => task.entityName.includes(skill.name) || task.title.includes(skill.displayName) || task.parentTaskId), [tasks, skill.name, skill.displayName]);
  const hasTestPassed = Boolean(testResult);
  const guidanceSteps = [
    { key: '1', label: '填写目标', description: '补全名称、目标、场景与期望输出，让 AI 明白你要做什么。', state: 'done' },
    { key: '2', label: 'AI 生成', description: '系统按规范生成 Skill 草案、依赖与示例输入输出。', state: 'done' },
    { key: '3', label: '校对文档', description: '重点确认作用说明、流程说明、依赖 MCP 和示例结果。', state: 'current' },
    { key: '4', label: '自动测试并提交', description: '平台自动执行测试，通过后再提交审核中心。', state: hasTestPassed ? 'done' : 'pending' },
  ] as const;

  const moveStep = (index: number, direction: number) => {
    const target = index + direction;
    if (target < 0 || target >= skill.steps.length) return;
    const steps = [...skill.steps];
    [steps[index], steps[target]] = [steps[target], steps[index]];
    onUpdate({ ...skill, steps });
    notify('工作流顺序已更新');
  };

  const enableSkill = () => {
    onUpdate({ ...skill, enabledForUser: !skill.enabledForUser });
    notify(skill.enabledForUser ? '已在原型中停用用户侧能力' : '已在原型中启用用户侧能力');
  };

  return <section className="management-page detail-page">
    <button className="back-link" type="button" onClick={() => onNavigate('/admin/skills')}>← 返回 Skill 列表</button>
    <PageHeader
      eyebrow={skill.category}
      title={skill.displayName}
      description={skill.description}
      actions={<><StatusBadge status={skill.status} /><button className="secondary-action" type="button" onClick={enableSkill}>{skill.enabledForUser ? '停用用户侧' : '启用用户侧'}</button><button className="primary-action" type="button" onClick={() => notify('已提交审核中心，等待人工复核')}>提交审核</button></>}
    />
    <DetailTabs tabs={['引导流程', '工作流', 'Schema', '测试']} active={tab} onChange={setTab} />
    {tab === '引导流程' && <div className="skill-guided-layout">
      <section className="panel-card skill-guidance-hero">
        <div>
          <span>GUIDED FLOW</span>
          <h3>按这 4 步做，就能把一个 Skill 从想法推进到可审核状态</h3>
          <p>先说清楚目标，再让 AI 生成，随后校对关键文档，最后跑自动测试并提交审核。整个过程都在系统里完成，不需要跳到外部环境。</p>
        </div>
        <div className="skill-guidance-progress">
          {guidanceSteps.map((item) => <article key={item.key} className={`guidance-step-card ${item.state}`}>
            <b>{item.key}</b>
            <strong>{item.label}</strong>
            <p>{item.description}</p>
          </article>)}
        </div>
      </section>

      <div className="skill-guidance-main">
        <article className="panel-card skill-guidance-step">
          <div className="section-toolbar">
            <div><h3>第 1 步：混合输入，把需求说清楚</h3><p>运维只需要填这几个字段，AI 就能按规范生成 Skill 草案。</p></div>
            <button className="secondary-action" type="button" onClick={() => notify('已按当前描述重新生成草案')}>重新生成</button>
          </div>
          <div className="hybrid-input-grid">
            <label><span>名称</span><input defaultValue={skill.displayName} /></label>
            <label><span>目标</span><input defaultValue={skill.tagline || skill.description} /></label>
            <label><span>适用场景</span><input defaultValue={skill.scenes?.join(' / ') || ''} /></label>
            <label><span>期望输出</span><input defaultValue={skill.expectedOutput?.join(' / ') || skill.outputType} /></label>
            <label className="hybrid-prompt"><span>自然语言命令</span><textarea defaultValue={`请按照 mcp_and_skill_standard_specs 规范生成 ${skill.displayName}，自动补齐依赖、示例输入输出与测试用例。`} /></label>
          </div>
        </article>

        <article className="panel-card skill-guidance-step">
          <div className="section-toolbar">
            <div><h3>第 2 步：确认 AI 生成结果与生成日志</h3><p>这里先看平台自动生成了什么，再决定是否进入文档校对。</p></div>
            <button className="secondary-action" type="button" onClick={() => notify('已触发 AI 自动修复重试')}>AI 自动修复重试</button>
          </div>
          <div className="skill-guidance-split">
            <div className="definition-grid">
              <div><span>当前发布版本</span><strong>{skill.publishedVersion}</strong></div>
              <div><span>最新草案</span><strong>{skill.latestVersion}</strong></div>
              <div><span>自动测试</span><strong>{hasTestPassed ? '已通过' : '待运行'}</strong></div>
              <div><span>用户启用状态</span><strong>{skill.enabledForUser ? '已启用' : '未启用'}</strong></div>
            </div>
            <div className="dependency-list">
              <button type="button"><span>skills/{skill.name}.py</span><b>查看 →</b></button>
              <button type="button"><span>示例输入 / 输出</span><b>查看 →</b></button>
              <button type="button"><span>自动测试报告</span><b>查看 →</b></button>
            </div>
          </div>
          <div className="generation-log">
            <article><span>10:31</span><strong>解析需求</strong><p>识别到需要新的业务诊断 Skill，并检查现有 MCP 依赖。</p></article>
            <article><span>10:33</span><strong>生成草案</strong><p>创建 `skills/{skill.name}.py` 草案，补齐 inputSchema、mcpTools 和 flow steps。</p></article>
            <article><span>10:35</span><strong>自动测试</strong><p>首次测试发现依赖 MCP 版本未发布，已创建 MCP 子任务并等待完成。</p></article>
            <article><span>10:38</span><strong>重试联调</strong><p>依赖就绪后重新跑示例输入输出测试，当前结果可提交审核。</p></article>
          </div>
        </article>

        <article className="panel-card skill-guidance-step">
          <div className="section-toolbar">
            <div><h3>第 3 步：校对关键文档</h3><p>审核前最需要运维确认的是作用、流程、依赖 MCP 和示例输入输出。</p></div>
            <button className="primary-action" type="button" onClick={() => notify('关键文档修改已保存到原型状态')}>保存文档</button>
          </div>
          <div className="doc-editor-grid">
            <label>
              <span>作用说明</span>
              <textarea value={docDraft.value} onChange={(event) => setDocDraft((current) => ({ ...current, value: event.target.value }))} />
            </label>
            <label>
              <span>流程说明</span>
              <textarea value={docDraft.flow} onChange={(event) => setDocDraft((current) => ({ ...current, flow: event.target.value }))} />
            </label>
            <label className="doc-editor-wide">
              <span>示例输入输出</span>
              <textarea value={docDraft.examples} onChange={(event) => setDocDraft((current) => ({ ...current, examples: event.target.value }))} />
            </label>
          </div>
        </article>

        <article className="panel-card skill-guidance-step">
          <div className="section-toolbar">
            <div><h3>第 4 步：跑自动测试，再提交审核</h3><p>所有测试都在系统内执行，通过后再进入审核中心，不需要外部测试环境。</p></div>
            <button className="primary-action" type="button" onClick={() => setTestResult(`测试完成：${skill.displayName} 已依次执行 ${skill.steps.length} 个步骤，自动测试全部通过，可提交审核。`)}>运行自动测试</button>
          </div>
          <div className="skill-guidance-test-strip">
            <div className="test-input compact-test-input">
              <h3>测试输入</h3>
              <p>直接使用示例问题验证 Skill 的主流程和依赖 MCP。</p>
              <textarea value={testInput} onChange={(event) => setTestInput(event.target.value)} />
            </div>
            <div className="test-output compact-test-output">
              <h3>测试结果</h3>
              {testResult ? <><span className="result-success">✓ 执行成功</span><p>{testResult}</p><div className="mini-timeline">{skill.steps.map((item) => <span key={item.name}>✓ {item.description}<small>{item.mcp}</small></span>)}</div></> : <div className="empty-console">等待运行测试</div>}
            </div>
          </div>
        </article>
      </div>

      <aside className="skill-guidance-side">
        <article className="panel-card">
          <h3>当前状态</h3>
          <div className="definition-grid guidance-mini-grid">
            <div><span>审核状态</span><strong>{skill.status === 'enabled' ? '可提交' : '草稿中'}</strong></div>
            <div><span>依赖 MCP</span><strong>{skill.mcpTools.length} 个</strong></div>
            <div><span>工作流步骤</span><strong>{skill.steps.length} 步</strong></div>
            <div><span>示例用例</span><strong>{skill.examples.length} 条</strong></div>
          </div>
        </article>

        <article className="panel-card">
          <h3>审核重点</h3>
          <div className="mini-timeline task-timeline">
            <span>✓ 功能作用是否说清楚<small>是否能让审核人快速理解这个 Skill 做什么</small></span>
            <span>✓ 流程是否闭环<small>步骤顺序、依赖 MCP、输入输出是否一致</small></span>
            <span>✓ 示例是否可信<small>输入输出是否能反映真实使用场景</small></span>
          </div>
        </article>

        <article className="panel-card">
          <h3>依赖链路</h3>
          <div className="task-stack compact">
            <article className="task-card stage-published">
              <div className="task-card-top"><div><span>Skill 主任务</span><strong>{skill.displayName}</strong></div><i>{skill.releaseStatus === 'published' ? '已发布' : '待处理'}</i></div>
              <p>主任务在依赖 MCP 就绪后继续联调测试并进入审核中心。</p>
            </article>
            <article className="task-card stage-ready_for_review">
              <div className="task-card-top"><div><span>MCP 子任务</span><strong>inventory_snapshot_mcp</strong></div><i>待审核</i></div>
              <p>MCP 子任务已通过自动测试，等待人工审核后发布。</p>
            </article>
          </div>
        </article>

        {relatedTasks.length > 0 && <article className="panel-card">
          <h3>任务流转</h3>
          <div className="mini-timeline task-timeline">
            {relatedTasks.map((task) => <span key={task.id}>✓ {task.title}<small>{task.summary}</small></span>)}
          </div>
        </article>}
      </aside>
    </div>}

    {tab === '工作流' && <div className="workflow-editor">
      <div className="section-toolbar"><div><h3>纵向工作流</h3><p>步骤按顺序调用 MCP，并通过变量引用传递结果。</p></div><button className="primary-action" type="button" onClick={() => { onUpdate({ ...skill, steps: [...skill.steps, { name: `new_step_${skill.steps.length + 1}`, description: '新工作流步骤', mcp: 'llm', arguments: '{{input.query}}' }] }); notify('已添加步骤'); }}>＋ 添加步骤</button></div>
      {skill.steps.map((item, index) => {
        const mcpName = item.mcp;
        return <article className="workflow-editor-step" key={`${item.name}-${index}`}><div className="step-number">{index + 1}</div><div className="step-main"><div><h4>{item.description}</h4><code>{item.name}</code></div><button type="button" onClick={() => onNavigate(`/admin/mcps/${mcpName}`)}>{item.mcp} ↗</button><pre>{item.arguments}</pre></div><div className="step-actions"><button type="button" onClick={() => moveStep(index, -1)}>↑</button><button type="button" onClick={() => moveStep(index, 1)}>↓</button></div></article>;
      })}
    </div>}

    {tab === 'Schema' && <div className="detail-grid">
      <article className="panel-card"><h3>输入字段</h3><div className="schema-field"><strong>query</strong><span>string · 必填</span><p>用户的自然语言查询</p></div></article>
      <article className="panel-card"><h3>场景与输出约束</h3>{skill.scenes?.map((scene) => <p className="example-item" key={scene}>{scene}</p>)}{skill.expectedOutput?.map((item) => <p className="example-item" key={item}>{item}</p>)}</article>
      <article className="panel-card code-card span-2"><h3>原始配置</h3><pre>{JSON.stringify({ name: skill.name, category: skill.category, mcpTools: skill.mcpTools, inputSchema: { type: 'object', required: ['query'] }, releaseStatus: skill.releaseStatus }, null, 2)}</pre></article>
    </div>}

    {tab === '测试' && <div className="test-console">
      <div className="test-input">
        <h3>自动测试</h3>
        <p>平台自动校验模块导入、Skill 配置结构、MCP 可解析性和示例输出结构。</p>
        <textarea value={testInput} onChange={(event) => setTestInput(event.target.value)} />
        <button className="primary-action" type="button" onClick={() => setTestResult(`测试完成：${skill.displayName} 已依次执行 ${skill.steps.length} 个步骤，自动测试全部通过，可提交审核。`)}>运行测试</button>
      </div>
      <div className="test-output">
        <h3>运行结果</h3>
        {testResult ? <><span className="result-success">✓ 执行成功</span><p>{testResult}</p><div className="mini-timeline">{skill.steps.map((item) => <span key={item.name}>✓ {item.description}<small>{item.mcp}</small></span>)}</div></> : <div className="empty-console">等待运行测试</div>}
      </div>
    </div>}
    <PrototypeToast text={toast} />
  </section>;
}
