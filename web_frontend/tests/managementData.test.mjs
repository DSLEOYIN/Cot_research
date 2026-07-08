import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  buildLifecycleMetrics,
  buildUnifiedAssets,
  countTasksByLifecycleStage,
  lifecycleStageForReleaseStatus,
  resolveActivityRoute,
  resolveTaskRoute,
  taskLifecycleStage,
  tasksForAsset,
} from '../.tmp/management-data-test/managementData.js';

const baseTask = {
  id: 'task-001',
  title: '生成渠道库存诊断 Skill',
  type: 'skill',
  entityName: 'channel_inventory_diagnosis',
  priority: 'P0',
  stage: 'blocked_by_dependency',
  releaseStatus: 'blocked_by_dependency',
  owner: '运维-王敏',
  updatedAt: '今天 10:42',
  summary: '等待依赖 MCP 发布后继续联调测试。',
  blockedBy: '依赖 MCP `inventory_snapshot_mcp` 尚未发布',
  autoTestPassRate: '4/6',
};

const skill = (name, displayName, releaseStatus) => ({
  name,
  displayName,
  description: `${displayName} 描述`,
  category: '测试分类',
  outputType: '测试输出',
  status: 'draft',
  releaseStatus,
  mcpTools: [],
  steps: [],
  examples: [],
  updatedAt: '刚刚',
});

const mcp = (name, displayName, releaseStatus) => ({
  name,
  displayName,
  description: `${displayName} 描述`,
  category: 'Database',
  status: 'draft',
  releaseStatus,
  health: 'unchecked',
  latency: '--',
  source: '测试',
  config: [],
  schema: {},
  updatedAt: '刚刚',
});

