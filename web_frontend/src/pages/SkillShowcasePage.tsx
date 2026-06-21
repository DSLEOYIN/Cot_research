import { SkillDefinition } from '../managementData';

type Props = { skill: SkillDefinition; onNavigate: (path: string) => void; onInstall: (name: string) => void; onTry: (example: string) => void };

const requirementAction = (requirement: string) => {
  if (requirement.includes('数据库')) return '确认你的账号拥有业务数据库只读权限；没有权限时，请联系数据管理员开通。';
  if (requirement.includes('联网')) return '确认当前环境允许访问公开互联网；受限网络需要由系统管理员开启。';
  if (requirement.includes('历史')) return '确保数据库中已接入去年同期和上月同期数据，否则无法完成对比计算。';
  if (requirement.includes('知识库')) return '确认字段口径知识库已配置；如结果口径不清晰，请联系系统维护人员补充。';
  if (requirement.includes('上下文')) return '请先在同一对话中完成一次数据查询，再继续提出对比分析问题。';
  return '该能力由平台统一提供，安装后即可在智能问答中使用。';
};

export function SkillShowcasePage({ skill, onNavigate, onInstall, onTry }: Props) {
  const demoStages = ['识别问题与指标', '检索口径并查询数据', '计算结果并生成图表'];
  const installOrTrySkill = () => skill.installed ? onTry(skill.examples[0]) : onInstall(skill.name);

  return <section className="skill-showcase-page">
    <button className="back-link showcase-back" type="button" onClick={() => onNavigate('/skills/library')}>← 返回 Skill 商店</button>
    <section className="showcase-hero">
      <div className="showcase-icon">{skill.displayName.slice(0, 1)}</div>
      <div className="showcase-copy"><span>{skill.category} · 企业内部认证</span><h1>{skill.displayName}</h1><p>{skill.tagline}</p><div className="showcase-actions"><button className="primary-action" type="button" onClick={installOrTrySkill}>{skill.installed ? '立即体验' : '安装 Skill'}</button><button className="secondary-action" type="button" onClick={() => onTry(skill.examples[0])}>带着示例去提问</button>{skill.installed && <i>✓ 已安装到我的助手</i>}</div></div>
      <div className="showcase-result-card"><span>你将获得</span><strong>{skill.outputType}</strong><div className="mini-chart"><i /><i /><i /><i /><i /></div><p>自动完成分析，并给出可继续追问的结论。</p></div>
    </section>

    <section className="showcase-section"><div className="showcase-heading"><span>VALUE</span><h2>这个 Skill 能为你做什么</h2><p>直接说出业务问题，Skill 会自动选择步骤并交付结果。</p></div><div className="value-grid">{skill.outcomes?.map((item, index) => <article key={item}><b>0{index + 1}</b><h3>{item}</h3><p>无需理解底层工具或复杂配置，结果可以继续追问和用于汇报。</p></article>)}</div></section>

    <section className="showcase-section demo-section">
      <div className="showcase-heading"><span>LIVE CHATBI DEMO</span><h2>在真实问答页面中，它会这样工作</h2><p>下面演示从发送“{skill.examples[0]}”到获得分析结果的完整过程。</p></div>
      <div className="chat-demo-window">
        <aside className="chat-demo-sidebar"><div className="chat-demo-brand">C</div><strong>当前对话</strong><span>{skill.displayName}分析</span><span>业务数据问答</span></aside>
        <div className="chat-demo-main">
          <header><div><strong>ChatBI 智能问答</strong><span>已启用：{skill.displayName}</span></div><i>● 在线</i></header>
          <div className="chat-demo-conversation">
            <div className="chat-demo-message user">{skill.examples[0]}</div>
            <div className="chat-demo-message assistant">
              <div className="chat-demo-thinking">{demoStages.map((stage, index) => <div style={{ animationDelay: `${index * .8}s` }} key={stage}><i>{index + 1}</i><span>{stage}</span><b>完成</b></div>)}</div>
              <div className="chat-demo-result"><span>分析完成</span><strong>{skill.outcomes?.[3] || skill.outcomes?.[0]}</strong><p>结果已按业务口径完成计算，并定位了需要关注的变化。</p><div className="chat-demo-chart"><i /><i /><i /><i /><i /></div></div>
            </div>
          </div>
          <footer><span>继续追问这个结果...</span><button type="button" onClick={() => onTry(skill.examples[0])}>➤</button></footer>
        </div>
      </div>
    </section>

    <section className="showcase-section"><div className="showcase-heading"><span>USE CASES</span><h2>可以直接这样问</h2><p>点击案例，会带着问题进入智能问答页面。</p></div><div className="case-grid">{skill.examples.map((example, index) => <button type="button" key={example} onClick={() => onTry(example)}><span>案例 0{index + 1}</span><strong>{example}</strong><i>立即体验 →</i></button>)}</div></section>

    <section className="showcase-section io-section">
      <div className="showcase-heading"><span>EXAMPLES</span><h2>示例输入 / 输出</h2><p>帮助用户在安装前理解这个 Skill 会返回什么样的结果。</p></div>
      <div className="detail-grid">
        <article className="panel-card"><h3>示例输入</h3><p className="example-item">{skill.examples[0]}</p></article>
        <article className="panel-card"><h3>示例输出</h3><p className="example-item">{skill.exampleOutput || skill.outputType}</p></article>
      </div>
    </section>

    <section className="showcase-section">
      <div className="showcase-heading"><span>REQUIREMENTS</span><h2>所需能力</h2><p>这个 Skill 会调用平台里的底层能力，但不会暴露技术细节给普通用户。</p></div>
      <div className="value-grid">{skill.mcpTools.slice(0, 4).map((item, index) => <article key={item}><b>0{index + 1}</b><h3>{item}</h3><p>由平台统一维护和授权，安装启用后自动参与执行。</p></article>)}</div>
    </section>

    <section className="showcase-section">
      <div className="showcase-heading"><span>AFTER INSTALL</span><h2>安装后反馈</h2><p>帮助用户理解启用后的使用表现、版本信息和最近活跃度。</p></div>
      <div className="showcase-usage-grid">
        <article><span>版本信息</span><strong>{skill.publishedVersion || '--'} / {skill.latestVersion || '--'}</strong><p>前者为当前可用版本，后者为最新草案或更新版本。</p></article>
        <article><span>最近活跃度</span><strong>{skill.usageCount30d || 0} 次</strong><p>最近 30 天的调用次数，用来判断是否值得保持启用。</p></article>
        <article><span>使用反馈</span><strong>{skill.successRate || '--'}</strong><p>最近 30 天成功率，帮助用户识别是否需要升级或停用。</p></article>
      </div>
    </section>

    <section className="showcase-requirements">
      <div className="requirements-intro"><span>BEFORE YOU START</span><h2>安装前检查</h2><p>完成下面检查后，这个 Skill 才能正确访问所需数据并返回结果。安装后需启用，才会在智能问答里参与路由。</p><button className="primary-action" type="button" onClick={installOrTrySkill}>{skill.installed ? '进入智能问答体验' : '安装到我的助手'}</button></div>
      <div className="requirement-check-list">{skill.requirements?.map((item) => <article className="requirement-check-card" key={item}><i>✓</i><div><strong>{item}</strong><span>需要你做什么</span><p>{requirementAction(item)}</p></div></article>)}</div>
    </section>
  </section>;
}
