# Skill Step 1 Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current all-at-once guided-flow content in the Skill detail page with a clickable Step 1 clarification wizard that starts from one sentence, asks 2 to 3 mocked follow-up questions, and ends in an editable structured summary.

**Architecture:** Keep all changes inside the frontend prototype. Refactor only the `引导流程` tab in `SkillDetailPage.tsx`, drive the conversation with local React state and keyword-based mock branches, and preserve the existing `工作流` / `Schema` / `测试` tabs unchanged.

**Tech Stack:** React 18, TypeScript, Vite, CSS, Python contract tests

---

### Task 1: Lock The New Step 1 Contract In Tests

**Files:**
- Modify: `/Users/leo/work/ai_model/Cot_research/tests/test_web_frontend_contract.py`
- Verify against: `/Users/leo/work/ai_model/Cot_research/web_frontend/src/pages/SkillDetailPage.tsx`

- [ ] **Step 1: Write the failing test expectations for the new wizard copy**

Add or update the existing Skill detail contract test so it asserts the new Step 1 markers instead of the old four-step explainer markers.

```python
def test_skill_management_has_search_workflow_schema_and_test_console():
    listing = read(SRC / "pages" / "SkillsPage.tsx")
    detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    data = read(SRC / "managementData.ts")

    assert "Skill 管理" in listing
    assert "搜索 Skill" in listing
    assert "新建 Skill" in listing
    assert "skill-card" in listing
    assert "工作流" in detail
    assert "Schema" in detail
    assert "测试" in detail
    assert "一句话描述你想做的 Skill" in detail
    assert "确认需求并生成草案" in detail
    assert "目标场景" in detail
    assert "预期输出" in detail
    assert "添加步骤" in detail
    assert "运行测试" in detail
    assert "data_web_compare_analysis" in data
    assert "mcpTools" in data
```

- [ ] **Step 2: Run the targeted contract test and verify it fails**

Run:

```bash
python3 -m pytest /Users/leo/work/ai_model/Cot_research/tests/test_web_frontend_contract.py -k skill_management_has_search_workflow_schema_and_test_console -v
```

Expected: FAIL because the new Step 1 strings do not yet exist in `SkillDetailPage.tsx`.

- [ ] **Step 3: Commit nothing yet**

Do not implement or stage code in this task. The goal is only to create the red test for the new UI contract.

### Task 2: Replace The Guided Flow With A Mocked Clarification Wizard

**Files:**
- Modify: `/Users/leo/work/ai_model/Cot_research/web_frontend/src/pages/SkillDetailPage.tsx`
- Reference: `/Users/leo/work/ai_model/Cot_research/web_frontend/src/managementData.ts`

- [ ] **Step 1: Add local state for the Step 1 wizard**

Introduce local state for:

- the initial user request text
- current wizard phase (`draft`, `clarifying`, `summary`, `ready`)
- the selected mock branch
- the current follow-up question index
- collected follow-up answers
- editable summary fields

Use a compact typed shape like this:

```tsx
type WizardBranch = 'data_query' | 'diagnostic' | 'web_compare';

type WizardSummary = {
  intent: string;
  scenarios: string;
  output: string;
  dependencies: string;
};

const [wizardInput, setWizardInput] = useState(skill.description);
const [wizardPhase, setWizardPhase] = useState<'draft' | 'clarifying' | 'summary' | 'ready'>('draft');
const [wizardBranch, setWizardBranch] = useState<WizardBranch>('data_query');
const [wizardQuestionIndex, setWizardQuestionIndex] = useState(0);
const [wizardAnswers, setWizardAnswers] = useState<string[]>([]);
const [wizardReply, setWizardReply] = useState('');
const [wizardSummary, setWizardSummary] = useState<WizardSummary>({
  intent: skill.tagline || skill.description,
  scenarios: skill.scenes?.join(' / ') || '',
  output: skill.expectedOutput?.join(' / ') || skill.outputType,
  dependencies: skill.mcpTools.join(' / '),
});
```

- [ ] **Step 2: Add a small mock branching model and summary builder**

Create in-file helper constants or functions for three mocked branches:

```tsx
const WIZARD_BRANCHES = {
  data_query: {
    questions: ['你主要想让这个 Skill 查哪些业务数据？', '结果更偏表格、摘要，还是口径说明？'],
    summary: (input: string, answers: string[]) => ({
      intent: `围绕${input}提供内部业务查询与基础解读能力`,
      scenarios: answers[0] || '销量、库存、订单等内部经营查询',
      output: answers[1] || '结构化数据表 + 简短业务解读',
      dependencies: 'knowledge_retrieval / sql_executor / llm',
    }),
  },
  diagnostic: {
    questions: ['你希望它判断什么问题或异常？', '最后是给结论、原因，还是行动建议？'],
    summary: (input: string, answers: string[]) => ({
      intent: `围绕${input}提供诊断分析与异常定位能力`,
      scenarios: answers[0] || '经营异常、波动归因、问题定位',
      output: answers[1] || '诊断结论 + 关键原因 + 建议动作',
      dependencies: 'knowledge_retrieval / sql_executor / llm',
    }),
  },
  web_compare: {
    questions: ['你要对比的外部对象或市场范围是什么？', '你更关心趋势结论、资料摘要，还是对比表？'],
    summary: (input: string, answers: string[]) => ({
      intent: `围绕${input}提供内部数据结合外部公开信息的对比分析能力`,
      scenarios: answers[0] || '国际市场、竞品、外部趋势对比',
      output: answers[1] || '对比摘要 + 外部信息引用 + 结论说明',
      dependencies: 'web_search / knowledge_retrieval / llm',
    }),
  },
} as const;
```

