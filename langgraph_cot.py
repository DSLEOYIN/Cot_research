"""
LangGraph ReAct Agent - Standard Skill + MCP Double-layer Execution Engine

Core Flow:
Question → LLM dynamic routing to Skill → Standard Workflow Engine executes steps in Skill (resolving variables) → Streamlit thought chain rendering
"""

from __future__ import annotations

import json
import os
import re
from contextvars import ContextVar
from typing import TypedDict, Sequence, Literal, Any, Optional, List
from dataclasses import dataclass
from app_config import get_config
from prompt_loader import render_prompt

# Import registered MCPs and Skills
from mcps import execute_mcp, list_mcps
from skills import get_skill, list_skills

# Active callback isolated per request/thread for streaming status updates.
_ACTIVE_CALLBACK: ContextVar[Any] = ContextVar("active_callback", default=None)


# ==================== Variable Template Resolver ====================

def resolve_variables(template: Any, context: dict) -> Any:
    """
    Recursively resolves {{variable}} placeholders from the context.
    Supports path routing such as {{input.query}}, {{steps.retrieve_schema.output}}, etc.
    """
    if isinstance(template, str):
        # 1. First check if it is a single complete variable mapping, to preserve its original type (e.g. list/dict)
        single_match = re.match(r"^\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}$", template.strip())
        if single_match:
            path = single_match.group(1).strip()
            parts = path.split('.')
            current = context
            found = True
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    found = False
                    break
            if found:
                return current

        # 2. Otherwise perform inline string substitution
        pattern = r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}"
        
        def replace_match(match):
            path = match.group(1).strip()
            parts = path.split('.')
            current = context
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return match.group(0) # Keep original if not found
            
            if isinstance(current, (dict, list)):
                return json.dumps(current, ensure_ascii=False)
            return str(current)
            
        return re.sub(pattern, replace_match, template)
        
    elif isinstance(template, dict):
        return {k: resolve_variables(v, context) for k, v in template.items()}
    elif isinstance(template, list):
        return [resolve_variables(x, context) for x in template]
    return template


def _parse_json_result(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return raw


def _strip_sql_fence(text: str) -> str:
    sql = (text or "").strip()
    if sql.startswith("```sql"):
        sql = sql[6:]
    elif sql.startswith("```"):
        sql = sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]
    return sql.strip()


def _append_thought(thought_process: list, thought_entry: dict) -> None:
    thought_process.append(thought_entry)
    _emit_callback(thought_entry)


def _emit_callback(thought_entry: dict) -> None:
    callback = _ACTIVE_CALLBACK.get()
    if callback:
        try:
            callback(thought_entry)
        except Exception:
            pass


def _current_user_question(messages: Sequence[dict]) -> str:
    for message in reversed(list(messages)):
        if message.get("role") == "user":
            return message.get("content", "")
    return messages[-1].get("content", "") if messages else ""


def _sanitize_history_messages(history: Sequence[dict] | None, max_messages: int = 8) -> list[dict]:
    if not history:
        return []

    sanitized = []
    for message in history:
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        sanitized.append({"role": role, "content": content})
    return sanitized[-max_messages:]


def _history_before_current_user(messages: Sequence[dict]) -> list[dict]:
    message_list = list(messages)
    current_user_index = None
    for index in range(len(message_list) - 1, -1, -1):
        if message_list[index].get("role") == "user":
            current_user_index = index
            break
    if current_user_index is None:
        return _sanitize_history_messages(message_list)
    return _sanitize_history_messages(message_list[:current_user_index])


def _format_recent_memory(history_messages: Sequence[dict]) -> str:
    if not history_messages:
        return ""

    role_labels = {"user": "用户", "assistant": "助手"}
    lines = ["最近会话上下文："]
    for message in history_messages:
        role_label = role_labels.get(message.get("role"), message.get("role", "消息"))
        content = message.get("content", "")
        if len(content) > 360:
            content = content[:360] + "..."
        lines.append(f"{role_label}：{content}")
    return "\n".join(lines)


def _recent_history_text(history_messages: Sequence[dict], max_chars: int = 1600) -> str:
    text = "\n".join((message.get("content") or "") for message in history_messages)
    return text[-max_chars:]


def _query_with_memory(current_question: str, history_messages: Sequence[dict]) -> str:
    memory_text = _format_recent_memory(history_messages)
    if not memory_text:
        return current_question

    return (
        f"当前问题：{current_question}\n\n"
        f"{memory_text}\n\n"
        "请优先回答当前问题；当当前问题依赖上文时，结合最近会话上下文理解指代、时间、组织和指标。"
    )


