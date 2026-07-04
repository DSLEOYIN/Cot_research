from __future__ import annotations

import asyncio
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat_repository import ChatRepository, DEFAULT_DB_PATH
from langgraph_cot import run_agent
from permission_repository import PermissionRepository
from registry_repository import RegistryRepository


DEFAULT_SESSION_TITLES = {"新对话", "新聊天"}
SESSION_TITLE_MAX_LENGTH = 20
SESSION_SUMMARY_MAX_LENGTH = 48
ANSWER_STREAM_DELAY_SECONDS = 0.024

PROTOTYPE_CAPABILITIES = [
    {
        "name": "data_query",
        "displayName": "数据查询与分析",
        "category": "数据分析",
        "description": "查询内部销量、库存、订单、达成率等业务数据，并生成解读与口径说明。",
        "outputType": "表格 / 图表 / 分析报告",
        "applicableOrganizations": ["广汽国际", "集团总部", "试点子公司"],
        "status": "published",
    },
    {
        "name": "data_web_compare_analysis",
        "displayName": "内部数据与联网分析",
        "category": "数据分析",
        "description": "查询内部真实业务数据，并结合公开市场和竞品信息完成综合分析。",
        "outputType": "内外部综合分析",
        "applicableOrganizations": ["广汽国际", "品牌与市场部"],
        "status": "published",
    },
    {
        "name": "yoy_yoy_analysis",
        "displayName": "同环比分析",
        "category": "数据分析",
        "description": "处理同比、环比、增长率和趋势变化分析。",
        "outputType": "分析报告 / 百分比",
        "applicableOrganizations": ["广汽国际", "销售管理部"],
        "status": "published",
    },
]

PROTOTYPE_ORGANIZATION_PROFILES = [
    {
        "id": "gac-international",
        "organizationName": "广汽国际",
        "roleName": "销售分析岗",
        "openSkills": ["数据查询与分析", "同环比分析", "内部数据与联网分析"],
        "dataDomains": ["销售", "库存"],
        "actionPermissions": ["查询", "下载"],
        "approvalMode": "部门管理员复核",
    },
    {
        "id": "gac-passenger-vehicle",
        "organizationName": "广汽乘用车",
        "roleName": "HR 管理员",
        "openSkills": ["智能问答", "制度问答", "请假申请"],
        "dataDomains": ["人力", "OA"],
        "actionPermissions": ["查询", "提交", "审批"],
        "approvalMode": "动作型能力二次确认",
    },
    {
        "id": "gac-headquarters",
        "organizationName": "集团总部",
        "roleName": "平台管理员",
        "openSkills": ["数据查询与分析", "同环比分析", "内部数据与联网分析"],
        "dataDomains": ["平台配置", "监控", "审计"],
        "actionPermissions": ["发布", "回滚", "授权"],
        "approvalMode": "高风险操作留痕审计",
    },
]

PROTOTYPE_ADMIN_SKILLS = [
    {
        **PROTOTYPE_CAPABILITIES[0],
        "businessDomain": "销售经营",
        "riskLevel": "中",
        "requiresApproval": True,
        "writesData": False,
        "mcpTools": ["llm", "knowledge_retrieval", "n2sql", "sql_executor"],
        "releaseStatus": "published",
    },
    {
        **PROTOTYPE_CAPABILITIES[1],
        "businessDomain": "市场分析",
        "riskLevel": "中",
        "requiresApproval": True,
        "writesData": False,
        "mcpTools": ["llm", "knowledge_retrieval", "n2sql", "sql_executor", "web_search"],
        "releaseStatus": "published",
    },
    {
        "name": "global_policy_watch",
        "displayName": "海外政策追踪",
        "category": "政策分析",
        "description": "追踪海外市场政策变化，并给出业务影响摘要。",
        "outputType": "政策摘要 / 风险提示",
        "applicableOrganizations": ["广汽国际", "集团总部"],
        "status": "draft",
        "businessDomain": "政策分析",
        "riskLevel": "中",
        "requiresApproval": True,
        "writesData": False,
        "mcpTools": ["web_search", "llm"],
        "releaseStatus": "ready_to_publish",
    },
]

PROTOTYPE_ADMIN_MCPS = [
    {
        "name": "sql_executor",
        "displayName": "SQL 执行器",
        "category": "Database",
        "description": "执行安全只读 SQL，并应用表白名单和最大行数限制。",
        "readWriteRisk": "只读查询型能力，需记录访问来源",
        "health": "healthy",
        "releaseStatus": "published",
        "referencedBy": ["数据查询与分析", "内部数据与联网分析", "同环比分析"],
    },
    {
        "name": "knowledge_retrieval",
        "displayName": "知识检索",
        "category": "Retrieval",
        "description": "从知识库检索表结构、字段标准和业务规则。",
        "readWriteRisk": "只读查询型能力，需记录访问来源",
        "health": "warning",
        "releaseStatus": "published",
        "referencedBy": ["数据查询与分析", "内部数据与联网分析"],
    },
    {
        "name": "inventory_snapshot_mcp",
        "displayName": "库存快照连接器",
        "category": "Database",
        "description": "生成渠道库存快照，并提供给 Skill 联调使用。",
        "readWriteRisk": "只读查询型能力，需记录访问来源",
        "health": "healthy",
        "releaseStatus": "ready_for_review",
        "referencedBy": ["渠道库存诊断"],
    },
]

