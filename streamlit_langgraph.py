"""
ChatBI Clean Agent - Minimalist SOP & MCP Double-layer Execution Engine UI

Features:
- Premium minimalist design (removed technical noise, neon borders, and complex slide-style footers).
- Real-time deep reasoning progress updates via Streamlit's native st.status connected to langgraph_cot callback.
- Auto-collapses the deep reasoning box upon completion, leaving only the pristine final answer on screen.
- Streamlined sidebar: hides advanced schemas, white-lists, and registers inside a single "Advanced Developer Tools" box.
"""

import streamlit as st
import json
import os

from langgraph_cot import run_agent
from skills import list_skills
from mcps import list_mcps
from app_config import get_config
import theme_loader


def render_markdown_table_chart(md_table: str):
    import pandas as pd
    try:
        lines = [line.strip() for line in md_table.strip().split("\n") if line.strip()]
        if len(lines) < 3:
            return
        
        headers = [h.strip() for h in lines[0].split("|")[1:-1]]
        if not headers:
            return
            
        rows_data = []
        for line in lines[2:]:
            if line.startswith("|-") or line.startswith("| -") or "---" in line:
                continue
            row = [r.strip() for r in line.split("|")[1:-1]]
            if len(row) == len(headers):
                rows_data.append(row)
                
        if not rows_data:
            return
            
        df = pd.DataFrame(rows_data, columns=headers)
        
        for col in df.columns:
            try:
                cleaned = df[col].astype(str).str.replace("%", "").str.replace(",", "").str.strip()
                df[col] = pd.to_numeric(cleaned)
            except Exception:
                pass
                
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols and len(df) > 0:
            st.markdown("<p style='font-size:0.95rem; font-weight:600; color:#ffffff; margin-top:1.2rem; margin-bottom:0.5rem;'>📊 动态数据直观图表</p>", unsafe_allow_html=True)
            
            categorical_cols = [c for c in df.columns if c not in numeric_cols]
            if categorical_cols:
                x_col = categorical_cols[0]
                df_chart = df.set_index(x_col)[numeric_cols]
            else:
                df_chart = df[numeric_cols]
                
            st.bar_chart(df_chart, use_container_width=True)
    except Exception:
        pass

# ==================== Page Configuration & Pristine CSS ====================
st.set_page_config(
    page_title="ChatBI 智能数据助理",
    page_icon="🧠",
    layout="wide"
)