def _route_contextual_followup(user_question: str, history_messages: Sequence[dict]) -> tuple[str | None, str]:
    q_lower = user_question.lower()
    recent_history_text = _recent_history_text(history_messages)

    web_keywords = [
        "联网", "网上", "网络", "公开资料", "公开信息", "搜索", "搜一下", "查一下",
        "新闻", "最新", "今天", "行业趋势", "行业情况", "外部信息", "外部数据", "竞品"
    ]
    external_market_keywords = [
        "全球", "全球市场", "国际市场", "海外市场", "公开市场", "行业市场",
        "市场表现", "市场情况", "卖得怎么样", "卖的怎么样"
    ]
    context_keywords = ["刚才", "上文", "上面", "之前", "前面", "这个结果", "真实数据", "内部数据", "对比", "比较", "解释", "分析", "竞品"]
    data_keywords = ["销量", "终端量", "批发量", "库存", "订单", "排产", "达成", "销售", "卖", "表现", "国家", "大区", "公司"]
    internal_subject_keywords = ["广汽国际", "国际", "中东公司", "内部", "真实数据", "内部数据", "我司", "本公司"]
    followup_keywords = ["为什么", "原因", "继续", "展开", "深挖", "详细", "再分析", "建议", "怎么办", "怎么做", "接着", "进一步", "然后呢", "这个呢", "那呢", "对比呢", "竞品"]

    has_web_intent = any(k in q_lower for k in web_keywords)
    has_external_market_intent = any(k in q_lower for k in external_market_keywords)
    has_context_compare_intent = any(k in q_lower for k in context_keywords)
    has_data_intent = any(k in q_lower for k in data_keywords)
    has_internal_subject = any(k in q_lower for k in internal_subject_keywords)
    has_followup_intent = any(k in q_lower for k in followup_keywords)
    recent_has_data_context = any(k in recent_history_text for k in data_keywords + ["内部真实数据", "内部数据查询", "SQL", "数据查询结果", "销量表现"])
    recent_has_web_context = any(k in recent_history_text for k in web_keywords + ["联网检索", "外部公开资料", "公开资料"])

    # A current-turn composite request must contain a fresh internal data query.
    # Short follow-ups like "和其他竞品对比呢" should reuse prior data instead of regenerating SQL.
    if has_followup_intent and recent_has_data_context and (has_web_intent or has_context_compare_intent or recent_has_web_context):
        return "web_compare_analysis", "检测到当前问题是基于上一轮数据/分析上下文的竞品或外部对比追问，复用会话上下文并路由至[联网对比分析]技能。"

    if has_followup_intent and recent_has_data_context:
        return "data_query", "检测到当前问题是对上一轮数据分析的追问，继承会话上下文并路由至[数据查询与分析]技能。"

    if (has_web_intent or has_external_market_intent) and has_data_intent and has_internal_subject:
        return "data_web_compare_analysis", "检测到当前句子同时包含内部主体/业务指标和全球或公开市场表现诉求，需要内部数据与联网公开资料共同支撑，路由至[内部数据与联网竞品对比分析]技能。"

    return None, ""


def _intent_flags(user_question: str, history_messages: Sequence[dict] | None = None) -> dict[str, bool]:
    q_lower = user_question.lower()
    recent_history_text = _recent_history_text(history_messages or [])
    web_keywords = [
        "联网", "网上", "网络", "公开资料", "公开信息", "搜索", "搜一下", "查一下",
        "新闻", "最新", "今天", "行业趋势", "行业情况", "外部信息", "外部数据", "竞品"
    ]
    external_market_keywords = [
        "全球", "全球市场", "国际市场", "海外市场", "公开市场", "行业市场",
        "市场表现", "市场情况", "卖得怎么样", "卖的怎么样"
    ]
    data_keywords = ["销量", "终端量", "批发量", "库存", "订单", "排产", "达成", "销售", "卖", "表现", "国家", "大区", "公司"]
    internal_subject_keywords = ["广汽国际", "国际", "中东公司", "内部", "真实数据", "内部数据", "我司", "本公司"]
    followup_keywords = ["为什么", "原因", "继续", "展开", "深挖", "详细", "再分析", "建议", "怎么办", "怎么做", "接着", "进一步", "然后呢", "这个呢", "那呢", "对比呢", "竞品"]
    recent_has_data_context = any(k in recent_history_text for k in data_keywords + ["内部真实数据", "内部数据查询", "SQL", "数据查询结果", "销量表现"])

    return {
        "has_web_intent": any(k in q_lower for k in web_keywords),
        "has_external_market_intent": any(k in q_lower for k in external_market_keywords),
        "has_data_intent": any(k in q_lower for k in data_keywords),
        "has_internal_subject": any(k in q_lower for k in internal_subject_keywords),
        "has_followup_intent": any(k in q_lower for k in followup_keywords),
        "recent_has_data_context": recent_has_data_context,
        "has_yoy_intent": any(k in q_lower for k in ["同比", "环比", "增长"]),
    }


