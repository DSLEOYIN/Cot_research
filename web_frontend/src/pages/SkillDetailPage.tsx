import { useMemo, useState } from 'react';
import { lifecycleActionByStage, lifecycleStageForReleaseStatus, LifecycleStage, OperationsTask, ReleaseActivity, SkillDefinition, skillGovernanceTags, stageLabel, tasksForAsset } from '../managementData';
import { DetailSummaryPanel, DetailTestPanel, LifecycleOverviewPanel, PageHeader, PrototypeToast, RecentActivityPanel, StageActionPanel, StatusBadge } from '../components/ManagementUi';

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
  const completenessChecks = [
    { label: '业务说明', value: skillPrompt.length > 16 ? '已补齐' : '待补充', description: '确认业务目标、使用场景和期望输出是否足够清晰。' },
    { label: '适用组织', value: governance?.applicableOrganizations.length ? '已补齐' : '待补充', description: '提审前需明确组织范围和授权边界。' },
    { label: '依赖 MCP', value: skill.mcpTools.length ? '已补齐' : '待补充', description: '检查测试阶段需要暴露的依赖调用和失败定位。' },
    { label: '风险说明', value: governance?.requiresApproval ? '已补齐' : '待确认', description: '动作权限、审批要求和回退策略会进入审核说明。' },
  ];
  const blockedGuidance = relatedTasks.find((task) => task.releaseStatus === 'blocked_by_dependency');
  const unblockGuidanceItems = blockedGuidance ? [
    { label: '当前阻塞', value: blockedGuidance.blockedBy || blockedGuidance.failureReason || '等待依赖解锁', description: '先明确外部依赖、白名单或提审资料缺口。' },
    { label: '建议动作', value: '转到运行与权限补齐治理配置', description: '优先核对组织授权、审批模式和账号级覆盖，再恢复测试。' },
    { label: '恢复条件', value: '依赖解锁后重新运行测试', description: '阻塞解除后回到当前页执行一键测试与提审。' },
  ] : [];

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
      {/* 阶段状态 / 当前阶段主操作 / 影响组织与风险提示由 LifecycleOverviewPanel 统一渲染；FocusAreaPanel 由该组件内部复用。 */}
      <LifecycleOverviewPanel
        summaryTitle="影响组织与风险提示"
        summaryDescription="组织与权限从开发主流程降级为只读提示，真正的授权配置放到发布前治理配置中处理。"
        currentStage={currentStage}
        currentStageAction={currentStageAction}
        summaryItems={summaryItems}
        stageSteps={stageSteps}
        focusAreas={focusAreas}
      />
      <StageActionPanel
        title="当前阶段操作"
        description="统一主操作密度：先在详情页完成测试或提审，再按需跳到治理配置辅助区。"
        primaryLabel="提交治理"
        onPrimary={() => { onSubmitGovernance(skill); notify('已提交治理流程，等待人工复核'); }}
        secondaryLabel="发布前治理配置"
        onSecondary={() => onNavigate(`/admin/operations-center?asset=skill:${skill.name}`)}
      />
      {currentStage === 'blocked' && blockedGuidance ? <DetailSummaryPanel
        title="解除阻塞引导"
        description="当前对象处于阻塞态，先处理依赖与治理配置，再恢复测试和提审。"
        items={unblockGuidanceItems}
      /> : null}

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

      <DetailSummaryPanel
        title="AI 生成 Skill 草案"
        description="这里只展示用户能判断的结果：这个 Skill 做什么、适合谁用、需要哪些权限。"
        items={[
          { label: '生成的 Skill 草案', value: '业务能力说明', description: draftGenerated ? skillPrompt : skill.description },
          { label: '适用组织', value: governance?.applicableOrganizations.join(' / ') || '待组织授权确认', description: '后续由组织与权限页控制开通范围。' },
          { label: '数据域权限', value: skill.requirements?.join(' / ') || '无额外数据域', description: '需要访问的数据域会进入授权审核。' },
          { label: '动作权限', value: governance?.writesData ? '包含写入动作' : '仅查询与分析', description: governance?.requiresApproval ? '需要组织审批后才能使用。' : '标准授权即可使用。' },
        ]}
      />

      <DetailSummaryPanel
        title="提审资料完整性检查"
        description="提交治理前先确认这几个必填项已经补齐，避免被退回补资料。"
        items={completenessChecks}
      />

      <DetailTestPanel title="测试这个 Skill" description="输入一个用户真实会问的问题，直接看大模型生成的 Skill 能不能跑通。" actionLabel="运行测试" onAction={runTest}>
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
      </DetailTestPanel>

      <RecentActivityPanel title="最近治理记录" description="查看最近提交治理、发布或其他关键动作，方便回看当前版本状态。" items={recentActivities.map((item) => ({ id: item.id, detail: item.detail }))} emptyText="暂无治理动作" />

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