Add a simple classifier:

```tsx
const detectWizardBranch = (text: string): WizardBranch => {
  if (/对比|外部|竞品|市场/.test(text)) return 'web_compare';
  if (/诊断|分析|原因|异常|归因/.test(text)) return 'diagnostic';
  return 'data_query';
};
```

- [ ] **Step 3: Replace the current `引导流程` tab body with the new wizard layout**

Remove the current four stacked guided-flow sections and render a single progressive Step 1 layout:

- initial prompt card with one input and sample hints
- clarification conversation card when the flow starts
- editable summary card when enough answers are collected
- final CTA `确认需求并生成草案`

Preserve the page header, tab strip, toast behavior, and all non-`引导流程` tabs.

The layout should include these literal UI markers:

```tsx
<h3>先用一句话描述你想做的 Skill</h3>
<button className="primary-action" type="button">开始澄清需求</button>
<h3>AI 正在帮你补齐关键信息</h3>
<h3>已整理为结构化需求草案</h3>
<button className="primary-action" type="button">确认需求并生成草案</button>
```

- [ ] **Step 4: Implement the wizard transitions with minimal event handlers**

Add handlers for:

- starting the wizard
- submitting one follow-up answer
- moving from clarification to summary after enough answers
- editing summary fields
- clicking the final confirmation CTA

Use simple logic like:

```tsx
const startWizard = () => {
  const branch = detectWizardBranch(wizardInput);
  setWizardBranch(branch);
  setWizardAnswers([]);
  setWizardReply('');
  setWizardQuestionIndex(0);
  setWizardPhase('clarifying');
};

const submitWizardReply = () => {
  const nextAnswers = [...wizardAnswers, wizardReply.trim()];
  const branchConfig = WIZARD_BRANCHES[wizardBranch];
  if (nextAnswers.length >= branchConfig.questions.length) {
    setWizardAnswers(nextAnswers);
    setWizardSummary(branchConfig.summary(wizardInput, nextAnswers));
    setWizardPhase('summary');
    setWizardReply('');
    return;
  }
  setWizardAnswers(nextAnswers);
  setWizardQuestionIndex(nextAnswers.length);
  setWizardReply('');
};

const confirmWizardSummary = () => {
  setWizardPhase('ready');
  notify('需求已确认，下一步将生成 Skill 草案');
};
```

- [ ] **Step 5: Run the targeted contract test and verify it passes**

Run:

```bash
python3 -m pytest /Users/leo/work/ai_model/Cot_research/tests/test_web_frontend_contract.py -k skill_management_has_search_workflow_schema_and_test_console -v
```

Expected: PASS.

### Task 3: Style The New Step 1 Flow And Verify The Frontend Build

**Files:**
- Modify: `/Users/leo/work/ai_model/Cot_research/web_frontend/src/styles/app.css`
- Verify with: `/Users/leo/work/ai_model/Cot_research/web_frontend/src/pages/SkillDetailPage.tsx`

- [ ] **Step 1: Add dedicated CSS for the wizard-first layout**

Add focused styles for the new Step 1 layout rather than trying to reuse the old four-step grid styles. Include classes such as:

```css
.skill-wizard-shell {}
.skill-wizard-stage {}
.skill-wizard-intro {}
.skill-wizard-conversation {}
.skill-wizard-message {}
.skill-wizard-summary {}
.skill-wizard-summary-grid {}
.skill-wizard-hint-row {}
.skill-wizard-ready {}
```

The styling goal is:

- clean initial state
- one main column for the conversation
- minimal side noise during clarification
- summary fields that feel editable and reviewable

- [ ] **Step 2: Run the frontend build to catch TypeScript or CSS integration issues**

Run:

```bash
cd /Users/leo/work/ai_model/Cot_research/web_frontend && npm run build
```

Expected: successful TypeScript build and Vite production build with no errors.

- [ ] **Step 3: Run the full frontend contract suite**

Run:

```bash
python3 -m pytest /Users/leo/work/ai_model/Cot_research/tests/test_web_frontend_contract.py -q
```

Expected: all frontend contract tests PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add /Users/leo/work/ai_model/Cot_research/tests/test_web_frontend_contract.py \
  /Users/leo/work/ai_model/Cot_research/web_frontend/src/pages/SkillDetailPage.tsx \
  /Users/leo/work/ai_model/Cot_research/web_frontend/src/styles/app.css \
  /Users/leo/work/ai_model/Cot_research/docs/superpowers/specs/2026-06-16-skill-step1-wizard-design.md \
  /Users/leo/work/ai_model/Cot_research/docs/superpowers/plans/2026-06-16-skill-step1-wizard.md
git commit -m "feat: prototype step-one skill wizard"
```

Expected: a single focused commit containing the Step 1 wizard prototype and its contract updates.