# Custom minimalist premium dark styling (Gemini & ChatGPT Soft Grey Dark Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Sleek minimalist soft dark styling (Gemini Style) */
    .stApp {
        background-color: #131314 !important;
        color: #e3e3e3 !important;
        font-family: 'Inter', 'Outfit', sans-serif !important;
    }
    
    /* Typography override */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: -0.015em;
    }
    
    /* Elegant Title Gradient matching Gemini Advanced */
    .main-title {
        font-size: 2.8rem !important;
        font-weight: 600 !important;
        background: linear-gradient(75deg, #1ba1e2, #a777e3, #f472b6) !webkit-linear-gradient(75deg, #1ba1e2, #a777e3, #f472b6) !important;
        background: linear-gradient(75deg, #4285f4, #9b51e0, #ff8c94) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-align: center;
        margin-bottom: 0.1rem;
    }
    
    .subtitle {
        color: #c4c7c5 !important;
        font-size: 1.05rem !important;
        margin-bottom: 2.5rem !important;
        text-align: center !important;
        font-weight: 300 !important;
    }
    
    /* Sidebar Overrides (Gemini style panel) */
    section[data-testid="stSidebar"] {
        background-color: #1e1e1f !important;
        border-right: 1px solid #2d2d2e !important;
    }
    section[data-testid="stSidebar"] * {
        color: #c4c7c5 !important;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* Override Streamlit buttons to look like Gemini suggestion cards */
    .stButton > button {
        background-color: #1e1e1f !important;
        border: 1px solid #2d2d2e !important;
        border-radius: 16px !important;
        color: #e3e3e3 !important;
        padding: 1.2rem 1.1rem !important;
        height: auto !important;
        min-height: 86px !important;
        text-align: left !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        box-shadow: none !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    .stButton > button:hover {
        background-color: #2a2a2b !important;
        border-color: #444746 !important;
        color: #ffffff !important;
        transform: translateY(-2px);
    }
    .stButton > button:active {
        background-color: #202124 !important;
        transform: translateY(0);
    }
    
    /* Custom Styling for Sidebar Reset/Action Buttons */
    section[data-testid="stSidebar"] button {
        background-color: #2a2a2b !important;
        border: 1px solid #3c3c3e !important;
        border-radius: 8px !important;
        color: #e3e3e3 !important;
        padding: 0.4rem 0.8rem !important;
        min-height: auto !important;
        font-size: 0.85rem !important;
        text-align: center !important;
        justify-content: center !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: #333334 !important;
        border-color: #444746 !important;
    }

    /* Style the sidebar inputs to look like Gemini standard fields */
    div[data-testid="stSidebar"] div[data-baseweb="select"], 
    div[data-testid="stSidebar"] div[data-baseweb="base-input"],
    div[data-testid="stSidebar"] input {
        background-color: #1e1e1f !important;
        border-radius: 8px !important;
    }
    
    /* Expanders & details tags (Sleek charcoal style) */
    details {
        background-color: #1e1e1f !important;
        border: 1px solid #2d2d2e !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin: 8px 0 !important;
    }
    summary {
        color: #8ab4f8 !important; /* Gemini soft blue */
        font-weight: 500 !important;
        cursor: pointer;
        outline: none;
        font-size: 0.9em;
    }
    summary:hover {
        color: #aecbfa !important;
    }
    pre {
        background-color: #111112 !important;
        border: 1px solid #2d2d2e !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Streamlit expander overrides */
    .stExpander {
        background-color: #1e1e1f !important;
        border: 1px solid #2d2d2e !important;
        border-radius: 12px !important;
        margin-bottom: 0.8rem !important;
    }
    .stExpander > div {
        border: none !important;
    }
    
    /* Sleek status bar for thinking */
    .status-bar-clean {
        background-color: #1e1e1f !important;
        border: 1px solid #2d2d2e !important;
        border-radius: 10px !important;
        padding: 10px 14px;
        font-size: 0.9rem;
        color: #c4c7c5;
    }
    
    /* Make the chat input container perfectly match the Gemini look */
    div[data-testid="stChatInput"] {
        border-radius: 28px !important;
        background-color: #1e1e1f !important;
        border: 1px solid #3c3c3e !important;
        padding: 4px 10px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #e3e3e3 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Override chat message bubble padding & backgrounds */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 1.2rem 0.5rem !important;
        border-bottom: 1px solid #2d2d2e !important;
    }
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1a1a1b !important; /* Extremely soft contrast for assistant replies */
    }
</style>
""", unsafe_allow_html=True)


# ==================== Sidebar: Pristine & Consolidated ====================
with st.sidebar:
    st.markdown('<h2 style="font-size:1.5rem; margin-bottom:0.5rem; color:#ffffff;">✨ ChatBI 场景管理</h2>', unsafe_allow_html=True)
    st.markdown("---")

    # Clear Chat History Button
    if st.button("🗑️ 清除会话历史", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("question", None)
        st.rerun()

    st.markdown("---")

    # Scenario Theme Configuration
    st.subheader("🎯 业务场景主题")
    themes = theme_loader.get_themes()
    active_theme = theme_loader.get_active_theme()
    
    selected_theme = st.selectbox(
        "选择当前场景",
        options=themes,
        index=themes.index(active_theme) if active_theme in themes else 0,
        key="active_theme_selector",
        label_visibility="collapsed"
    )
    
    # Apply selected theme
    os.environ["ACTIVE_THEME"] = selected_theme
    st.caption(f"📁 激活主题: **{selected_theme}**")
    st.markdown("---")

    # API Configuration
    st.subheader("🔑 凭证配置")
    api_key = st.text_input("API Key", type="password", value=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "", label_visibility="collapsed", placeholder="输入 API Key 以启动 Real 模式")
    if api_key:
        os.environ["DEEPSEEK_API_KEY"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key
    
    app_mode = st.selectbox("运行模式", ["mock", "real"], index=0 if get_config().mock_enabled else 1)
    os.environ["APP_MODE"] = app_mode
    os.environ["MOCK_ENABLED"] = "true" if app_mode == "mock" else "false"

    st.markdown("---")

    # Advanced Developer Tools: Pack everything technical together!
    with st.expander("⚙️ 高级配置 (开发者工具)"):
        st.markdown("**📊 允许查询的数据表白名单**")
        allowed_tbls = get_config().database.allowed_tables
        if allowed_tbls:
            for tbl in allowed_tbls:
                st.caption(f"🔹 `{tbl}`")
        else:
            st.info("未配置允许数据表")

        st.markdown("---")
        
        # New Theme Registration Form
        st.markdown("**➕ 录入新场景主题**")
        with st.form("import_theme_form"):
            new_theme_name = st.text_input("场景名称", placeholder="例如: 财务分析")
            new_table_name = st.text_input("物理表名", placeholder="例如: v_dm_finance_daily")
            new_table_ddl = st.text_area("建表语句 (CREATE TABLE DDL)", placeholder="CREATE TABLE v_dm_finance_daily (...)")
            
            submit_btn = st.form_submit_button("💾 录入并保存配置")
            if submit_btn:
                if not new_theme_name.strip() or not new_table_name.strip() or not new_table_ddl.strip():
                    st.error("请完整填写表单！")
                else:
                    current_config = theme_loader.load_config()
                    theme_key = new_theme_name.strip()
                    tbl_key = new_table_name.strip().lower()
                    
                    if theme_key not in current_config:
                        current_config[theme_key] = {"tables": [], "schemas": {}}
                    if tbl_key not in current_config[theme_key]["tables"]:
                        current_config[theme_key]["tables"].append(tbl_key)
                        
                    current_config[theme_key]["schemas"][tbl_key] = new_table_ddl.strip()
                    if theme_loader.save_config(current_config):
                        st.success(f"成功录入表 `{tbl_key}`")
                        st.rerun()
                    else:
                        st.error("写入失败")

        st.markdown("---")
        
        # Skills Panel
        st.markdown("**📦 已注册 SOP 技能**")
        for s in list_skills():
            st.caption(f"🔮 **{s.get('name')}**: {s.get('description')}")

        st.markdown("---")
        
        # MCP Tools Panel
        st.markdown("**🔧 已注册 MCP 原子工具**")
        for m in list_mcps():
            st.caption(f"🛠️ **{m.get('name')}**: {m.get('description')}")


# ==================== Main UI Workspace ====================

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# If chat is empty, show the premium home page brand
if len(st.session_state.messages) == 0:
    st.markdown('<h1 class="main-title" style="margin-top: 4rem;">✨ ChatBI 智能数据助理</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">基于 SOP & MCP 双层引擎的产销存智能决策助理</p>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    # Minimalist Examples
    st.markdown("<p style='font-size:0.95rem; font-weight: 500; color:#a0aec0; margin-bottom: 0.8rem; text-align:center;'>💡 推荐快速测试案例</p>", unsafe_allow_html=True)
    cols = st.columns(4)
    examples = [
        ("📊 本月中东公司销量多少？", "本月中东公司销量多少？", 0),
        ("⚖️ 同比去年怎么样？", "本月终端量同比去年怎么样？", 1),
        ("📖 什么是库存周转率？", "什么是库存周转率？", 2),
        ("💬 汽车保养公里数？", "汽车保养一般多少公里做一次？", 3)
    ]

    clicked_example = None
    for label, q, col_idx in examples:
        if cols[col_idx].button(label, use_container_width=True, key=f"ex_{col_idx}"):
            clicked_example = q
else:
    # If chat is not empty, show a small elegant header at the very top
    st.markdown(f'<p style="font-size:0.8rem; color:#717684; margin-bottom: 1.2rem; border-bottom: 1px solid #1e2029; padding-bottom: 0.5rem;">💬 当前对话场景: <b>{selected_theme}</b></p>', unsafe_allow_html=True)
    clicked_example = None

# Render all past messages in conversational history
for msg_idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            thought_process = msg.get("thought_process", [])
            selected_skill = msg.get("selected_skill")
            question = msg.get("question", "")
            
            if thought_process:
                # Use a small collapsed st.expander for historical CoT Trace
                with st.expander("🧠 查看已完成的思考与决策明细", expanded=False):
                    st.markdown("### 📋 完整 SOP 决策执行明细 (CoT Trace)")
                    for step in thought_process:
                        step_num = step.get("step", 0)
                        step_type = step.get("step_type", "")
                        
                        if step_type == "select_skill":
                            st.markdown(f"**意图识别意图选择**: `{selected_skill or '直接回答/闲聊'}`")
                            st.markdown(f"*选择原因*: {step.get('reason', '')}")
                        elif step_type == "execute_mcp":
                            st.markdown(f"**步骤 {step_num-1} [{step.get('reason', '')}]**: `{step.get('decision', '')}`")
                            
                            mcp_in_str = json.dumps(step.get("mcp_input", {}), indent=2, ensure_ascii=False)
                            mcp_out_raw = step.get("mcp_output", "")
                            try:
                                mcp_out_parsed = json.loads(mcp_out_raw)
                                mcp_out_str = json.dumps(mcp_out_parsed, indent=2, ensure_ascii=False)
                            except Exception:
                                mcp_out_str = mcp_out_raw

                            st.markdown(f"""
                            <details>
                                <summary>查看本步参数传递与返回详情</summary>
                                <p style="margin: 5px 0 2px 0; font-weight: bold; color: #9061f9;">输入参数 (Arguments):</p>
                                <pre>{mcp_in_str}</pre>
                                <p style="margin: 8px 0 2px 0; font-weight: bold; color: #9061f9;">输出数据 (Raw Return):</p>
                                <pre>{mcp_out_str}</pre>
                            </details>
                            """, unsafe_allow_html=True)
                        elif step_type == "workflow_error":
                            st.error(f"**工作流失败**: {step.get('error', '')}")
                    
                    # Append Mermaid
                    mermaid_code = ["graph TD"]
                    mermaid_code.append("    classDef start fill:#4f46e5,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef process fill:#3b82f6,stroke:#fff,stroke-width:1px,color:#fff;")
                    mermaid_code.append("    classDef active fill:#10b981,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef endNode fill:#ec4899,stroke:#fff,stroke-width:2px,color:#fff;")
                    
                    mermaid_code.append(f'    Start(["💬 {question[:15]}..."]) --> Router{{"🧠 意图路由层"}}')
                    if selected_skill:
                        mermaid_code.append(f'    Router -->|选择技能: {selected_skill}| Skill["📦 {selected_skill} SOP 管道"]')
                        execute_steps = [s for s in thought_process if s.get("step_type") == "execute_mcp"]
                        prev_node = "Skill"
                        for s in execute_steps:
                            s_num = s.get("step", 0)
                            node_id = f"Step_{s_num}"
                            mcp_name_node = s.get("decision", "").split("调用原子工具 [")[-1].replace("]", "").split()[0]
                            s_name = s.get("decision", "").split("[")[1].split("]")[0] if "[" in s.get("decision", "") else f"step_{s_num-1}"
                            mermaid_code.append(f'    {prev_node} --> {node_id}["⚙️ {s_num-1}: {s_name} ({mcp_name_node})"]')
                            mermaid_code.append(f'    class {node_id} process;')
                            prev_node = node_id
                        mermaid_code.append(f'    {prev_node} --> Answer["✅ 最终回答"]')
                        mermaid_code.append('    class Answer endNode;')
                    else:
                        mermaid_code.append('    Router -->|未匹配技能| Answer["💬 直接回答"]')
                        mermaid_code.append('    class Answer endNode;')
                    
                    mermaid_code.append('    class Start start; class Router active;')
                    if selected_skill:
                        mermaid_code.append('    class Skill active;')
                    
                    mermaid_str = "\n".join(mermaid_code)
                    with st.expander("📊 查看决策树与调用流程图 (Mermaid)", expanded=False):
                        st.markdown(f"```mermaid\n{mermaid_str}\n```")
            
            st.markdown(msg["content"])
            
            # Render Markdown Table and chart, if present, cleanly outside the thinking box
            if "|" in msg["content"]:
                try:
                    table_part = ""
                    for line in msg["content"].split("\n"):
                        if line.strip().startswith("|"):
                            table_part += line + "\n"
                    if table_part:
                        render_markdown_table_chart(table_part)
                except Exception:
                    pass

# Detect new user query
user_query = st.chat_input("💬 在此输入您想要分析的业务问题...")

if clicked_example:
    user_query = clicked_example

if user_query:
    # 1. Append User Message
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # 2. Render User Message instantly
    with st.chat_message("user"):
        st.markdown(user_query)
        
    # 3. Create Assistant Message Container and execute Agent
    with st.chat_message("assistant"):
        with st.status("🧠 智能代理深度思考中...", expanded=True) as status_box:
            
            # Streaming Callback to show live progress
            def step_callback(step):
                step_type = step.get("step_type")
                decision = step.get("decision", "")
                
                if step_type == "select_skill":
                    status_box.write(f"🔍 **[意图分析]** 路由决策成功 -> {decision}")
                elif step_type == "execute_mcp":
                    status_box.write(f"⚙️ **[管道执行]** {decision}")
                    # Print generated SQL live if present
                    if step.get("llm_output"):
                        status_box.write(step.get("llm_output"))
                elif step_type == "workflow_error":
                    status_box.write(f"❌ **[工作流中断]** {decision}")
                elif step_type == "final_answer":
                    status_box.write(f"✅ **[分析完毕]** 口径对齐与结果解读就绪")

            # Execute agent synchronously with callback
            result = run_agent(user_query, callback=step_callback)
            
            if "error" in result:
                status_box.update(label="❌ 决策分析执行失败", state="error", expanded=True)
                st.error(result["error"])
                
                # Save assistant response to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"决策分析执行失败: {result['error']}",
                    "thought_process": [],
                    "selected_skill": None,
                    "question": user_query
                })
            else:
                # Compile thought details in status box
                with status_box:
                    st.markdown("---")
                    st.markdown("### 📋 完整 SOP 决策执行明细 (CoT Trace)")
                    thought_process = result.get("thought_process", [])
                    selected_skill = result.get("selected_skill")
                    
                    for step in thought_process:
                        step_num = step.get("step", 0)
                        step_type = step.get("step_type", "")
                        
                        if step_type == "select_skill":
                            st.markdown(f"**意图识别意图选择**: `{selected_skill or '直接回答/闲聊'}`")
                            st.markdown(f"*选择原因*: {step.get('reason', '')}")
                        elif step_type == "execute_mcp":
                            st.markdown(f"**步骤 {step_num-1} [{step.get('reason', '')}]**: `{step.get('decision', '')}`")
                            
                            mcp_in_str = json.dumps(step.get("mcp_input", {}), indent=2, ensure_ascii=False)
                            mcp_out_raw = step.get("mcp_output", "")
                            try:
                                mcp_out_parsed = json.loads(mcp_out_raw)
                                mcp_out_str = json.dumps(mcp_out_parsed, indent=2, ensure_ascii=False)
                            except Exception:
                                mcp_out_str = mcp_out_raw

                            st.markdown(f"""
                            <details>
                                <summary>查看本步参数传递与返回详情</summary>
                                <p style="margin: 5px 0 2px 0; font-weight: bold; color: #9061f9;">输入参数 (Arguments):</p>
                                <pre>{mcp_in_str}</pre>
                                <p style="margin: 8px 0 2px 0; font-weight: bold; color: #9061f9;">输出数据 (Raw Return):</p>
                                <pre>{mcp_out_str}</pre>
                            </details>
                            """, unsafe_allow_html=True)
                        elif step_type == "workflow_error":
                            st.error(f"**工作流失败**: {step.get('error', '')}")
                    
                    # Append Mermaid
                    mermaid_code = ["graph TD"]
                    mermaid_code.append("    classDef start fill:#4f46e5,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef process fill:#3b82f6,stroke:#fff,stroke-width:1px,color:#fff;")
                    mermaid_code.append("    classDef active fill:#10b981,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef endNode fill:#ec4899,stroke:#fff,stroke-width:2px,color:#fff;")
                    
                    mermaid_code.append(f'    Start(["💬 {user_query[:15]}..."]) --> Router{{"🧠 意图路由层"}}')
                    if selected_skill:
                        mermaid_code.append(f'    Router -->|选择技能: {selected_skill}| Skill["📦 {selected_skill} SOP 管道"]')
                        execute_steps = [s for s in thought_process if s.get("step_type") == "execute_mcp"]
                        prev_node = "Skill"
                        for s in execute_steps:
                            s_num = s.get("step", 0)
                            node_id = f"Step_{s_num}"
                            mcp_name_node = s.get("decision", "").split("调用原子工具 [")[-1].replace("]", "").split()[0]
                            s_name = s.get("decision", "").split("[")[1].split("]")[0] if "[" in s.get("decision", "") else f"step_{s_num-1}"
                            mermaid_code.append(f'    {prev_node} --> {node_id}["⚙️ {s_num-1}: {s_name} ({mcp_name_node})"]')
                            mermaid_code.append(f'    class {node_id} process;')
                            prev_node = node_id
                        mermaid_code.append(f'    {prev_node} --> Answer["✅ 最终回答"]')
                        mermaid_code.append('    class Answer endNode;')
                    else:
                        mermaid_code.append('    Router -->|未匹配技能| Answer["💬 直接回答"]')
                        mermaid_code.append('    class Answer endNode;')
                    
                    mermaid_code.append('    class Start start; class Router active;')
                    if selected_skill:
                        mermaid_code.append('    class Skill active;')
                    
                    mermaid_str = "\n".join(mermaid_code)
                    with st.expander("📊 查看决策树与调用流程图 (Mermaid)", expanded=False):
                        st.markdown(f"```mermaid\n{mermaid_str}\n```")

                # Collapse status_box automatically so the page is pristine
                status_box.update(label="🧠 深度思考过程已完成 (可点击展开查看决策详情)", state="complete", expanded=False)

                # Extract final answer text
                final_answer_text = ""
                for step in thought_process:
                    if "final_answer" in step:
                        final_answer_text = step["final_answer"]
                        break
                
                if not final_answer_text:
                    final_answer_text = "未生成完整的最终解答。"

                st.markdown(final_answer_text)
                
                # Save assistant response to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer_text,
                    "thought_process": thought_process,
                    "selected_skill": selected_skill,
                    "question": user_query
                })
                
                # Render Markdown Table and chart, if present, cleanly outside the thinking box
                if "|" in final_answer_text:
                    try:
                        table_part = ""
                        for line in final_answer_text.split("\n"):
                            if line.strip().startswith("|"):
                                table_part += line + "\n"
                        if table_part:
                            render_markdown_table_chart(table_part)
                    except Exception:
                        pass

                st.balloons()
                st.rerun()


# ==================== Footer ====================
st.markdown("---")
st.markdown("<p style='text-align:center; font-size:0.8rem; color:#717684;'>Powered by SOP & Model Context Protocol Engine • Google DeepMind Advanced Agentic Coding</p>", unsafe_allow_html=True)
