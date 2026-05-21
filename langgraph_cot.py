"""
LangGraph ReAct Agent - Standard Skill + MCP Double-layer Execution Engine

Core Flow:
Question → LLM dynamic routing to Skill → Standard Workflow Engine executes steps in Skill (resolving variables) → Streamlit thought chain rendering
"""

import json
import os
import re
from typing import TypedDict, Sequence, Literal, Any
from dataclasses import dataclass

# Import registered MCPs and Skills
from mcps import execute_mcp, list_mcps
from skills import get_skill, list_skills


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


# ==================== LangGraph State ====================

@dataclass
class AgentState(TypedDict):
    """Agent State"""
    messages: Sequence[dict]           # Conversational history
    selected_skill: str | None        # Dynamic selected Skill
    selected_mcp: str | None         # Standard matching mcp (fallback display)
    mcp_input: dict | None            # Input parameters
    mcp_result: str | None            # Executed result
    thought_process: list[dict]       # Full visual thought chain
    step_type: str                   # Current step type
    is_final: bool                   # Is workflow complete


# ==================== LLM Call Wrapper ====================

class DeepSeekLLM:
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url

    def invoke(self, messages: list) -> dict:
        import httpx
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {"model": "deepseek-chat", "messages": messages, "temperature": 0.2, "max_tokens": 2048}

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
    user_question = messages[-1].get("content", "") if messages else ""

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

**输出格式必须符合以下契约结构：**
[SKILL]技能英文Name[/SKILL]
[REASON]选择理由[/REASON]

例如：
用户问题：本月中东公司销量多少？
输出：
[SKILL]data_query[/SKILL]
[REASON]用户提问涉及销量数据查询，符合 data_query 技能场景[/REASON]
"""

    full_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_question}]

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return mock_select_skill(state)

        llm = DeepSeekLLM(api_key=api_key)
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

    # Record first thought step
    thought_entry = {
        "step": 1,
        "step_type": "select_skill",
        "decision": f"第一层决策：选择业务技能单元 [{selected_skill}]" if selected_skill else "未选择合适技能",
        "reason": reason or "大模型完成意图分析，启动工作流调度",
        "llm_output": content,
    }

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
    user_question = messages[0].get("content", "") if messages else ""

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
        "input": {"query": user_question},
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

        try:
            result_data = json.loads(result_str)
        except Exception:
            result_data = result_str

        # Write step output back to global context
        context["steps"][step_name] = {
            "output": result_data
        }

        last_step_output = result_str
        last_mcp = mcp_name
        last_args = resolved_args

        # 3. Compile thought step object for Streamlit front-end
        step_thought = {
            "step": step_num + 1,  # step 1 is the skill router
            "step_type": "execute_mcp",
            "decision": f"SOP 步骤 {step_num} [{step_name}]：调用原子工具 [{mcp_name}]",
            "reason": step_item["description"],
            "mcp_input": resolved_args,
            "mcp_output": result_str,
            "llm_output": ""
        }

        # If LLM MCP is called, extract output text for clear display
        if mcp_name == "llm" and isinstance(result_data, dict):
            step_thought["llm_output"] = result_data.get("text", "")
        # If N2SQL generated SQL, put in llm_output for beautiful syntax highlighting
        elif mcp_name == "n2sql" and isinstance(result_data, dict):
            step_thought["llm_output"] = f"生成的 SQL 语句：\n```sql\n{result_data.get('sql', '')}\n```"

        thought_process.append(step_thought)

    # Extract final answer from the last step
    final_answer = ""
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
    user_question = messages[-1].get("content", "") if messages else ""

    selected_skill = "chat"
    reason = "未检测到 API Key，触发本地意图分析规则系统。"

    # Check keyword patterns
    q_lower = user_question.lower()
    if any(k in q_lower for k in ["多少", "销量", "库存", "订单", "排产", "达成", "最好"]):
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

def run_agent(question: str):
    """Main execution engine method"""
    if graph is None:
        return {"error": "LangGraph is not configured correctly."}

    initial_state = AgentState(
        messages=[{"role": "user", "content": question}],
        selected_skill=None,
        selected_mcp=None,
        mcp_input=None,
        mcp_result=None,
        thought_process=[],
        step_type="start",
        is_final=False,
    )

    final_state = None
    try:
        for event in graph.stream(initial_state, {"recursion_limit": 30}):
            for node_name, node_state in event.items():
                if isinstance(node_state, dict) and "thought_process" in node_state:
                    final_state = node_state
    except Exception as e:
        return {"error": f"Engine execution failed: {str(e)}"}

    return final_state or {"error": "Execution did not return a valid state."}


if __name__ == "__main__":
    # Test query
    result = run_agent("本月中东公司销量多少？")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