def _skill_allowed_by_web_toggle(skill_name: str, web_search_enabled: bool) -> bool:
    if web_search_enabled:
        return True
    return skill_name not in {"web_search_answer", "web_compare_analysis", "data_web_compare_analysis"}


def _route_by_web_toggle(user_question: str, history_messages: Sequence[dict], web_search_enabled: bool) -> tuple[str | None, str]:
    flags = _intent_flags(user_question, history_messages)
    has_web_or_external = flags["has_web_intent"] or flags["has_external_market_intent"]
    has_internal_data_request = flags["has_data_intent"] and flags["has_internal_subject"]

    if not web_search_enabled and flags["has_web_intent"]:
        return "__web_disabled__", "用户明确要求联网检索，但本轮联网搜索开关关闭。"

    if web_search_enabled:
        if flags["has_followup_intent"] and flags["recent_has_data_context"]:
            return "web_compare_analysis", "联网搜索已开启，检测到当前问题依赖上文内部数据，路由至[联网对比分析]技能。"
        if has_internal_data_request:
            return "data_web_compare_analysis", "联网搜索已开启，内部数据问题需同时结合外部公开资料，路由至[内部数据与联网竞品对比分析]技能。"
        if has_web_or_external:
            return "web_search_answer", "联网搜索已开启，检测到公开资料检索诉求，路由至[联网检索问答]技能。"

    return None, ""


def _build_agent_messages(question: str, history: Sequence[dict] | None = None) -> list[dict]:
    history_messages = _sanitize_history_messages(history)
    return history_messages + [{"role": "user", "content": question}]


def _build_mcp_thought(step_num: int, step_name: str, step_item: dict, mcp_name: str, resolved_args: dict, result_str: str, result_data: Any) -> dict:
    thought = {
        "step": step_num + 1,
        "step_type": "execute_mcp",
        "decision": f"SOP 步骤 {step_num} [{step_name}]：调用原子工具 [{mcp_name}]",
        "reason": step_item["description"],
        "mcp_input": resolved_args,
        "mcp_output": result_str,
        "llm_output": ""
    }
    if mcp_name == "llm" and isinstance(result_data, dict):
        thought["llm_output"] = result_data.get("text", "")
    elif mcp_name == "n2sql" and isinstance(result_data, dict):
        thought["llm_output"] = f"生成的 SQL 语句：\n```sql\n{result_data.get('sql', '')}\n```"
    return thought


def _try_correct_sql(step_num: int, step_name: str, step_item: dict, resolved_args: dict, result_data: dict, context: dict, thought_process: list) -> tuple[str, Any, dict] | None:
    if step_item.get("mcp") != "sql_executor":
        return None

    try:
        import theme_loader
        table_info = theme_loader.get_active_theme_table_info()
    except Exception:
        table_info = ""

    wrong_sql = resolved_args.get("query", "")
    correction_args = {
        "prompt": context["input"]["query"],
        "prompt_type": "sql_correction",
        "template_vars": {
            "original_query": context["input"]["query"],
            "wrong_sql": wrong_sql,
            "error_message": result_data.get("error") or "",
            "error_type": result_data.get("error_type") or "",
            "table_info": table_info,
        }
    }

    correction_raw = execute_mcp("llm", **correction_args)
    correction_data = _parse_json_result(correction_raw)
    correction_thought = {
        "step": step_num + 1.1,
        "step_type": "sql_correction",
        "decision": f"SOP 步骤 {step_num} [{step_name}]：SQL 执行失败，调用 LLM 纠错",
        "reason": "SQL 执行失败后自动尝试修正一次",
        "mcp_input": correction_args,
        "mcp_output": correction_raw,
        "llm_output": correction_data.get("text", "") if isinstance(correction_data, dict) else "",
    }
    _append_thought(thought_process, correction_thought)

    if not isinstance(correction_data, dict) or correction_data.get("success") is False:
        return None

    corrected_sql = _strip_sql_fence(correction_data.get("text") or correction_data.get("data") or "")
    if not corrected_sql:
        return None

    retry_args = {**resolved_args, "query": corrected_sql}
    retry_raw = execute_mcp("sql_executor", **retry_args)
    retry_data = _parse_json_result(retry_raw)
    retry_thought = {
        "step": step_num + 1.2,
        "step_type": "execute_mcp",
        "decision": f"SOP 步骤 {step_num} [{step_name}]：使用修正 SQL 重试原子工具 [sql_executor]",
        "reason": "使用 SQL 纠错结果重试一次",
        "mcp_input": retry_args,
        "mcp_output": retry_raw,
        "llm_output": "",
    }
    _append_thought(thought_process, retry_thought)
    return retry_raw, retry_data, retry_args