PROTOTYPE_GOVERNANCE_TASKS = [
    {
        "id": "skill-task-001",
        "title": "生成渠道库存诊断 Skill",
        "type": "skill",
        "entityName": "channel_inventory_diagnosis",
        "priority": "P0",
        "stage": "blocked_by_dependency",
        "releaseStatus": "blocked_by_dependency",
        "owner": "运维-王敏",
        "updatedAt": "今天 10:42",
        "summary": "AI 已完成 Skill 流程草案，等待依赖 MCP 发布后继续联调测试。",
        "blockedBy": "依赖 MCP `inventory_snapshot_mcp` 尚未发布",
        "autoTestPassRate": "4/6",
        "failureReason": "Skill 集成测试被未发布 MCP 阻塞",
    },
    {
        "id": "mcp-task-014",
        "title": "生成库存快照 MCP 子任务",
        "type": "mcp",
        "entityName": "inventory_snapshot_mcp",
        "priority": "P1",
        "stage": "ready_for_review",
        "releaseStatus": "ready_for_review",
        "owner": "运维-王敏",
        "updatedAt": "今天 10:38",
        "summary": "已生成 Python 模块、inputSchema 与 mock 返回，自动测试通过。",
        "parentTaskId": "skill-task-001",
        "autoTestPassRate": "8/8",
        "reviewNotes": "重点确认返回结构命名是否与 Skill 编排一致。",
    },
    {
        "id": "skill-task-002",
        "title": "生成海外政策追踪 Skill",
        "type": "skill",
        "entityName": "global_policy_watch",
        "priority": "P1",
        "stage": "ready_to_publish",
        "releaseStatus": "ready_to_publish",
        "owner": "运维-李哲",
        "updatedAt": "今天 09:16",
        "summary": "审核通过，等待手动发布到集团能力目录。",
        "autoTestPassRate": "7/7",
        "reviewNotes": "已确认作用说明、流程和示例输入输出。",
    },
    {
        "id": "mcp-task-009",
        "title": "升级知识检索 MCP",
        "type": "mcp",
        "entityName": "knowledge_retrieval",
        "priority": "P0",
        "stage": "testing",
        "releaseStatus": "testing",
        "owner": "运维-陈雪",
        "updatedAt": "今天 08:54",
        "summary": "AI 正在根据失败日志自动修复重试，重点解决字段映射缺失。",
        "autoTestPassRate": "5/8",
        "failureReason": "字段映射缺失，导致示例 query 返回空结果。",
    },
]

PROTOTYPE_RELEASE_ACTIVITIES = [
    {
        "id": "release-001",
        "entityType": "skill",
        "entityName": "库存快照助手",
        "action": "submitted_for_review",
        "operator": "平台管理员",
        "detail": "已提交人工复核，等待确认业务口径与组织范围。",
        "createdAt": "2026-06-24T09:20:00+08:00",
    },
    {
        "id": "release-002",
        "entityType": "mcp",
        "entityName": "SQL 执行器",
        "action": "health_check_passed",
        "operator": "平台管理员",
        "detail": "健康检查通过，连接与 Schema 校验正常。",
        "createdAt": "2026-06-24T10:10:00+08:00",
    },
    {
        "id": "release-003",
        "entityType": "skill",
        "entityName": "海外政策追踪",
        "action": "published_to_catalog",
        "operator": "平台管理员",
        "detail": "已发布到集团能力目录，并保留上一稳定版本回滚预案。",
        "createdAt": "2026-06-24T11:05:00+08:00",
    },
]

PROTOTYPE_PLATFORM_METRICS = {
    "monthlyActiveUsers": 2486,
    "apiSuccessRate": "97.8%",
    "topSkills": ["数据查询与分析", "内部数据与联网分析", "同环比分析"],
    "coverageOrganizations": 12,
    "riskAlerts": ["请假类 Skill 待权限模型接入", "知识检索字段映射需复核", "海外政策能力待灰度发布"],
}

PROTOTYPE_PLATFORM_SKILL_METRICS = {
    "topSkills": ["数据查询与分析", "内部数据与联网分析", "同环比分析"],
    "averageCostPerCall": "¥0.42",
    "failureReasons": ["知识检索字段映射缺失", "依赖 MCP 未发布", "组织授权未开通"],
    "recommendation": "优先补齐知识检索映射和依赖 MCP 发布，可直接提升当前高频能力的稳定性。",
}

PROTOTYPE_PLATFORM_ALERTS = [
    {"id": "alert-001", "level": "critical", "message": "知识检索字段映射缺失，影响高频数据分析链路。", "source": "知识检索 MCP", "updatedAt": "今天 08:54"},
    {"id": "alert-002", "level": "warning", "message": "海外政策能力待灰度发布，需确认首批组织范围。", "source": "Skill 发布", "updatedAt": "今天 09:16"},
    {"id": "alert-003", "level": "info", "message": "组织权限 PATCH 写入链路运行稳定，近 24 小时无保存失败。", "source": "权限治理", "updatedAt": "今天 10:10"},
]

PROTOTYPE_ACTION_GOVERNANCE = [
    {
        "id": "action-001",
        "skillName": "请假申请",
        "organizationName": "广汽乘用车",
        "approvalStatus": "待审批",
        "confirmationRule": "提交前必须展示请假区间、审批人和影响考勤天数，并由本人二次确认。",
        "rollbackStatus": "若 OA 提交失败，回退为草稿并保留上次填写内容。",
        "auditTrail": ["10:05 发起请假申请", "10:06 命中动作型能力规则", "10:07 等待主管审批"],
    },
    {
        "id": "action-002",
        "skillName": "外部通知发送",
        "organizationName": "集团总部",
        "approvalStatus": "已回退",
        "confirmationRule": "发送外部通知前需校验白名单并完成平台管理员确认。",
        "rollbackStatus": "外部接口失败后已自动取消发送，并生成补发建议。",
        "auditTrail": ["09:40 发起外部通知", "09:41 白名单校验通过", "09:42 外部接口超时，自动回退"],
    },
]


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    is_pinned: Optional[bool] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    web_search_enabled: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