describe('management lifecycle utilities', () => {
  it('maps release status and failure context to lifecycle stage', () => {
    assert.equal(lifecycleStageForReleaseStatus('draft'), 'draft');
    assert.equal(lifecycleStageForReleaseStatus('testing'), 'testing');
    assert.equal(lifecycleStageForReleaseStatus('ready_for_review'), 'review');
    assert.equal(lifecycleStageForReleaseStatus('review_approved'), 'review');
    assert.equal(lifecycleStageForReleaseStatus('ready_to_publish'), 'publish');
    assert.equal(lifecycleStageForReleaseStatus('published'), 'published');
    assert.equal(lifecycleStageForReleaseStatus('blocked_by_dependency'), 'blocked');
    assert.equal(lifecycleStageForReleaseStatus('blocked_by_dependency', '自动测试失败'), 'review_rejected');
  });

  it('derives task stage from failure reason before blocked reason', () => {
    assert.equal(taskLifecycleStage({ releaseStatus: 'blocked_by_dependency', blockedBy: '依赖未发布' }), 'review_rejected');
    assert.equal(taskLifecycleStage({ releaseStatus: 'ready_to_publish' }), 'publish');
    assert.equal(countTasksByLifecycleStage([
      { releaseStatus: 'testing' },
      { releaseStatus: 'ready_for_review' },
      { releaseStatus: 'ready_to_publish' },
    ], 'review'), 1);
  });

  it('includes child MCP tasks when resolving Skill task context', () => {
    const childTask = {
      ...baseTask,
      id: 'task-002',
      type: 'mcp',
      entityName: 'inventory_snapshot_mcp',
      parentTaskId: 'task-001',
      title: '生成库存快照 MCP 子任务',
      releaseStatus: 'ready_for_review',
      stage: 'ready_for_review',
      blockedBy: undefined,
    };

    const skillTasks = tasksForAsset('skill', 'channel_inventory_diagnosis', '渠道库存诊断', [baseTask, childTask]);
    const mcpTasks = tasksForAsset('mcp', 'inventory_snapshot_mcp', '库存快照 MCP', [baseTask, childTask]);

    assert.deepEqual(skillTasks.map((task) => task.id), ['task-001', 'task-002']);
    assert.deepEqual(mcpTasks.map((task) => task.id), ['task-002']);
  });

  it('builds lifecycle metrics and sorts actionable unified assets first', () => {
    const assets = buildUnifiedAssets();

    assert.equal(assets[0].type, 'mcp');
    assert.equal(assets[0].name, 'text_analysis');
    assert.equal(assets[0].lifecycleStage, 'review_rejected');
    assert.equal(assets[1].type, 'skill');
    assert.equal(assets[1].name, 'channel_inventory_diagnosis');
    assert.equal(assets[1].lifecycleStage, 'review_rejected');
    assert.equal(assets[2].lifecycleStage, 'testing');
    assert.equal(assets[3].name, 'inventory_snapshot_mcp');
    assert.equal(assets[3].lifecycleStage, 'review');
    assert.equal(assets[4].name, 'global_policy_watch');
    assert.equal(assets[4].lifecycleStage, 'publish');

    assert.deepEqual(buildLifecycleMetrics(assets), {
      total: assets.length,
      testing: assets.filter((asset) => asset.lifecycleStage === 'testing').length,
      review: assets.filter((asset) => asset.lifecycleStage === 'review').length,
      publish: assets.filter((asset) => asset.lifecycleStage === 'publish').length,
    });
  });

  it('sorts unified directory records by lifecycle stage, type, and Chinese display name', () => {
    const assets = buildUnifiedAssets(
      [
        skill('skill_publish', '乙发布 Skill', 'ready_to_publish'),
        skill('skill_review', '甲提审 Skill', 'ready_for_review'),
        skill('skill_alpha', '阿尔法 Skill', 'published'),
        skill('skill_beta', '贝塔 Skill', 'published'),
      ],
      [
        mcp('mcp_review', '乙提审 MCP', 'ready_for_review'),
        mcp('mcp_published', '甲发布 MCP', 'published'),
      ],
      [],
    );

    assert.deepEqual(assets.map((asset) => `${asset.lifecycleStage}:${asset.type}:${asset.displayName}`), [
      'review:mcp:乙提审 MCP',
      'review:skill:甲提审 Skill',
      'publish:skill:乙发布 Skill',
      'published:mcp:甲发布 MCP',
      'published:skill:阿尔法 Skill',
      'published:skill:贝塔 Skill',
    ]);
  });

  it('resolves workbench task and activity routes to stable asset detail pages', () => {
    const assets = [
      { type: 'skill', name: 'channel_inventory_diagnosis', displayName: '渠道库存诊断', route: '/admin/skills/channel_inventory_diagnosis' },
      { type: 'mcp', name: 'inventory_snapshot_mcp', displayName: '库存快照 MCP', route: '/admin/mcps/inventory_snapshot_mcp' },
    ];
    const skills = [{ name: 'channel_inventory_diagnosis', displayName: '渠道库存诊断' }];
    const mcps = [{ name: 'inventory_snapshot_mcp', displayName: '库存快照 MCP' }];

    assert.equal(resolveTaskRoute({ type: 'skill', entityName: '渠道库存诊断', title: '生成渠道库存诊断 Skill' }, skills, mcps), '/admin/skills/channel_inventory_diagnosis');
    assert.equal(resolveTaskRoute({ type: 'mcp', entityName: 'inventory_snapshot_mcp', title: '生成库存快照 MCP 子任务' }, skills, mcps), '/admin/mcps/inventory_snapshot_mcp');
    assert.equal(resolveTaskRoute({ type: 'skill', entityName: 'unknown', title: '未知任务' }, skills, mcps), '/admin/assets');
    assert.equal(resolveActivityRoute({ entityType: 'skill', entityName: '渠道库存诊断' }, assets), '/admin/skills/channel_inventory_diagnosis');
    assert.equal(resolveActivityRoute({ entityType: 'mcp', entityName: '缺失对象' }, assets), '/admin/assets');
  });
});