# ==================== LangGraph State ====================

@dataclass
class AgentState(TypedDict):
    """Agent State"""
    messages: Sequence[dict]           # Conversational history
    selected_skill: Optional[str]      # Dynamic selected Skill
    selected_mcp: Optional[str]        # Standard matching mcp (fallback display)
    mcp_input: Optional[dict]          # Input parameters
    mcp_result: Optional[str]          # Executed result
    thought_process: List[dict]        # Full visual thought chain
    step_type: str                   # Current step type
    is_final: bool                   # Is workflow complete
    web_search_enabled: bool          # Whether current turn may use web search


# ==================== LLM Call Wrapper ====================

class DeepSeekLLM:
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        config = get_config()
        self.api_key = api_key or config.model.api_key
        self.base_url = base_url
        self.model = config.model.model

    def invoke(self, messages: list) -> dict:
        import httpx
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": messages, "temperature": 0.2, "max_tokens": 2048}

        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()


# ==================== LangGraph Nodes ====================

def step1_select_skill(state: AgentState) -> AgentState:
    """
    Step 1: LLM Dynamic Router to choose appropriate Skill
    """
    messages = list(state["messages"])
    user_question = _current_user_question(messages)
    history_messages = _history_before_current_user(messages)
    web_search_enabled = bool(state.get("web_search_enabled", False))
    contextual_skill, contextual_reason = _route_contextual_followup(user_question, history_messages)

    # Load dynamic registered skills
    skills_list = list_skills()
    skill_desc_list = []
    for s in skills_list:
        tools_list = s.get("mcpTools", s.get("mcp_tools", []))
        skill_desc_list.append(f"- **{s['name']}**: {s['description']} (包含原子工具: {', '.join(tools_list)})")
    skill_list_prompt = "\n".join(skill_desc_list)

    system_prompt = f"""你是一个高级智能助手，擅长根据用户提问，从以下注册的能力单元（Skills）中挑选最合适的一个。

可用技能（Skills）：
{skill_list_prompt}

**工作流程：**
1. 深入分析用户问题的意图与统计诉求。
2. 从上述可用技能中选择最精确匹配的一个。输出的技能名必须是上述技能配置中定义的英文 name 标识，例如：data_query、yoy_yoy_analysis 或 chat。
3. 详细给出你选择这个技能的业务原因。

**多轮追问规则：**
- 如果当前问题是“和其他竞品对比呢”“为什么会这样”“继续展开原因”等短追问，必须结合最近会话上下文理解，不能按孤立闲聊处理。
- 如果上文已有内部数据结果，当前问题只要求竞品/外部/公开资料对比，应选择 web_compare_analysis，复用上文数据，不要重新选择 data_web_compare_analysis。
- 只有当前这一句话本身明确包含新的内部数据查询对象、时间和指标，同时又要求联网/竞品/外部数据时，才选择 data_web_compare_analysis。
- 在当前业务场景中，用户说“国际”默认指“广汽国际”，不要理解为宏观国际形势。

**输出格式必须符合以下契约结构：**
[SKILL]技能英文Name[/SKILL]
[REASON]选择理由[/REASON]

例如：
用户问题：本月中东公司销量多少？
输出：
[SKILL]data_query[/SKILL]
[REASON]用户提问涉及销量数据查询，符合 data_query 技能场景[/REASON]
"""

    history_text = _format_recent_memory(history_messages) or "无"
    router_prompt = render_prompt(
        "router",
        {
            "skill_list": skill_list_prompt,
            "history": history_text,
            "query": user_question,
        },
    )
    if router_prompt:
        full_messages = [{"role": "user", "content": router_prompt}]
    else:
        full_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"最近会话上下文：\n{history_text}\n\n当前用户问题：{user_question}"},
        ]

    try:
        config = get_config()
        forced_skill, forced_reason = _route_by_web_toggle(user_question, history_messages, web_search_enabled)
        if forced_skill == "__web_disabled__":
            final_answer = "当前问题需要联网检索。请先开启联网搜索开关后再发送，我会结合公开资料进行回答。"
            thought_entry = {
                "step": 1,
                "step_type": "select_skill",
                "decision": "联网搜索开关关闭，已拦截联网检索请求",
                "reason": forced_reason,
                "llm_output": "[WEB_SEARCH_DISABLED]",
            }
            _emit_callback(thought_entry)
            return {
                **state,
                "messages": messages + [{"role": "assistant", "content": final_answer}],
                "selected_skill": None,
                "thought_process": state["thought_process"] + [thought_entry],
                "step_type": "select_skill",
                "is_final": True,
            }
        if forced_skill:
            content = f"[SKILL]{forced_skill}[/SKILL]\n[REASON]{forced_reason}[/REASON]"
        elif contextual_skill and _skill_allowed_by_web_toggle(contextual_skill, web_search_enabled):
            content = f"[SKILL]{contextual_skill}[/SKILL]\n[REASON]{contextual_reason}[/REASON]"
        elif config.mock_enabled or not config.model.api_key:
            return mock_select_skill(state)
        else:
            llm = DeepSeekLLM(api_key=config.model.api_key)
            response = llm.invoke(full_messages)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"LLM Routing failed, falling back to Mock. Error: {e}")
        return mock_select_skill(state)

    # Parse LLM output
    skill_match = re.search(r'\[SKILL\](.*?)\[/SKILL\]', content, re.DOTALL)
    reason_match = re.search(r'\[REASON\](.*?)\[/REASON\]', content, re.DOTALL)

    selected_skill = skill_match.group(1).strip() if skill_match else None
    reason = reason_match.group(1).strip() if reason_match else ""

    # Verify if selected skill is valid
    valid_skill_names = [s["name"] for s in skills_list]
    if selected_skill and selected_skill not in valid_skill_names:
        # Try finding case-insensitive or fuzzy match
        matched = False
        for valid_name in valid_skill_names:
            if valid_name.lower() == selected_skill.lower():
                selected_skill = valid_name
                matched = True
                break
        if not matched:
            selected_skill = None

    if selected_skill and not _skill_allowed_by_web_toggle(selected_skill, web_search_enabled):
        final_answer = "当前问题需要联网检索。请先开启联网搜索开关后再发送，我会结合公开资料进行回答。"
        thought_entry = {
            "step": 1,
            "step_type": "select_skill",
            "decision": "联网搜索开关关闭，已拦截联网类技能",
            "reason": f"路由器选择了 {selected_skill}，但本轮联网搜索开关关闭。",
            "llm_output": content,
        }
        _emit_callback(thought_entry)
        return {
            **state,
            "messages": messages + [{"role": "assistant", "content": final_answer}],
            "selected_skill": None,
            "thought_process": state["thought_process"] + [thought_entry],
            "step_type": "select_skill",
            "is_final": True,
        }

    # Record first thought step
    thought_entry = {
        "step": 1,
        "step_type": "select_skill",
        "decision": f"第一层决策：选择业务技能单元 [{selected_skill}]" if selected_skill else "未选择合适技能",
        "reason": reason or "大模型完成意图分析，启动工作流调度",
        "llm_output": content,
    }

    # Trigger streaming callback
    _emit_callback(thought_entry)

    return {
        **state,
        "messages": messages + [{"role": "assistant", "content": f"[技能意图路由] {selected_skill}"}],
        "selected_skill": selected_skill,
        "thought_process": state["thought_process"] + [thought_entry],
        "step_type": "select_skill",
        "is_final": selected_skill is None,
    }


