import { useMemo, useState } from 'react';
import { SkillDefinition } from '../managementData';
import { PageHeader } from '../components/ManagementUi';

type McpDraftPayload = {
  name: string;
  displayName: string;
  description: string;
  category: string;
  source: string;
  writesData: boolean;
  targetSystem: string;
};

type Props = {
  skills: SkillDefinition[];
  onNavigate: (path: string) => void;
  onCreate: (payload: McpDraftPayload) => void | Promise<void>;
};

export function McpCreatorPage({ skills, onNavigate, onCreate }: Props) {
  const [displayName, setDisplayName] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Retrieval');
  const [source, setSource] = useState('外部服务');
  const [targetSystem, setTargetSystem] = useState('');
  const [description, setDescription] = useState('');
  const [writesData, setWritesData] = useState(false);
  const [generated, setGenerated] = useState(false);

  const relatedSkills = useMemo(
    () => skills.filter((skill) => skill.category.includes('数据') || skill.category.includes('分析')).slice(0, 3),
    [skills],
  );
  const canGenerate = displayName.trim() && name.trim() && description.trim() && targetSystem.trim();

  const submit = async () => {
    if (!canGenerate) return;
    await onCreate({
      name: name.trim(),
      displayName: displayName.trim(),
      description: description.trim(),
      category,
      source,
      writesData,
      targetSystem: targetSystem.trim(),
    });
  };

  return <section className="management-page detail-page">
    <button className="back-link" type="button" onClick={() => onNavigate('/admin/assets')}>← 返回统一目录</button>
    <PageHeader
      eyebrow="MCP Onboarding"
      title="接入 MCP 向导"
      description="定义连接对象、读写边界和预期依赖，让平台先形成可治理的接入草稿。"
    />

    <div className="creator-shell">
      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <span>STEP 1</span>
            <h3>录入连接信息</h3>
            <p>先说清楚这个 MCP 连接什么系统、做什么事情、面向哪类调用场景。</p>
          </div>
          <button className="primary-action" type="button" onClick={() => setGenerated(true)} disabled={!canGenerate}>生成接入草案</button>
        </div>
        <div className="creator-form-grid">
          <label>
            <span>MCP 名称</span>
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="例如：政策源连接器" />
          </label>
          <label>
            <span>MCP 标识</span>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="例如：policy_feed_connector" />
          </label>
          <label>
            <span>工具分类</span>
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option>Retrieval</option>
              <option>Database</option>
              <option>Utility</option>
              <option>Workflow</option>
            </select>
          </label>
          <label>
            <span>接入来源</span>
            <select value={source} onChange={(event) => setSource(event.target.value)}>
              <option>外部服务</option>
              <option>集团内部系统</option>
              <option>本地执行器</option>
            </select>
          </label>
          <label className="span-2">
            <span>目标系统</span>
            <input value={targetSystem} onChange={(event) => setTargetSystem(event.target.value)} placeholder="例如：海外法规聚合平台 / 集团政策库" />
          </label>
        </div>
        <label className="creator-textarea">
          <span>能力说明</span>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="例如：定时抓取海外政策变更，返回国家、法规主题、生效时间和原文链接。" />
        </label>
      </section>

      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <span>STEP 2</span>
            <h3>风险与引用面</h3>
            <p>把读写属性和可能影响的 Skill 范围先声明出来，方便后续灰度和审计。</p>
          </div>
        </div>
        <div className="creator-choice-grid">
          <div>
            <span>读写属性</span>
            <div className="creator-toggle-row">
              <button type="button" className={!writesData ? 'active' : ''} onClick={() => setWritesData(false)}>只读 / 查询</button>
              <button type="button" className={writesData ? 'active' : ''} onClick={() => setWritesData(true)}>读写受控</button>
            </div>
          </div>
          <div>
            <span>建议优先联调 Skill</span>
            <div className="creator-chip-grid static">
              {relatedSkills.map((skill) => <span key={skill.name}>{skill.displayName}</span>)}
            </div>
          </div>
        </div>
      </section>

      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <span>STEP 3</span>
            <h3>接入草案预览</h3>
            <p>创建后会进入 MCP 治理详情页，可以继续补连接配置、健康检查和发布节奏。</p>
          </div>
          <button className="primary-action" type="button" onClick={submit} disabled={!generated || !canGenerate}>创建并进入治理</button>
        </div>
        <div className="creator-preview-grid">
          <div><span>连接对象</span><strong>{targetSystem || '待指定目标系统'}</strong><p>{description || '等待补充能力说明'}</p></div>
          <div><span>分类与来源</span><strong>{category} / {source}</strong><p>后续可在治理页继续补健康检查与环境配置。</p></div>
          <div><span>读写风险</span><strong>{writesData ? '读写受控' : '只读 / 查询'}</strong><p>{writesData ? '需要审批、留痕和失败回溯。' : '适合先做查询型原型联调。'}</p></div>
          <div><span>首批联调范围</span><strong>{relatedSkills.map((skill) => skill.displayName).join(' / ') || '待指定 Skill'}</strong><p>先验证引用影响，再进入灰度发布。</p></div>
        </div>
      </section>
    </div>
  </section>;
}