PROTOTYPE_ROLES = [
    {
        "id": "platform-admin",
        "roleName": "平台管理员",
        "openSkills": ["数据查询与分析", "同环比分析", "内部数据与联网分析", "请假申请"],
        "dataDomains": ["平台配置", "监控", "审计", "销售", "库存"],
        "actionPermissions": ["查询", "下载", "发布", "回滚", "授权"],
        "canAccessAdmin": True,
    },
    {
        "id": "sales-analyst",
        "roleName": "销售分析岗",
        "openSkills": ["数据查询与分析", "同环比分析"],
        "dataDomains": ["销售", "库存"],
        "actionPermissions": ["查询", "下载"],
        "canAccessAdmin": False,
    },
    {
        "id": "ai-developer",
        "roleName": "AI 开发者",
        "openSkills": ["数据查询与分析", "内部数据与联网分析"],
        "dataDomains": ["销售", "库存", "知识库"],
        "actionPermissions": ["查询", "测试", "提交"],
        "canAccessAdmin": True,
    },
]


PROTOTYPE_ACCOUNTS = [
    {
        "id": "u-admin",
        "username": "platform_admin",
        "password": "admin123",
        "displayName": "平台管理员",
        "organizationId": "gac-headquarters",
        "organizationName": "集团总部",
        "roleIds": ["platform-admin"],
        "roleNames": ["平台管理员"],
        "allowedSkills": [],
        "deniedSkills": [],
    },
    {
        "id": "u-sales-chen",
        "username": "chen_sales",
        "password": "sales123",
        "displayName": "陈销售",
        "organizationId": "gac-international",
        "organizationName": "广汽国际",
        "roleIds": ["sales-analyst"],
        "roleNames": ["销售分析岗"],
        "allowedSkills": [],
        "deniedSkills": [],
    },
    {
        "id": "u-dev-lin",
        "username": "lin_dev",
        "password": "dev123",
        "displayName": "林开发",
        "organizationId": "gac-headquarters",
        "organizationName": "集团总部",
        "roleIds": ["ai-developer"],
        "roleNames": ["AI 开发者"],
        "allowedSkills": ["内部数据与联网分析"],
        "deniedSkills": [],
    },
]


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item not in merged:
                merged.append(item)
    return merged


def _account_view(account: dict[str, Any], organizations: list[dict[str, Any]], roles: list[dict[str, Any]]) -> dict[str, Any]:
    organization = _find_by_name(organizations, account["organizationId"], "Organization")
    account_roles = [role for role in roles if role["id"] in account["roleIds"]]
    role_skills = _merge_unique(*[role["openSkills"] for role in account_roles])
    role_domains = _merge_unique(*[role["dataDomains"] for role in account_roles])
    role_actions = _merge_unique(*[role["actionPermissions"] for role in account_roles])
    baseline_skills = _merge_unique(organization["openSkills"], role_skills)
    effective_skills = [skill for skill in _merge_unique(baseline_skills, account["allowedSkills"]) if skill not in account["deniedSkills"]]
    return {
        **{key: value for key, value in account.items() if key != "password"},
        "organizationName": organization["organizationName"],
        "roleNames": [role["roleName"] for role in account_roles],
        "effectiveSkills": effective_skills,
        "effectiveDataDomains": _merge_unique(organization["dataDomains"], role_domains),
        "effectiveActionPermissions": _merge_unique(organization["actionPermissions"], role_actions),
        "canAccessAdmin": any(role["canAccessAdmin"] for role in account_roles),
    }


def _history_for_agent(session: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": message["role"], "content": message["content"]}
        for message in session.get("messages", [])
        if message["role"] in {"user", "assistant"} and message.get("content")
    ]


def _step_title(thought: dict[str, Any]) -> str:
    if thought.get("step_type") == "select_skill":
        return "意图识别"
    if thought.get("step_type") == "final_answer":
        return "最终回答"
    if thought.get("step_type") == "workflow_error":
        return "执行错误"
    decision = thought.get("decision", "")
    if "原子工具 [" in decision:
        return decision.split("原子工具 [", 1)[1].split("]", 1)[0]
    return thought.get("step_type") or "执行步骤"


def _status_from_thought(thought: dict[str, Any]) -> str:
    if thought.get("step_type") == "workflow_error" or thought.get("error"):
        return "failed"
    return "completed"