def step2_run_workflow(state: AgentState) -> AgentState:
    """
    Step 2: Generic standard Workflow Engine node.
    Performs step-by-step SOP execution with context piping and outputs the thought chain.
    """
    skill_name = state.get("selected_skill")
    messages = list(state["messages"])
    user_question = _current_user_question(messages)
    history_messages = _history_before_current_user(messages)
    workflow_query = _query_with_memory(user_question, history_messages)

    skill_config = get_skill(skill_name)
    if not skill_config:
        return {
            **state,
            "is_final": True,
            "messages": messages + [{"role": "assistant", "content": f"未找到技能配置: {skill_name}"}],
            "step_type": "workflow_execution"
        }

    steps = sorted(skill_config["flow"]["steps"], key=lambda x: x["step"])
    thought_process = list(state["thought_process"])

    # Global context for resolving variables
    context = {
        "input": {
            "query": workflow_query,
            "current_query": user_question,
            "conversation_context": _format_recent_memory(history_messages),
        },
        "steps": {}
    }

    last_step_output = ""
    last_mcp = ""
    last_args = {}

    for idx, step_item in enumerate(steps):
        step_num = step_item["step"]
        step_name = step_item["name"]
        mcp_name = step_item["mcp"]
        raw_args = step_item.get("arguments", {})

        # 1. Resolve variable mappings (Data Piping)
        resolved_args = resolve_variables(raw_args, context)

        # 2. Invoke atomic MCP
        print(f"[Workflow Engine] Executing Step {step_num}: {step_name} via {mcp_name}...")
        result_str = execute_mcp(mcp_name, **resolved_args)

        result_data = _parse_json_result(result_str)

        # Write step output back to global context
        context["steps"][step_name] = {
            "output": result_data
        }

        last_step_output = result_str
        last_mcp = mcp_name
        last_args = resolved_args

        step_thought = _build_mcp_thought(step_num, step_name, step_item, mcp_name, resolved_args, result_str, result_data)
        _append_thought(thought_process, step_thought)

        if isinstance(result_data, dict) and result_data.get("success") is False:
            correction_result = _try_correct_sql(step_num, step_name, step_item, resolved_args, result_data, context, thought_process)
            if correction_result:
                result_str, result_data, resolved_args = correction_result
                context["steps"][step_name] = {
                    "output": result_data
                }
                last_step_output = result_str
                last_mcp = mcp_name
                last_args = resolved_args
                if not (isinstance(result_data, dict) and result_data.get("success") is False):
                    continue

            error_message = result_data.get("error") or "MCP 执行失败"
            error_type = result_data.get("error_type") or "MCPError"
            final_answer = f"工作流已中断：步骤 {step_num} [{step_name}] 调用 {mcp_name} 失败。错误类型：{error_type}。错误信息：{error_message}"
            error_thought = {
                "step": step_num + 2,
                "step_type": "workflow_error",
                "decision": "关键 MCP 失败，工作流已中断",
                "final_answer": final_answer,
                "error": error_message,
                "error_type": error_type,
                "failed_step": step_name,
                "failed_mcp": mcp_name,
            }
            thought_process.append(error_thought)

            # Trigger streaming callback
            _emit_callback(error_thought)
            return {
                **state,
                "messages": messages + [{"role": "assistant", "content": final_answer}],
                "selected_mcp": mcp_name,
                "mcp_input": resolved_args,
                "mcp_result": result_str,
                "thought_process": thought_process,
                "step_type": "workflow_execution",
                "is_final": True
            }

    # Extract final answer from the workflow steps
    final_answer = ""

    # Helper to extract text from step outputs
    def _extract_step_text(step_output):
        if isinstance(step_output, str):
            try:
                step_output = json.loads(step_output)
            except Exception:
                return step_output
        if isinstance(step_output, dict):
            return step_output.get("text") or step_output.get("data") or step_output.get("result") or str(step_output)
        return str(step_output)

    # 1. Custom structured formatting for data_query skill
    if "data_interpretation" in context["steps"] and "data_scope_explanation" in context["steps"]:
        interpretation_text = _extract_step_text(context["steps"]["data_interpretation"]["output"])
        scope_text = _extract_step_text(context["steps"]["data_scope_explanation"]["output"])
        
        table_md = ""
        if "sql_execution" in context["steps"]:
            table_md = _extract_step_text(context["steps"]["sql_execution"]["output"])
            
        final_answer = ""
        if table_md and "|" in table_md:
            final_answer += f"### 📊 数据查询结果\n{table_md}\n\n"
            
        final_answer += f"### 💡 业务分析与解读\n{interpretation_text}\n\n"
        final_answer += f"### 🛡️ 数据统计口径说明\n> {scope_text}"
        
    # 2. Custom structured formatting for YoY analysis skill
    elif "yoy_analysis" in context["steps"]:
        yoy_analysis_text = _extract_step_text(context["steps"]["yoy_analysis"]["output"])
        
        table_md = ""
        if "sql_execution" in context["steps"]:
            table_md = _extract_step_text(context["steps"]["sql_execution"]["output"])
            
        final_answer = ""
        if table_md and "|" in table_md:
            final_answer += f"### 📊 同环比计算数据\n{table_md}\n\n"
            
        final_answer += f"### 💡 同环比深度解读\n{yoy_analysis_text}"

    # 3. Default fallback for other skills / chat
    else:
        try:
            last_data = json.loads(last_step_output)
            if isinstance(last_data, dict):
                if "text" in last_data and last_data["text"]:
                    final_answer = last_data["text"]
                elif "data" in last_data and last_data["data"]:
                    final_answer = last_data["data"]
                elif "result" in last_data and last_data["result"]:
                    final_answer = str(last_data["result"])
                else:
                    final_answer = str(last_data)
            else:
                final_answer = str(last_data)
        except Exception:
            final_answer = last_step_output

    # Append final visual thought chain
    final_thought = {
        "step": len(steps) + 2,
        "step_type": "final_answer",
        "decision": "工作流执行完毕，生成最终业务解答",
        "final_answer": final_answer
    }
    thought_process.append(final_thought)

    # Trigger streaming callback
    _emit_callback(final_thought)

    return {
        **state,
        "messages": messages + [{"role": "assistant", "content": final_answer}],
        "selected_mcp": last_mcp,
        "mcp_input": last_args,
        "mcp_result": last_step_output,
        "thought_process": thought_process,
        "step_type": "workflow_execution",
        "is_final": True
    }


