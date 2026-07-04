import { useMemo, useState } from 'react';
import { lifecycleActionByStage, lifecycleStageForReleaseStatus, LifecycleStage, OperationsTask, ReleaseActivity, SkillDefinition, skillGovernanceTags, stageLabel, tasksForAsset } from '../managementData';
import { LifecycleOverviewPanel, PageHeader, PrototypeToast, StatusBadge } from '../components/ManagementUi';

type Props = {
  skill: SkillDefinition;
  tasks: OperationsTask[];
  recentActivities: ReleaseActivity[];
  onNavigate: (path: string) => void;
  onUpdate: (skill: SkillDefinition) => void;
  onSubmitGovernance: (skill: SkillDefinition) => void;
};

export function SkillDetailPage({ skill, tasks, recentActivities, onNavigate, onUpdate, onSubmitGovernance }: Props) {
  const [toast, setToast] = useState('');
  const [skillPrompt, setSkillPrompt] = useState(skill.tagline || skill.description);
  const [draftGenerated, setDraftGenerated] = useState(true);
  const [testInput, setTestInput] = useState(skill.examples[0] || '');
  const [testResult, setTestResult] = useState('');
  const [testAuditTrail, setTestAuditTrail] = useState<string[]>([]);
  const [showTechnicalPreview, setShowTechnicalPreview] = useState(false);
  const governance = skillGovernanceTags[skill.name];
  const relatedTasks = useMemo(() => tasksForAsset('skill', skill.name, skill.displayName, tasks), [tasks, skill.name, skill.displayName]);
  const primaryMcp = skill.mcpTools[0] || 'llm';
  const isActionSkill = Boolean(governance?.writesData || skill.category.includes('流程') || skill.requirements?.some((item) => item.includes('OA')));
  const failureSummary = relatedTasks.find((task) => task.type === 'skill')?.failureReason || relatedTasks.find((task) => task.type === 'skill')?.blockedBy;
  const currentStage = lifecycleStageForReleaseStatus(skill.releaseStatus, failureSummary);
  const currentStageAction = lifecycleActionByStage[currentStage];
  const stageSteps: LifecycleStage[] = ['draft', 'testing', 'review', 'publish'];
  const summaryItems = [
    { label: '当前阶段', value: stageLabel[currentStage], description: currentStageAction },
    {
      label: '影响组织与风险提示',
      value: governance?.applicableOrganizations.join(' / ') || '待配置组织范围',
      description: `${governance?.requiresApproval ? '需组织审批' : '标准授权'} · ${governance?.writesData ? '包含写入动作' : '只读能力'}`,
    },
    { label: '依赖状态', value: skill.mcpTools.join(' / '), description: '依赖 MCP 会在测试阶段自动暴露失败定位。' },
    { label: '发布前治理配置', value: '运行与权限辅助区', description: '上线前再配置组织授权、角色模板和审计策略。' },
  ];
  const focusAreas = [
    { label: '测试', value: '示例输入与结果回放', description: '在当前页直接运行示例问题、查看结果和失败定位。' },
    { label: '提审资料', value: '差异摘要与风险说明', description: '提交前确认作用说明、适用组织、依赖影响和审核反馈。' },
    { label: '发布检查清单', value: '版本差异 / 回滚预案', description: '审核通过后在当前页完成发布确认，不再跨页跳转。' },
    { label: '运行记录', value: `${recentActivities.length} 条最近动作`, description: '回看提交治理、审核、发布和依赖变化。' },
  ];

  const notify = (text: string) => { setToast(text); window.setTimeout(() => setToast(''), 2200); };

  const generateDraft = () => {
    setDraftGenerated(true);
    onUpdate({
      ...skill,
      tagline: skillPrompt,
      examples: testInput ? Array.from(new Set([testInput, ...skill.examples])) : skill.examples,
      updatedAt: '刚刚',
    });
    notify('大模型已生成 Skill 草案');
  };

  const runTest = () => {
    const testedQuestion = testInput || skill.examples[0] || skillPrompt;
    if (isActionSkill) {
      setTestResult(`系统已按“${testedQuestion}”模拟执行 ${skill.displayName}，先补齐必填字段，再命中审批规则与二次确认，最后演示提交流程失败后的自动回退。`);
      setTestAuditTrail([
        '审批命中：识别到这是动作型 Skill，需检查组织授权和审批人配置。',
        '二次确认：已展示提交对象、影响范围和审批路径，等待用户确认。',
        '失败回退：模拟 OA 提交超时，系统自动保留草稿并提示补提。',
        '审计输出：审批命中、确认时间和回退原因已写入治理日志。',
      ]);
    } else {
      setTestResult(`测试通过：系统已按“${testedQuestion}”模拟执行 ${skill.displayName}，完成意图识别、依赖工具调用和结果生成。`);
      setTestAuditTrail([]);
    }
    notify('一键测试完成');
  };

  return <section className="management-page detail-page">
    <button className="back-link" type="button" onClick={() => onNavigate('/admin/assets')}>← 返回统一目录</button>
    <PageHeader
      eyebrow={skill.category}
      title={skill.displayName}
      description="单详情页推进测试 → 提审 → 发布；把当前阶段主操作、依赖和治理提示放在同一页里。"
      actions={<><StatusBadge status={skill.status} /><button className="secondary-action" type="button" onClick={() => setShowTechnicalPreview((value) => !value)}>{showTechnicalPreview ? '收起技术预览' : '查看技术预览'}</button><button className="primary-action" type="button" onClick={() => { onSubmitGovernance(skill); notify('已提交治理流程，等待人工复核'); }}>提交治理</button></>}
    />

    <div className="skill-simple-layout">
      {/* 阶段状态 / 当前阶段主操作 / 影响组织与风险提示由 LifecycleOverviewPanel 统一渲染 */}
      <LifecycleOverviewPanel
        summaryTitle="影响组织与风险提示"
        summaryDescription="组织与权限从开发主流程降级为只读提示，真正的授权配置放到发布前治理配置中处理。"
        currentStage={currentStage}
        currentStageAction={currentStageAction}
        summaryItems={summaryItems}
        stageSteps={stageSteps}
        focusAreas={focusAreas}
      />

      <section className="panel-card skill-prompt-builder">
        <div className="section-toolbar">
          <div>
            <span>STEP 1</span>
            <h3>描述你想做什么 Skill</h3>
            <p>不用先写技术字段或工作流。把业务目标说清楚，剩下交给大模型生成。</p>
          </div>
          <button className="primary-action" type="button" onClick={generateDraft}>让大模型生成</button>
        </div>
        <textarea value={skillPrompt} onChange={(event) => setSkillPrompt(event.target.value)} placeholder="例如：我想做一个可以查询海外销量、生成趋势图，并解释异常波动原因的 Skill。" />
      </section>

      <section className="panel-card skill-generated-draft">
        <div className="section-toolbar">
          <div>
            <span>STEP 2</span>
            <h3>AI 生成 Skill 草案</h3>
            <p>这里只展示用户能判断的结果：这个 Skill 做什么、适合谁用、需要哪些权限。</p>
          </div>
        </div>
        <div className="generated-summary-grid">
          <div><span>生成的 Skill 草案</span><strong>业务能力说明</strong><p>{draftGenerated ? skillPrompt : skill.description}</p></div>
          <div><span>适用组织</span><strong>{governance?.applicableOrganizations.join(' / ') || '待组织授权确认'}</strong><p>后续由组织与权限页控制开通范围。</p></div>
          <div><span>数据域权限</span><strong>{skill.requirements?.join(' / ') || '无额外数据域'}</strong><p>需要访问的数据域会进入授权审核。</p></div>
          <div><span>动作权限</span><strong>{governance?.writesData ? '包含写入动作' : '仅查询与分析'}</strong><p>{governance?.requiresApproval ? '需要组织审批后才能使用。' : '标准授权即可使用。'}</p></div>
        </div>
      </section>

      <section className="panel-card skill-simple-test">
        <div className="section-toolbar">
          <div>
            <span>STEP 3</span>
            <h3>测试这个 Skill</h3>
            <p>输入一个用户真实会问的问题，直接看大模型生成的 Skill 能不能跑通。</p>
          </div>
          <button className="primary-action" type="button" onClick={runTest}>运行测试</button>
        </div>
        <div className="simple-test-grid">
          <label>
            <span>测试问题</span>
            <textarea value={testInput} onChange={(event) => setTestInput(event.target.value)} placeholder="输入一句真实业务问题" />
          </label>
          <div className="test-output simple-test-result">
            <h3>测试结果</h3>
            {testResult ? <>
              <span className="result-success">✓ 执行成功</span>
              <p>{testResult}</p>
              {isActionSkill && <div className="test-guard-grid">
                <div><span>审批命中</span><strong className="test-guard-status">已识别动作型 Skill</strong><p>提交前先校验组织授权、审批模式和动作权限。</p></div>
                <div><span>二次确认</span><strong className="test-guard-status">等待用户确认</strong><p>展示请假区间、审批人和影响范围，再允许继续提交。</p></div>
                <div><span>失败回退</span><strong className="test-guard-status">已保留草稿</strong><p>外部流程失败时自动回退，不直接丢失用户输入。</p></div>
                <div><span>审计输出</span><strong className="test-guard-status">已写入治理日志</strong><p>{testAuditTrail.join(' ')}</p></div>
              </div>}
            </> : <div className="empty-console">等待一键测试</div>}
          </div>
        </div>
      </section>

      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <span>RECENT</span>
            <h3>最近治理记录</h3>
            <p>查看最近提交治理、发布或其他关键动作，方便回看当前版本状态。</p>
          </div>
        </div>
        <div className="release-diff-list">
          {recentActivities.length ? recentActivities.map((item) => <span key={item.id}>{item.detail}</span>) : <span>暂无治理动作</span>}
        </div>
      </section>

      {showTechnicalPreview && <section className="panel-card skill-technical-preview">
        <div className="section-toolbar">
          <div>
            <span>OPTIONAL</span>
            <h3>技术预览</h3>
            <p>给开发和运维看的底层信息，普通用户不需要先理解这些。</p>
          </div>
          <button className="secondary-action" type="button" onClick={() => onNavigate(`/admin/mcps/${primaryMcp}`)}>查看依赖 MCP</button>
        </div>
        <div className="tech-preview-grid">
          <div><span>依赖 MCP</span>{skill.mcpTools.map((mcpName) => <button type="button" key={mcpName} onClick={() => onNavigate(`/admin/mcps/${mcpName}`)}>{mcpName} ↗</button>)}</div>
          <div><span>自动编排步骤</span>{skill.steps.map((step, index) => <p key={step.name}>{index + 1}. {step.description}</p>)}</div>
          <div><span>治理任务</span>{relatedTasks.length > 0 ? relatedTasks.map((task) => <p key={task.id}>{task.title}</p>) : <p>暂无阻塞任务</p>}</div>
        </div>
      </section>}
    </div>

    <PrototypeToast text={toast} />
  </section>;
}
