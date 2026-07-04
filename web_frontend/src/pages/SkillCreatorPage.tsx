import { useMemo, useState } from 'react';
import { OrganizationAccessProfile } from '../managementData';
import { PageHeader } from '../components/ManagementUi';

type SkillDraftPayload = {
  name: string;
  displayName: string;
  description: string;
  category: string;
  outputType: string;
  applicableOrganizations: string[];
  requiresApproval: boolean;
  writesData: boolean;
};

type Props = {
  organizations: OrganizationAccessProfile[];
  onNavigate: (path: string) => void;
  onCreate: (payload: SkillDraftPayload) => void | Promise<void>;
};

export function SkillCreatorPage({ organizations, onNavigate, onCreate }: Props) {
  const [displayName, setDisplayName] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('数据分析');
  const [outputType, setOutputType] = useState('分析报告');
  const [goal, setGoal] = useState('');
  const [selectedOrganizations, setSelectedOrganizations] = useState<string[]>(organizations.slice(0, 2).map((item) => item.organizationName));
  const [writesData, setWritesData] = useState(false);
  const [requiresApproval, setRequiresApproval] = useState(true);
  const [generated, setGenerated] = useState(false);

  const canGenerate = displayName.trim() && name.trim() && goal.trim();
  const previewSummary = useMemo(() => ({
    description: goal.trim() || '等待输入业务目标',
    organizations: selectedOrganizations.length ? selectedOrganizations.join(' / ') : '待指定试点组织',
    dataScope: writesData ? '需要写入动作审批和失败回溯' : '默认只读查询与分析链路',
    approval: requiresApproval ? '需组织审批后开通' : '标准授权后即可试点',
  }), [goal, selectedOrganizations, writesData, requiresApproval]);

  const toggleOrganization = (organizationName: string) => {
    setSelectedOrganizations((items) => items.includes(organizationName)
      ? items.filter((item) => item !== organizationName)
      : [...items, organizationName]);
  };

  const submit = async () => {
    if (!canGenerate) return;
    await onCreate({
      name: name.trim(),
      displayName: displayName.trim(),
      description: goal.trim(),
      category,
      outputType,
      applicableOrganizations: selectedOrganizations,
      requiresApproval,
      writesData,
    });
  };

  return <section className="management-page detail-page">
    <button className="back-link" type="button" onClick={() => onNavigate('/admin/assets')}>← 返回统一目录</button>
    <PageHeader
      eyebrow="Skill Creation"
      title="新建 Skill 向导"
      description="先把业务目标、适用组织和权限边界说清楚，再生成可进入治理流程的 Skill 草案。"
    />

    <div className="creator-shell">
      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <span>STEP 1</span>
            <h3>描述业务目标</h3>
            <p>面向平台管理员和 AI 开发者，先定义能力名称、标识、适用场景和输出形态。</p>
          </div>
          <button className="primary-action" type="button" onClick={() => setGenerated(true)} disabled={!canGenerate}>生成 Skill 草案</button>
        </div>
        <div className="creator-form-grid">
          <label>
            <span>能力名称</span>
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="例如：海外政策追踪" />
          </label>
          <label>
            <span>能力标识</span>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="例如：global_policy_watch" />
          </label>
          <label>
            <span>能力分类</span>
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option>数据分析</option>
              <option>政策分析</option>
              <option>流程办理</option>
              <option>知识问答</option>
            </select>
          </label>
          <label>
            <span>输出形态</span>
            <input value={outputType} onChange={(event) => setOutputType(event.target.value)} placeholder="例如：摘要 / 时间线 / 风险提示" />
          </label>
        </div>
        <label className="creator-textarea">
          <span>业务目标</span>
          <textarea value={goal} onChange={(event) => setGoal(event.target.value)} placeholder="例如：追踪海外新能源汽车政策变化，提取法规更新时间、适用市场、影响车型和需要跟进的动作建议。" />
        </label>
      </section>

      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <span>STEP 2</span>
            <h3>组织与权限范围</h3>
            <p>这里不暴露底层编排细节，只先定义谁能用、是否涉及写入动作，以及是否需要审批。</p>
          </div>
        </div>
        <div className="creator-choice-grid">
          <div>
            <span>试点组织</span>
            <div className="creator-chip-grid">
              {organizations.map((organization) => <button key={organization.organizationName} type="button" className={selectedOrganizations.includes(organization.organizationName) ? 'active' : ''} onClick={() => toggleOrganization(organization.organizationName)}>{organization.organizationName}</button>)}
            </div>
          </div>
          <div>
            <span>动作属性</span>
            <div className="creator-toggle-row">
              <button type="button" className={!writesData ? 'active' : ''} onClick={() => setWritesData(false)}>只读分析</button>
              <button type="button" className={writesData ? 'active' : ''} onClick={() => setWritesData(true)}>包含写入动作</button>
            </div>
          </div>
          <div>
            <span>审批模式</span>
            <div className="creator-toggle-row">
              <button type="button" className={requiresApproval ? 'active' : ''} onClick={() => setRequiresApproval(true)}>需组织审批</button>
              <button type="button" className={!requiresApproval ? 'active' : ''} onClick={() => setRequiresApproval(false)}>标准授权</button>
            </div>
          </div>
        </div>
      </section>

      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <span>STEP 3</span>
            <h3>草案预览</h3>
            <p>生成后会直接进入 Skill 编排详情页，继续测试示例问题和补充技术预览。</p>
          </div>
          <button className="primary-action" type="button" onClick={submit} disabled={!generated || !canGenerate}>创建并进入编排</button>
        </div>
        <div className="creator-preview-grid">
          <div><span>业务能力说明</span><strong>{displayName || '待命名 Skill'}</strong><p>{previewSummary.description}</p></div>
          <div><span>适用组织</span><strong>{previewSummary.organizations}</strong><p>创建后可在组织与权限页继续细化授权。</p></div>
          <div><span>数据与动作边界</span><strong>{previewSummary.dataScope}</strong><p>高风险动作默认会进入平台审计视图。</p></div>
          <div><span>开通方式</span><strong>{previewSummary.approval}</strong><p>适合先做原型验证，再进入正式发布流程。</p></div>
        </div>
      </section>
    </div>
  </section>;
}