# ==================== Mock Rules Fallback ====================

def mock_select_skill(state: AgentState) -> AgentState:
    """Mock Router fallback in case API key is missing"""
    messages = list(state["messages"])
    user_question = _current_user_question(messages)
    history_messages = _history_before_current_user(messages)
    recent_history_text = _recent_history_text(history_messages)
    contextual_skill, contextual_reason = _route_contextual_followup(user_question, history_messages)
    web_search_enabled = bool(state.get("web_search_enabled", False))
    forced_skill, forced_reason = _route_by_web_toggle(user_question, history_messages, web_search_enabled)

    selected_skill = "chat"
    reason = "未检测到 API Key，触发本地意图分析规则系统。"

    # Check keyword patterns
    q_lower = user_question.lower()
    web_keywords = [
        "联网", "网上", "网络", "公开资料", "公开信息", "搜索", "搜一下", "查一下",
        "新闻", "最新", "今天", "行业趋势", "行业情况", "外部信息", "外部数据"
    ]
    external_market_keywords = [
        "全球", "全球市场", "国际市场", "海外市场", "公开市场", "行业市场",
        "市场表现", "市场情况", "卖得怎么样", "卖的怎么样"
    ]
    context_keywords = ["刚才", "上文", "上面", "之前", "前面", "这个结果", "真实数据", "内部数据", "对比", "比较", "解释", "分析"]
    data_keywords = ["销量", "终端量", "批发量", "库存", "订单", "排产", "达成", "销售", "卖", "表现", "国家", "大区", "公司"]
    internal_subject_keywords = ["广汽国际", "国际", "中东公司", "内部", "真实数据", "内部数据", "我司", "本公司"]
    followup_keywords = ["为什么", "原因", "继续", "展开", "深挖", "详细", "再分析", "建议", "怎么办", "怎么做", "接着", "进一步", "然后呢", "这个呢", "那呢"]
    has_web_intent = any(k in q_lower for k in web_keywords)
    has_external_market_intent = any(k in q_lower for k in external_market_keywords)
    has_context_compare_intent = any(k in q_lower for k in context_keywords)
    has_data_intent = any(k in q_lower for k in data_keywords)
    has_internal_subject = any(k in q_lower for k in internal_subject_keywords)
    has_followup_intent = any(k in q_lower for k in followup_keywords)
    recent_has_data_context = any(k in recent_history_text for k in data_keywords + ["内部真实数据", "内部数据查询", "SQL", "数据查询结果"])
    recent_has_web_context = any(k in recent_history_text for k in web_keywords + ["联网检索", "外部公开资料", "竞品", "公开资料"])

    if forced_skill == "__web_disabled__":
        final_answer = "当前问题需要联网检索。请先开启联网搜索开关后再发送，我会结合公开资料进行回答。"
        thought_entry = {
            "step": 1,
            "step_type": "select_skill",
            "decision": "联网搜索开关关闭，已拦截联网检索请求",
            "reason": forced_reason,
            "llm_output": "[WEB_SEARCH_DISABLED]",
        }
        _emit_callback(thought_entry)
        return {
            **state,
            "messages": messages + [{"role": "assistant", "content": final_answer}],
            "selected_skill": None,
            "thought_process": state["thought_process"] + [thought_entry],
            "step_type": "select_skill",
            "is_final": True,
        }
    if forced_skill:
        selected_skill = forced_skill
        reason += f" {forced_reason}"
    elif contextual_skill and _skill_allowed_by_web_toggle(contextual_skill, web_search_enabled):
        selected_skill = contextual_skill
        reason += f" {contextual_reason}"
    elif web_search_enabled and (has_web_intent or has_external_market_intent) and has_data_intent and has_internal_subject:
        selected_skill = "data_web_compare_analysis"
        reason += " 检测到内部主体/业务指标与全球或公开市场表现的复合诉求，需要内部数据和联网公开资料共同支撑，路由至[内部数据与联网竞品对比分析]技能。"
    elif web_search_enabled and has_web_intent and has_context_compare_intent:
        selected_skill = "web_compare_analysis"
        reason += " 检测到联网信息和上文/真实数据对比分析诉求，路由至[联网对比分析]技能。"
    elif web_search_enabled and has_web_intent:
        selected_skill = "web_search_answer"
        reason += " 检测到明确联网检索诉求，路由至[联网检索问答]技能。"
    elif web_search_enabled and has_followup_intent and recent_has_data_context and recent_has_web_context:
        selected_skill = "web_compare_analysis"
        reason += " 检测到当前问题是对上一轮内外部对比分析的追问，继承会话上下文并路由至[联网对比分析]技能。"
    elif has_followup_intent and recent_has_data_context:
        selected_skill = "data_query"
        reason += " 检测到当前问题是对上一轮数据分析的追问，继承会话上下文并路由至[数据查询与分析]技能。"
    elif has_data_intent:
        if any(k in q_lower for k in ["同比", "环比", "增长"]):
            selected_skill = "yoy_yoy_analysis"
            reason += " 检测到业务指标及同比/环比关键词，路由至[同环比分析]技能。"
        else:
            selected_skill = "data_query"
            reason += " 检测到销量/库存/订单等业务指标，路由至[数据查询与分析]技能。"
    elif any(k in q_lower for k in ["同比", "环比", "增长"]):
        selected_skill = "yoy_yoy_analysis"
        reason += " 检测到同比/环比计算诉求，路由至[同环比分析]技能。"

    thought_entry = {
        "step": 1,
        "step_type": "select_skill",
        "decision": f"第一层决策（规则引擎模拟）：选择技能 [{selected_skill}]",
        "reason": reason,
        "llm_output": f"[RULE] Selected Skill: {selected_skill} because of rule matching.",
    }

    # Trigger streaming callback
    _emit_callback(thought_entry)

    return {
        **state,
        "messages": messages + [{"role": "assistant", "content": f"[技能意图路由] {selected_skill}"}],
        "selected_skill": selected_skill,
        "thought_process": state["thought_process"] + [thought_entry],
        "step_type": "select_skill",
        "is_final": selected_skill is None,
    }