def _save_steps(repo: ChatRepository, assistant_message_id: str, thoughts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    saved = []
    for index, thought in enumerate(thoughts, start=1):
        saved.append(
            repo.add_step(
                assistant_message_id,
                step_index=index,
                step_type=thought.get("step_type") or "step",
                title=_step_title(thought),
                status=_status_from_thought(thought),
                summary=thought.get("reason") or thought.get("decision") or "",
                mcp_name=thought.get("failed_mcp"),
                mcp_input=thought.get("mcp_input"),
                mcp_output=thought.get("mcp_output"),
                llm_output=thought.get("llm_output") or thought.get("final_answer") or "",
                error=thought.get("error"),
            )
        )
    return saved


def _save_step(
    repo: ChatRepository,
    assistant_message_id: str,
    index: int,
    thought: dict[str, Any],
    duration_ms: int | None = None,
) -> dict[str, Any]:
    return repo.add_step(
        assistant_message_id,
        step_index=index,
        step_type=thought.get("step_type") or "step",
        title=_step_title(thought),
        status=_status_from_thought(thought),
        summary=thought.get("reason") or thought.get("decision") or "",
        mcp_name=thought.get("failed_mcp"),
        mcp_input=thought.get("mcp_input"),
        mcp_output=thought.get("mcp_output"),
        llm_output=thought.get("llm_output") or thought.get("final_answer") or "",
        error=thought.get("error"),
        duration_ms=duration_ms,
    )


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _split_answer_for_streaming(content: str) -> tuple[str, str]:
    analysis_markers = ("### 💡", "### 业务分析", "### 分析", "### 建议")
    positions = [content.find(marker) for marker in analysis_markers if content.find(marker) >= 0]
    if not positions:
        return "", content
    split_at = min(positions)
    return content[:split_at].rstrip(), content[split_at:].lstrip()


def _answer_chunks(content: str, chunk_size: int = 18) -> list[str]:
    return [content[index:index + chunk_size] for index in range(0, len(content), chunk_size)]


def _preview_content_from_thought(thought: dict[str, Any]) -> str:
    decision = thought.get("decision") or ""
    if not decision.endswith("原子工具 [sql_executor]"):
        return ""
    output = thought.get("mcp_output")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except json.JSONDecodeError:
            pass
    if isinstance(output, dict):
        output = output.get("text") or output.get("data") or output.get("result") or ""
    if not isinstance(output, str) or "|" not in output:
        return ""
    return f"### 📊 内部数据查询结果\n{output.strip()}"


def _running_step(index: int) -> dict[str, Any]:
    return {
        "id": f"running-{index}",
        "message_id": "running",
        "step_index": index,
        "step_type": "running",
        "title": "正在执行下一节点",
        "status": "running",
        "summary": "Skill 与 MCP 链路正在运行",
        "created_at": "",
    }


def _title_from_first_question(message: str) -> str:
    title = " ".join(message.split())
    if len(title) <= SESSION_TITLE_MAX_LENGTH:
        return title
    return f"{title[:SESSION_TITLE_MAX_LENGTH]}…"


def _summary_from_question(message: str) -> str:
    summary = " ".join(message.split())
    if len(summary) <= SESSION_SUMMARY_MAX_LENGTH:
        return summary
    return f"{summary[:SESSION_SUMMARY_MAX_LENGTH]}…"


def _auto_name_session(repo: ChatRepository, session: dict[str, Any], message: str) -> None:
    if session.get("title") not in DEFAULT_SESSION_TITLES or session.get("messages"):
        return
    title = _title_from_first_question(message)
    if title:
        repo.update_session(session["id"], title=title)


def _update_session_summary(repo: ChatRepository, session_id: str, message: str) -> None:
    summary = _summary_from_question(message)
    if summary:
        repo.update_session(session_id, summary=summary)


def _find_by_name(items: list[dict[str, Any]], name: str, label: str) -> dict[str, Any]:
    for item in items:
        if item.get("name") == name or item.get("id") == name:
            return item
    raise HTTPException(status_code=404, detail=f"{label} not found: {name}")


def _lifecycle_stage_for_release_status(release_status: str, failure_reason: str | None = None) -> str:
    if release_status == "draft":
        return "draft"
    if release_status == "testing":
        return "testing"
    if release_status in {"ready_for_review", "review_approved"}:
        return "review"
    if release_status == "ready_to_publish":
        return "publish"
    if release_status == "published":
        return "published"
    if failure_reason:
        return "review_rejected"
    return "blocked"


def _tasks_for_asset(
    task_type: str,
    entity_name: str,
    display_name: str,
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    direct_tasks = [
        task for task in tasks
        if task["type"] == task_type and (
            task["entityName"] == entity_name
            or task["entityName"] == display_name
            or display_name in task["title"]
        )
    ]
    if task_type != "skill":
        return direct_tasks
    direct_task_ids = {task["id"] for task in direct_tasks}
    child_tasks = [task for task in tasks if task.get("parentTaskId") in direct_task_ids]
    return [*direct_tasks, *child_tasks]


def _build_unified_assets(
    skills: list[dict[str, Any]],
    mcps: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for skill in skills:
        related_tasks = _tasks_for_asset("skill", skill["name"], skill["displayName"], tasks)
        primary_task = next((task for task in related_tasks if task["type"] == "skill"), None)
        failure_reason = (primary_task or {}).get("failureReason") or (primary_task or {}).get("blockedBy")
        assets.append({
            "asset_id": f"skill:{skill['name']}",
            "asset_type": "skill",
            "name": skill["name"],
            "display_name": skill["displayName"],
            "description": skill["description"],
            "category": skill["category"],
            "status": skill["status"],
            "release_status": skill["releaseStatus"],
            "current_stage": _lifecycle_stage_for_release_status(skill["releaseStatus"], failure_reason),
            "risk_level": skill.get("riskLevel") or "中",
            "owner": related_tasks[0]["owner"] if related_tasks else "平台管理员",
            "dependency_status": f"{len(skill.get('mcpTools') or [])} 个 MCP 依赖" if skill.get("mcpTools") else "无外部依赖",
            "failure_summary": failure_reason,
            "organization_summary": " / ".join(skill.get("applicableOrganizations") or []) or "待配置组织范围",
            "action_url": f"/admin/skills/{skill['name']}",
            "updated_at": primary_task["updatedAt"] if primary_task else "刚刚",
        })
    for mcp in mcps:
        failure_reason = mcp.get("blockedBy")
        assets.append({
            "asset_id": f"mcp:{mcp['name']}",
            "asset_type": "mcp",
            "name": mcp["name"],
            "display_name": mcp["displayName"],
            "description": mcp["description"],
            "category": mcp["category"],
            "status": mcp["status"],
            "release_status": mcp["releaseStatus"],
            "current_stage": _lifecycle_stage_for_release_status(mcp["releaseStatus"], failure_reason),
            "risk_level": "高" if "executor" in mcp["name"] else "中",
            "owner": _tasks_for_asset("mcp", mcp["name"], mcp["displayName"], tasks)[0]["owner"] if _tasks_for_asset("mcp", mcp["name"], mcp["displayName"], tasks) else "平台管理员",
            "dependency_status": f"被 {len(mcp.get('referencedBy') or [])} 个 Skill 引用" if mcp.get("referencedBy") else "尚未被 Skill 引用",
            "failure_summary": failure_reason,
            "organization_summary": "发布前治理配置",
            "action_url": f"/admin/mcps/{mcp['name']}",
            "updated_at": "刚刚",
        })
    stage_priority = {
        "blocked": 0,
        "review_rejected": 1,
        "testing": 2,
        "review": 3,
        "publish": 4,
        "draft": 5,
        "published": 6,
    }
    assets.sort(key=lambda item: (stage_priority.get(item["current_stage"], 99), 0 if item["asset_type"] == "mcp" else 1, item["display_name"]))
    return assets


def _match_action_skill(message: str) -> str | None:
    lowered = message.lower()
    if any(keyword in message for keyword in ["请假", "年假", "事假", "调休"]) or "leave" in lowered:
        return "leave_request"
    return None


def _mock_action_skill_result(message: str, skill_name: str, phase: str = "pending_confirmation") -> dict[str, Any]:
    if skill_name == "leave_request":
        if phase == "confirmed":
            return {
                "selected_skill": "leave_request",
                "messages": [{
                    "role": "assistant",
                    "content": (
                        "### 已提交\n"
                        "已收到你的确认，系统已按请假申请流程继续提交。\n\n"
                        "### 当前模拟结果\n"
                        f"- 申请内容：{message}\n"
                        "- 提交状态：已进入 OA 审批流\n"
                        "- 审计记录：已记录确认时间、提交人和审批路径。"
                    ),
                }],
                "thought_process": [
                    {"step_type": "approval_gate", "decision": "收到确认提交", "reason": "动作型 Skill 已完成二次确认"},
                    {"step_type": "submit_action", "decision": "提交至 OA 审批流", "reason": "按确认结果继续执行动作"},
                ],
            }
        if phase == "cancelled":
            return {
                "selected_skill": "leave_request",
                "messages": [{
                    "role": "assistant",
                    "content": (
                        "### 已回退\n"
                        "已按你的要求取消本次请假提交，当前申请已回退为草稿。\n\n"
                        "### 当前模拟结果\n"
                        f"- 原申请内容：{message}\n"
                        "- 回退状态：草稿已保留，可稍后补充后再次提交\n"
                        "- 审计记录：已记录取消时间和回退原因。"
                    ),
                }],
                "thought_process": [
                    {"step_type": "approval_gate", "decision": "收到取消指令", "reason": "动作型 Skill 在确认前被取消"},
                    {"step_type": "rollback_action", "decision": "回退为草稿", "reason": "保留用户输入，等待后续补提"},
                ],
            }
        return {
            "selected_skill": "leave_request",
            "messages": [{
                "role": "assistant",
                "content": (
                    "### 需确认后提交\n"
                    "已识别为请假申请。系统会先补齐请假区间、审批人和影响考勤天数，"
                    "在你完成二次确认后再继续提交。\n\n"
                    "### 当前模拟结果\n"
                    f"- 申请内容：{message}\n"
                    "- 审批状态：等待直属主管确认\n"
                    "- 失败回退：如 OA 提交失败，将自动保留草稿并提示补提。"
                ),
            }],
            "thought_process": [
                {"step_type": "select_skill", "decision": "选择 leave_request", "reason": "检测到请假/休假类动作型请求"},
                {"step_type": "approval_gate", "decision": "命中审批前置与二次确认", "reason": "动作型 Skill 需确认后提交"},
            ],
        }
    return {
        "selected_skill": "chat",
        "messages": [{"role": "assistant", "content": message}],
        "thought_process": [],
    }


def create_app(db_path: Optional[Union[str, Path]] = None) -> FastAPI:
    resolved_db_path = db_path or os.getenv("CHAT_DB_PATH") or DEFAULT_DB_PATH
    repo = ChatRepository(resolved_db_path)
    permission_repo = PermissionRepository(
        resolved_db_path,
        organizations=deepcopy(PROTOTYPE_ORGANIZATION_PROFILES),
        roles=deepcopy(PROTOTYPE_ROLES),
        accounts=deepcopy(PROTOTYPE_ACCOUNTS),
    )
    registry_repo = RegistryRepository(
        resolved_db_path,
        skills=deepcopy(PROTOTYPE_ADMIN_SKILLS),
        mcps=deepcopy(PROTOTYPE_ADMIN_MCPS),
        governance_tasks=deepcopy(PROTOTYPE_GOVERNANCE_TASKS),
        release_activities=deepcopy(PROTOTYPE_RELEASE_ACTIVITIES),
    )
    app = FastAPI(title="广汽集团 AI 一体化平台 API")
    app.state.repo = repo
    app.state.permission_repo = permission_repo
    app.state.registry_repo = registry_repo

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/sessions")
    def list_sessions():
        return repo.list_sessions()

    @app.post("/api/sessions")
    def create_session(payload: SessionCreate):
        return repo.create_session(payload.title)

    @app.get("/api/sessions/{session_id}")
    def get_session(session_id: str):
        try:
            return repo.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.patch("/api/sessions/{session_id}")
    def update_session(session_id: str, payload: SessionUpdate):
        try:
            return repo.update_session(
                session_id,
                title=payload.title,
                summary=payload.summary,
                is_pinned=payload.is_pinned,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete("/api/sessions/{session_id}", status_code=204)
    def delete_session(session_id: str):
        repo.delete_session(session_id)

    @app.post("/api/auth/login")
    def login(payload: LoginRequest):
        account = permission_repo.get_account_by_username(payload.username)
        if account and account["password"] == payload.password:
            account_view = permission_repo.account_view(account["id"])
            if account_view:
                return {"token": account["id"], "account": account_view}
        raise HTTPException(status_code=401, detail="Invalid username or password")

    @app.post("/api/auth/logout", status_code=204)
    def logout():
        return None

    @app.get("/api/auth/me")
    def get_current_account(account_id: str = "u-admin"):
        account = permission_repo.account_view(account_id)
        if account is None:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
        return account

    @app.get("/api/capabilities")
    def list_capabilities():
        return PROTOTYPE_CAPABILITIES

    @app.get("/api/capabilities/{skill_id}")
    def get_capability(skill_id: str):
        return _find_by_name(PROTOTYPE_CAPABILITIES, skill_id, "Capability")

    @app.get("/api/users/me/capabilities")
    def list_my_capabilities():
        return [item for item in PROTOTYPE_CAPABILITIES if item["name"] in {"data_query", "yoy_yoy_analysis"}]

    @app.get("/api/admin/accounts")
    def list_accounts():
        return permission_repo.list_account_views()

    @app.post("/api/admin/accounts")
    def create_account(payload: dict[str, Any]):
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="username is required")
        if permission_repo.get_account_by_username(username):
            raise HTTPException(status_code=409, detail=f"Account already exists: {username}")
        created = permission_repo.create_account(payload)
        account_view = permission_repo.account_view(created["id"])
        if account_view is None:
            raise HTTPException(status_code=500, detail=f"Failed to create account: {username}")
        return account_view

    @app.get("/api/admin/accounts/{account_id}/permissions")
    def get_account_permissions(account_id: str):
        account = permission_repo.account_view(account_id)
        if account is None:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
        return account

    @app.patch("/api/admin/accounts/{account_id}/permissions")
    def update_account_permissions(account_id: str, payload: dict[str, Any]):
        account = permission_repo.update_account(account_id, payload)
        if account is None:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
        account_view = permission_repo.account_view(account_id)
        if account_view is None:
            raise HTTPException(status_code=500, detail=f"Failed to reload account: {account_id}")
        return account_view

    @app.get("/api/admin/roles")
    def list_roles():
        return permission_repo.list_roles()

    @app.patch("/api/admin/roles/{role_id}")
    def update_role(role_id: str, payload: dict[str, Any]):
        role = permission_repo.update_role(role_id, payload)
        if role is None:
            raise HTTPException(status_code=404, detail=f"Role not found: {role_id}")
        return role

    @app.get("/api/organizations")
    def list_organizations():
        return permission_repo.list_organizations()

    @app.get("/api/organizations/{org_id}/permissions")
    def get_organization_permissions(org_id: str):
        organization = permission_repo.get_organization(org_id)
        if organization is None:
            raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
        return organization

    @app.patch("/api/organizations/{org_id}/permissions")
    def update_organization_permissions(org_id: str, payload: dict[str, Any]):
        organization = permission_repo.update_organization(org_id, payload)
        if organization is None:
            raise HTTPException(status_code=404, detail=f"Organization not found: {org_id}")
        return organization

    @app.get("/api/admin/skills")
    def list_admin_skills():
        return registry_repo.list_skills()

    @app.get("/api/admin/skills/{skill_id}")
    def get_admin_skill(skill_id: str):
        skill = registry_repo.get_skill(skill_id)
        if skill is None:
            raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
        return skill

    @app.post("/api/admin/skills")
    def create_admin_skill(payload: dict[str, Any]):
        return registry_repo.create_skill(payload)

    @app.patch("/api/admin/skills/{skill_id}")
    def update_admin_skill(skill_id: str, payload: dict[str, Any]):
        skill = registry_repo.update_skill(skill_id, payload)
        if skill is None:
            raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
        return skill

    @app.post("/api/admin/skills/{skill_id}/test")
    def test_admin_skill(skill_id: str, payload: dict[str, Any]):
        skill = registry_repo.get_skill(skill_id)
        if skill is None:
            raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
        return {"skillId": skill["name"], "status": "passed", "input": payload, "autoTestPassRate": "7/7"}

    @app.get("/api/admin/governance/tasks")
    def list_governance_tasks():
        return registry_repo.list_governance_tasks()

    @app.get("/api/admin/assets")
    def list_admin_assets():
        return _build_unified_assets(
            registry_repo.list_skills(),
            registry_repo.list_mcps(),
            registry_repo.list_governance_tasks(),
        )

    @app.get("/api/admin/governance/activities")
    def list_governance_activities():
        return registry_repo.list_release_activities()

    @app.post("/api/admin/governance/skills/{skill_id}/submit")
    def submit_skill_governance(skill_id: str):
        result = registry_repo.submit_skill_governance(skill_id, operator="平台管理员")
        if result is None:
            raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
        return result

    @app.post("/api/admin/governance/tasks/{task_id}/approve")
    def approve_governance_task(task_id: str):
        result = registry_repo.approve_governance_task(task_id, operator="平台管理员")
        if result is None:
            raise HTTPException(status_code=404, detail=f"Governance task not found: {task_id}")
        return result

    @app.post("/api/admin/governance/tasks/{task_id}/publish")
    def publish_governance_task(task_id: str):
        result = registry_repo.publish_governance_task(task_id, operator="平台管理员")
        if result is None:
            raise HTTPException(status_code=404, detail=f"Governance task not found: {task_id}")
        return result

    @app.get("/api/admin/mcps")
    def list_admin_mcps():
        return registry_repo.list_mcps()

    @app.post("/api/admin/mcps")
    def create_admin_mcp(payload: dict[str, Any]):
        return registry_repo.create_mcp(payload)

    @app.get("/api/admin/mcps/{mcp_id}")
    def get_admin_mcp(mcp_id: str):
        mcp = registry_repo.get_mcp(mcp_id)
        if mcp is None:
            raise HTTPException(status_code=404, detail=f"MCP not found: {mcp_id}")
        return mcp

    @app.patch("/api/admin/mcps/{mcp_id}")
    def update_admin_mcp(mcp_id: str, payload: dict[str, Any]):
        mcp = registry_repo.update_mcp(mcp_id, payload)
        if mcp is None:
            raise HTTPException(status_code=404, detail=f"MCP not found: {mcp_id}")
        return mcp

    @app.post("/api/admin/mcps/{mcp_id}/health-check")
    def run_admin_mcp_health_check(mcp_id: str):
        mcp = registry_repo.mark_mcp_health_check(mcp_id, operator="平台管理员", health="healthy")
        if mcp is None:
            raise HTTPException(status_code=404, detail=f"MCP not found: {mcp_id}")
        return {"mcpId": mcp["name"], "health": mcp["health"], "message": "健康检查通过"}

    @app.get("/api/admin/metrics/overview")
    def get_platform_metrics_overview():
        return PROTOTYPE_PLATFORM_METRICS

    @app.get("/api/admin/metrics/skills")
    def get_platform_skill_metrics():
        return PROTOTYPE_PLATFORM_SKILL_METRICS

    @app.get("/api/admin/metrics/organizations")
    def get_platform_organization_metrics():
        return {
            "coverageOrganizations": PROTOTYPE_PLATFORM_METRICS["coverageOrganizations"],
            "organizationItems": [
                {"organizationName": "广汽国际", "coverageRate": "92%", "activeUsers": 186},
                {"organizationName": "集团总部", "coverageRate": "88%", "activeUsers": 124},
                {"organizationName": "广汽乘用车", "coverageRate": "61%", "activeUsers": 83},
            ],
            "organizations": permission_repo.list_organizations(),
        }

    @app.get("/api/admin/alerts")
    def list_platform_alerts():
        return PROTOTYPE_PLATFORM_ALERTS

    @app.get("/api/admin/audit/permissions")
    def list_permission_audit_logs():
        return permission_repo.list_permission_audit_logs()

    @app.get("/api/admin/action-governance")
    def list_action_governance():
        return PROTOTYPE_ACTION_GOVERNANCE

    @app.post("/api/chat")
    def chat(payload: ChatRequest):
        try:
            session = repo.get_session(payload.session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        _auto_name_session(repo, session, payload.message)
        _update_session_summary(repo, payload.session_id, payload.message)
        user_message = repo.add_message(
            payload.session_id,
            role="user",
            content=payload.message,
            web_search_enabled=payload.web_search_enabled,
        )
        pending_action = None
        if session.get("pending_action_skill") and session.get("pending_action_status") == "pending_confirmation":
            pending_action = {
                "skill_name": session.get("pending_action_skill"),
                "original_message": session.get("pending_action_message"),
            }
        matched_action_skill = _match_action_skill(payload.message)
        if pending_action and payload.message.strip() in {"确认提交", "确认", "提交"}:
            result = _mock_action_skill_result(pending_action["original_message"], pending_action["skill_name"], "confirmed")
            repo.update_session(
                payload.session_id,
                pending_action_skill=None,
                pending_action_message=None,
                pending_action_status=None,
            )
        elif pending_action and payload.message.strip() in {"取消", "先取消", "撤回"}:
            result = _mock_action_skill_result(pending_action["original_message"], pending_action["skill_name"], "cancelled")
            repo.update_session(
                payload.session_id,
                pending_action_skill=None,
                pending_action_message=None,
                pending_action_status=None,
            )
        elif matched_action_skill:
            result = _mock_action_skill_result(payload.message, matched_action_skill)
            repo.update_session(
                payload.session_id,
                pending_action_skill=matched_action_skill,
                pending_action_message=payload.message,
                pending_action_status="pending_confirmation",
            )
        else:
            result = run_agent(
            payload.message,
            history=_history_for_agent(session),
            web_search_enabled=payload.web_search_enabled,
            )
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        assistant_content = result["messages"][-1]["content"]
        assistant_message = repo.add_message(
            payload.session_id,
            role="assistant",
            content=assistant_content,
            selected_skill=result.get("selected_skill"),
            web_search_enabled=payload.web_search_enabled,
            trace_open=True,
        )
        steps = _save_steps(repo, assistant_message["id"], result.get("thought_process", []))
        assistant_message["steps"] = steps
        repo.update_session(
            payload.session_id,
            last_mode=result.get("selected_skill"),
            last_web_search_enabled=payload.web_search_enabled,
        )
        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

    @app.post("/api/chat/stream")
    async def chat_stream(payload: ChatRequest):
        try:
            session = repo.get_session(payload.session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        async def event_stream():
            _auto_name_session(repo, session, payload.message)
            _update_session_summary(repo, payload.session_id, payload.message)
            user_message = repo.add_message(
                payload.session_id,
                role="user",
                content=payload.message,
                web_search_enabled=payload.web_search_enabled,
            )
            assistant_message = repo.add_message(
                payload.session_id,
                role="assistant",
                content="",
                web_search_enabled=payload.web_search_enabled,
                trace_open=True,
            )
            yield _sse("message_created", user_message)
            yield _sse("step_started", _running_step(1))

            pending_action = None
            if session.get("pending_action_skill") and session.get("pending_action_status") == "pending_confirmation":
                pending_action = {
                    "skill_name": session.get("pending_action_skill"),
                    "original_message": session.get("pending_action_message"),
                }
            matched_action_skill = _match_action_skill(payload.message)
            action_result = None
            if pending_action and payload.message.strip() in {"确认提交", "确认", "提交"}:
                action_result = _mock_action_skill_result(pending_action["original_message"], pending_action["skill_name"], "confirmed")
                repo.update_session(
                    payload.session_id,
                    pending_action_skill=None,
                    pending_action_message=None,
                    pending_action_status=None,
                )
            elif pending_action and payload.message.strip() in {"取消", "先取消", "撤回"}:
                action_result = _mock_action_skill_result(pending_action["original_message"], pending_action["skill_name"], "cancelled")
                repo.update_session(
                    payload.session_id,
                    pending_action_skill=None,
                    pending_action_message=None,
                    pending_action_status=None,
                )
            elif matched_action_skill:
                action_result = _mock_action_skill_result(payload.message, matched_action_skill)
                repo.update_session(
                    payload.session_id,
                    pending_action_skill=matched_action_skill,
                    pending_action_message=payload.message,
                    pending_action_status="pending_confirmation",
                )
            if action_result:
                result = action_result
                saved_steps = []
                for index, thought in enumerate(result.get("thought_process", []), start=1):
                    step = _save_step(repo, assistant_message["id"], index, thought, 180)
                    saved_steps.append(step)
                    yield _sse("step_completed", step)
                    if index < len(result.get("thought_process", [])):
                        yield _sse("step_started", _running_step(index + 1))

                assistant_content = result["messages"][-1]["content"]
                assistant_message_updated = repo.update_message(
                    assistant_message["id"],
                    content=assistant_content,
                    selected_skill=result.get("selected_skill"),
                )
                assistant_message_updated["steps"] = saved_steps
                repo.update_session(
                    payload.session_id,
                    last_mode=result.get("selected_skill"),
                    last_web_search_enabled=payload.web_search_enabled,
                )
                yield _sse("result_ready", {"content": assistant_content})
                yield _sse("answer_completed", assistant_message_updated)
                return

            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()

            def step_callback(thought: dict[str, Any]) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, ("step_completed", thought))

            async def run_worker() -> None:
                try:
                    result = await asyncio.to_thread(
                        run_agent,
                        payload.message,
                        callback=step_callback,
                        history=_history_for_agent(session),
                        web_search_enabled=payload.web_search_enabled,
                    )
                except Exception as exc:
                    result = {"error": f"Engine execution failed: {exc}"}
                await queue.put(("worker_completed", result))

            worker = asyncio.create_task(run_worker())
            saved_steps: list[dict[str, Any]] = []
            result: dict[str, Any] = {}
            step_started_at = loop.time()
            last_preview_content = ""

            while True:
                event, data = await queue.get()
                if event == "step_completed":
                    duration_ms = max(1, round((loop.time() - step_started_at) * 1000))
                    step = _save_step(repo, assistant_message["id"], len(saved_steps) + 1, data, duration_ms)
                    saved_steps.append(step)
                    yield _sse(event, step)
                    preview_content = _preview_content_from_thought(data)
                    if preview_content and preview_content != last_preview_content:
                        last_preview_content = preview_content
                        yield _sse("preview_ready", {"content": preview_content})
                    yield _sse("step_started", _running_step(len(saved_steps) + 1))
                    step_started_at = loop.time()
                    continue
                result = data
                break

            await worker
            if result.get("error"):
                error_message = result["error"]
                repo.update_message(assistant_message["id"], content=f"请求失败：{error_message}")
                yield _sse("error", {"message": error_message})
                return

            assistant_content = result["messages"][-1]["content"]
            assistant_message = repo.update_message(
                assistant_message["id"],
                content=assistant_content,
                selected_skill=result.get("selected_skill"),
            )
            assistant_message["steps"] = saved_steps
            repo.update_session(
                payload.session_id,
                last_mode=result.get("selected_skill"),
                last_web_search_enabled=payload.web_search_enabled,
            )
            result_content, analysis_content = _split_answer_for_streaming(assistant_content)
            yield _sse("result_ready", {"content": result_content})
            for delta in _answer_chunks(analysis_content):
                yield _sse("answer_delta", {"delta": delta})
                await asyncio.sleep(ANSWER_STREAM_DELAY_SECONDS)
            yield _sse("answer_completed", assistant_message)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return app


app = create_app()
