"""
LangGraph CoT Agent - Standard SOP + MCP Double-layer Execution Engine UI

Features:
- Dynamic registries for both Skills and MCP tools
- Dynamic pipeline variable piping and execution tracking
- Collapsible detailed thinking chain (CoT) cards
- Real-time environment variables configuration
- Dynamic Mermaid execution flowchart
"""

import streamlit as st
import json
import os

from langgraph_cot import run_agent
from skills import list_skills
from mcps import list_mcps

# ==================== Page Configuration & Styling ====================
st.set_page_config(
    page_title="Standard CoT & MCP Double-layer Orchestrator",
    page_icon="🧠",
    layout="wide"
)

# Custom premium CSS
st.markdown("""
<style>
    /* Premium visual styles */
    .stApp {
        background-color: #0f111a;
        color: #e2e8f0;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
    }
    .main-title {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #1e2230;
        border: 1px solid #2d3142;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-val {
        color: #a855f7 !important;
        font-size: 1.8rem;
        font-weight: bold;
    }
    /* Expander style overrides */
    .streamlit-expanderHeader {
        background-color: #1b1e2c !important;
        border: 1px solid #2d3246 !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
    }
    .streamlit-expanderContent {
        background-color: #121420 !important;
        border: 1px solid #2d3246 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ==================== Sidebar: Dynamic Registries & Config ====================
with st.sidebar:
    st.markdown('<h2 style="font-size:1.8rem; margin-bottom:0.5rem;">🧠 Agent Config</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#94a3b8; font-size:0.9rem;">Model Context Protocol (MCP) & SOP Engine</p>', unsafe_allow_html=True)
    st.markdown("---")

    # API Configuration
    st.subheader("🔑 凭证配置")
    api_key = st.text_input("DeepSeek / OpenAI API Key", type="password", value=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "")
    if api_key:
        os.environ["DEEPSEEK_API_KEY"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ 凭证载入成功")
    else:
        st.warning("⚠️ 缺省 API Key 将自动启用 Mock 路由规则")

    st.markdown("---")

    # Dynamic Skills Panel
    st.subheader("📦 已导入 Skills (业务 SOP 层)")
    skills = list_skills()
    if not skills:
        st.info("暂未加载任何 SOP 技能")
    for s in skills:
        with st.expander(f"🔮 {s.get('name')}"):
            st.markdown(f"**描述:** {s.get('description')}")
            st.markdown(f"**输出类型:** `{s.get('output_type', '无')}`")
            mcp_tools = s.get("mcpTools", s.get("mcp_tools", []))
            st.markdown(f"**包含原子工具:** `{', '.join(mcp_tools)}`")
            # Step pipeline details
            st.markdown("**SOP 管道流:**")
            steps = s.get("flow", {}).get("steps", [])
            for step_item in sorted(steps, key=lambda x: x["step"]):
                st.caption(f"`Step {step_item['step']}`: {step_item['name']} ({step_item['mcp']})")

    st.markdown("---")

    # Dynamic MCPs Panel
    st.subheader("🔧 已导入 MCPs (原子工具层)")
    mcps = list_mcps()
    if not mcps:
        st.info("暂未加载任何 MCP 原子工具")
    for m in mcps:
        with st.expander(f"🛠️ {m.get('name')}"):
            st.markdown(f"**描述:** {m.get('description')}")
            st.markdown(f"**分类:** `{m.get('category', 'utility')}`")
            if "inputSchema" in m:
                st.markdown("**输入参数定义:**")
                st.json(m["inputSchema"])


# ==================== Main UI Layout ====================
st.markdown('<h1 class="main-title">🧠 Standard CoT & MCP Double-layer Engine</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">完全解耦的声明式 SOP 工作流引擎 • 兼容 Anthropic MCP 协议标准 • 可视化思维链调试面板</p>', unsafe_allow_html=True)

# Examples / Quick Tests Grid
st.subheader("🎯 快速测试")
cols = st.columns(4)
examples = [
    ("📊 数据分析", "本月中东公司销量多少？", 0),
    ("⚖️ 同环比分析", "本月终端量同比去年怎么样？", 1),
    ("📖 知识库检索", "什么是库存周转率？", 2),
    ("💬 专业闲聊", "汽车保养一般多少公里做一次？", 3)
]

for label, q, col_idx in examples:
    if cols[col_idx].button(label, use_container_width=True):
        st.session_state.question = q

# Query Input Box
question = st.text_input("💬 请输入您的问题：", value=st.session_state.get("question", ""), placeholder="例如：本月中东公司销量多少？", key="input_query")

# Update st.session_state if input changes
if question != st.session_state.get("question", ""):
    st.session_state.question = question

if st.button("🚀 启动双层 SOP 决策", type="primary") and question:
    with st.spinner("🧠 声明式双层 SOP 引擎正在检索、解析并调度执行..."):
        result = run_agent(question)

        if "error" in result:
            st.error(result["error"])
        else:
            thought_process = result.get("thought_process", [])
            selected_skill = result.get("selected_skill")
            selected_mcp = result.get("selected_mcp")
            is_mocked = not (os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"))

            # Metrics / Result Summary Overview
            st.markdown("### 🎯 SOP 执行总览")
            sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
            with sum_col1:
                st.metric("激活 SOP 技能", selected_skill or "未知/闲聊", delta="Mock模式" if is_mocked else "大模型路由")
            with sum_col2:
                st.metric("调用的最后一个工具", selected_mcp or "无")
            with sum_col3:
                st.metric("总执行步骤数", f"{len(thought_process)} 步")
            with sum_col4:
                st.metric("运行状态", "成功", delta_color="normal")

            st.divider()

            # Dynamic Flowchart (Mermaid Rendering)
            st.markdown("### 🔄 SOP 动态执行图")
            mermaid_code = ["graph TD"]
            # Apply styling classes to nodes
            mermaid_code.append("    classDef start fill:#4f46e5,stroke:#fff,stroke-width:2px,color:#fff;")
            mermaid_code.append("    classDef process fill:#3b82f6,stroke:#fff,stroke-width:1px,color:#fff;")
            mermaid_code.append("    classDef active fill:#10b981,stroke:#fff,stroke-width:2px,color:#fff;")
            mermaid_code.append("    classDef endNode fill:#ec4899,stroke:#fff,stroke-width:2px,color:#fff;")
            
            mermaid_code.append(f'    Start(["💬 {question[:20]}..."]) --> Router{{"🧠 意图路由层"}}')
            
            if selected_skill:
                mermaid_code.append(f'    Router -->|选择技能: {selected_skill}| Skill["📦 {selected_skill} SOP 管道"]')
                
                # Retrieve execution steps from thought process
                execute_steps = [s for s in thought_process if s.get("step_type") == "execute_mcp"]
                
                prev_node = "Skill"
                for s in execute_steps:
                    step_num = s.get("step", 0)
                    node_id = f"Step_{step_num}"
                    
                    # Extract decision tool name
                    mcp_name = s.get("decision", "").split("调用原子工具 [")[-1].replace("]", "")
                    mcp_name = mcp_name.split()[0] if mcp_name else "tool"
                    
                    # Extract friendly step name if possible
                    step_name_match = s.get("decision", "")
                    step_name = step_name_match.split("[")[1].split("]")[0] if "[" in step_name_match else f"step_{step_num-1}"
                    
                    mermaid_code.append(f'    {prev_node} --> {node_id}["⚙️ {step_num-1}: {step_name} ({mcp_name})"]')
                    mermaid_code.append(f'    class {node_id} process;')
                    prev_node = node_id
                
                mermaid_code.append(f'    {prev_node} --> Answer["✅ 最终回答"]')
                mermaid_code.append('    class Answer endNode;')
            else:
                mermaid_code.append('    Router -->|未匹配技能| Answer["💬 直接回答"]')
                mermaid_code.append('    class Answer endNode;')
            
            mermaid_code.append('    class Start start;')
            mermaid_code.append('    class Router active;')
            mermaid_code.append('    class Skill active;')
            
            mermaid_str = "\n".join(mermaid_code)
            st.markdown(f"""
            ```mermaid
            {mermaid_str}
            ```
            """)

            st.divider()

            # Thinking Chain step-by-step
            st.markdown("### 📋 思维链与 SOP 执行明细")

            for step in thought_process:
                step_num = step.get("step", 0)
                step_type = step.get("step_type", "")

                if step_type == "select_skill":
                    icon = "🔍"
                    title = "第一层：意图识别路由 (Intent Routing)"
                    status_type = "info"
                elif step_type == "execute_mcp":
                    icon = "⚙️"
                    # Get friendly step name
                    decision_str = step.get("decision", "")
                    title = f"第二层 SOP 步骤 {step_num-1}: {decision_str}"
                    status_type = "success"
                elif step_type == "final_answer":
                    icon = "✅"
                    title = "第三层：输出生成与口径对齐 (Final Interpretation)"
                    status_type = "success"
                else:
                    icon = "📌"
                    title = f"步骤 {step_num}"
                    status_type = "normal"

                with st.expander(f"{icon} **{title}**", expanded=True):
                    # Show step description or reason
                    if "reason" in step and step["reason"]:
                        st.markdown(f"**💡 SOP 指令定义 / 决策原因:**\n> {step['reason']}")

                    # Show detailed inputs if executed an MCP
                    if "mcp_input" in step and step["mcp_input"]:
                        st.markdown("**📥 动态传参 (Piped Arguments):**")
                        st.json(step["mcp_input"])

                    # Show raw output of MCP
                    if "mcp_output" in step:
                        st.markdown("**📤 工具执行输出 (Raw Return Output):**")
                        output_raw = step["mcp_output"]
                        try:
                            # Try rendering pretty JSON if valid JSON
                            parsed_out = json.loads(output_raw)
                            st.json(parsed_out)
                            
                            # Additional visualization helper for SQL Query results
                            if isinstance(parsed_out, dict) and "data" in parsed_out:
                                db_data = parsed_out["data"]
                                if isinstance(db_data, str) and "|" in db_data:
                                    st.markdown("**📊 数据库查询表格视图:**")
                                    st.markdown(db_data)
                        except Exception:
                            # Raw text fallback
                            st.code(output_raw, language="text")

                    # Highlighted generated intermediate code / outputs
                    if "llm_output" in step and step["llm_output"]:
                        st.markdown("**✨ 步骤生成的中间产物 / SQL:**")
                        st.markdown(step["llm_output"])

                    # If final answer is reached
                    if "final_answer" in step:
                        st.markdown("---")
                        st.markdown('<h3 style="color:#10b981 !important;">✅ 最终业务解答 (Aligned Answer)</h3>', unsafe_allow_html=True)
                        st.info(step["final_answer"])

            st.balloons()


# ==================== Footer / Architecture Info ====================
st.markdown("---")
st.markdown('<h3 style="text-align: center;">🏗️ 行业标准的声明式双层 SOP 决策系统 </h3>', unsafe_allow_html=True)

arch_col1, arch_col2 = st.columns(2)

with arch_col1:
    st.markdown("""
    **SOP 业务能力单元 (Skill)**
    - **声明式配置**: 以标准 JSON/YAML 声明 SOP 每一阶段的指令描述、调用的原子 MCP、以及传参规则。
    - **数据管道传参 (Data Piping)**: 自动提取上下文历史数据，支持 `{{steps.step_name.output.field}}` 的高级语法规则，并能保持原生字典/列表结构数据。
    - **完全复用**: 可以作为成熟、高内聚的能力直接移植入主 Agent 决策池。
    """)

with arch_col2:
    st.markdown("""
    **Model Context Protocol (MCP)**
    - **高度标准化**: 完全符合 Anthropic MCP 的标准契约定义。
    - **CamelCase InputSchema**: 采用驼峰命名并显式规范入参格式，能无缝和 Claude Desktop 或主流 MCP 服务生态对接。
    - **解耦设计**: 原子工具细节完全对外透明，增改工具时无需变动业务流程引擎核心代码。
    """)

st.caption("Powered by Google DeepMind Advanced Agentic Coding • Standardized SOP Engine & Model Context Protocol")