# ==================== LangGraph Compiler ====================

try:
    from langgraph.graph import StateGraph, END

    def build_graph():
        workflow = StateGraph(AgentState)

        # Register nodes
        workflow.add_node("step1_skill", step1_select_skill)
        workflow.add_node("step2_run_workflow", step2_run_workflow)

        # Set entrypoint
        workflow.set_entry_point("step1_skill")

        # Routing edges
        def after_step1(state: AgentState) -> Literal["step2_run_workflow", END]:
            if state.get("is_final", False) or not state.get("selected_skill"):
                return END
            return "step2_run_workflow"

        workflow.add_conditional_edges(
            "step1_skill", 
            after_step1, 
            {
                "step2_run_workflow": "step2_run_workflow", 
                END: END
            }
        )
        
        workflow.add_edge("step2_run_workflow", END)

        return workflow.compile()

    graph = build_graph()

except ImportError as e:
    graph = None
    print(f"LangGraph not installed or import error: {e}")


# ==================== Executable Run Agent Function ====================

def run_agent(question: str, callback=None, history: Sequence[dict] | None = None, web_search_enabled: bool = False):
    """Main execution engine method with optional step-by-step callback"""
    callback_token = _ACTIVE_CALLBACK.set(callback)
    if graph is None:
        _ACTIVE_CALLBACK.reset(callback_token)
        return {"error": "LangGraph is not configured correctly."}

    initial_state = AgentState(
        messages=_build_agent_messages(question, history),
        selected_skill=None,
        selected_mcp=None,
        mcp_input=None,
        mcp_result=None,
        thought_process=[],
        step_type="start",
        is_final=False,
        web_search_enabled=web_search_enabled,
    )

    final_state = None
    try:
        for event in graph.stream(initial_state, {"recursion_limit": 30}):
            for node_name, node_state in event.items():
                if isinstance(node_state, dict) and "thought_process" in node_state:
                    final_state = node_state
    except Exception as e:
        return {"error": f"Engine execution failed: {str(e)}"}
    finally:
        _ACTIVE_CALLBACK.reset(callback_token)

    return final_state or {"error": "Execution did not return a valid state."}


if __name__ == "__main__":
    # Test query
    result = run_agent("本月中东公司销量多少？")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
