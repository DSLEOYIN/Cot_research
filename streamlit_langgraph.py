"""
ChatBI Clean Agent - Minimalist SOP & MCP Double-layer Execution Engine UI

Features:
- Premium minimalist light design 100% matching ChatGPT Light Mode.
- Dynamic conversation history with multi-session management (Pin, Rename, Confirm Delete).
- Real-time deep reasoning progress updates via Streamlit's native st.status connected to langgraph_cot callback.
- Auto-collapses the deep reasoning box upon completion, leaving only the pristine final answer on screen.
- Streamlined sidebar: hides advanced schemas, white-lists, and registers inside a single "Advanced Developer Tools" box.
"""

import streamlit as st
import json
import os
import uuid

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
            st.markdown("<p style='font-size:0.95rem; font-weight:600; color:#0d0d0d; margin-top:1.2rem; margin-bottom:0.5rem;'>📊 动态数据直观图表</p>", unsafe_allow_html=True)
            
            categorical_cols = [c for c in df.columns if c not in numeric_cols]
            if categorical_cols:
                x_col = categorical_cols[0]
                df_chart = df.set_index(x_col)[numeric_cols]
            else:
                df_chart = df[numeric_cols]
                
            st.bar_chart(df_chart, use_container_width=True)
    except Exception:
        pass


# ==================== Page Configuration ====================
st.set_page_config(
    page_title="ChatBI 智能数据助理",
    page_icon="✨",
    layout="wide"
)

# ==================== Session State Initialization ====================
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "active_session_id" not in st.session_state:
    default_id = str(uuid.uuid4())
    st.session_state.sessions[default_id] = {
        "id": default_id,
        "title": "新聊天",
        "messages": [],
        "is_pinned": False
    }
    st.session_state.active_session_id = default_id

# Inconsistency recovery
active_id = st.session_state.active_session_id
if active_id not in st.session_state.sessions:
    if st.session_state.sessions:
        active_id = list(st.session_state.sessions.keys())[0]
    else:
        active_id = str(uuid.uuid4())
        st.session_state.sessions[active_id] = {
            "id": active_id,
            "title": "新聊天",
            "messages": [],
            "is_pinned": False
        }
    st.session_state.active_session_id = active_id

active_sess = st.session_state.sessions[active_id]


# ==================== Page Premium Light CSS (ChatGPT Light Mode) ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Sleek minimalist light styling (ChatGPT Light Mode) */
    .stApp {
        background-color: #ffffff !important;
        color: #0d0d0d !important;
        font-family: 'Inter', 'Outfit', sans-serif !important;
    }
    
    /* Typography override */
    h1, h2, h3, h4, h5, h6 {
        color: #0d0d0d !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.015em;
    }
    
    /* Elegant Title */
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        color: #0d0d0d !important;
        text-align: center;
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        color: #4b5563 !important;
        font-size: 1.05rem !important;
        margin-bottom: 2.5rem !important;
        text-align: center !important;
        font-weight: 400 !important;
    }
    
    /* Sidebar Overrides (ChatGPT Clean Sidebar Panel) */
    section[data-testid="stSidebar"] {
        background-color: #f9f9f9 !important;
        border-right: 1px solid #e5e7eb !important;
    }
    section[data-testid="stSidebar"] * {
        color: #374151 !important;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #0d0d0d !important;
    }
    
    /* Override Suggestion Cards in the main workspace */
    .stButton > button {
        background-color: #ffffff !important;
        border: 1px solid #e3e3e3 !important;
        border-radius: 16px !important;
        color: #0d0d0d !important;
        padding: 1.2rem 1.1rem !important;
        height: auto !important;
        min-height: 86px !important;
        text-align: left !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    .stButton > button:hover {
        background-color: #f4f4f4 !important;
        border-color: #b4b4b4 !important;
        transform: translateY(-2px);
    }
    .stButton > button:active {
        background-color: #ececec !important;
        transform: translateY(0);
    }
    
    /* Sidebar Action/Control Buttons */
    section[data-testid="stSidebar"] button {
        background-color: #ffffff !important;
        border: 1px solid #e3e3e3 !important;
        border-radius: 8px !important;
        color: #374151 !important;
        padding: 0.35rem 0.6rem !important;
        min-height: auto !important;
        font-size: 0.82rem !important;
        text-align: center !important;
        justify-content: center !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: #f4f4f4 !important;
        border-color: #b4b4b4 !important;
        color: #0d0d0d !important;
    }
    
    /* Sidebar Session List Items styling (borderless rows) */
    div.sess-row-container {
        display: flex;
        align-items: center;
        width: 100%;
        margin-bottom: 2px;
    }
    
    /* Style the sidebar inputs to look like ChatGPT standard fields */
    div[data-testid="stSidebar"] div[data-baseweb="select"], 
    div[data-testid="stSidebar"] div[data-baseweb="base-input"],
    div[data-testid="stSidebar"] input {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #e3e3e3 !important;
    }
    
    /* Expanders & details tags (Sleek charcoal style) */
    details {
        background-color: #f9f9f9 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin: 8px 0 !important;
    }
    summary {
        color: #1a73e8 !important; /* Premium light blue link */
        font-weight: 500 !important;
        cursor: pointer;
        outline: none;
        font-size: 0.9em;
    }
    summary:hover {
        color: #1557b0 !important;
    }
    pre {
        background-color: #1a1a1a !important; /* Keep code dark for excellent syntax contrast */
        border: none !important;
        color: #f8f8f2 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Streamlit expander overrides */
    .stExpander {
        background-color: #f9f9f9 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        margin-bottom: 0.8rem !important;
    }
    .stExpander > div {
        border: none !important;
    }
    
    /* Sleek status bar for thinking */
    .status-bar-clean {
        background-color: #f9f9f9 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        padding: 10px 14px;
        font-size: 0.9rem;
        color: #4b5563;
    }
    
    /* Make the chat input container perfectly match the ChatGPT look */
    div[data-testid="stChatInput"] {
        border-radius: 24px !important;
        background-color: #ffffff !important;
        border: 1px solid #e3e3e3 !important;
        padding: 4px 10px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #0d0d0d !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Override chat message bubble padding & backgrounds */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 1.2rem 0.5rem !important;
        border-bottom: 1px solid #f0f0f0 !important;
    }
    /* Style user bubble like ChatGPT */
    div[data-testid="stChatMessage"]:nth-child(odd) div[data-testid="stChatMessageContent"] {
        background-color: #f4f4f4 !important;
        border-radius: 20px !important;
        padding: 10px 16px !important;
        color: #0d0d0d !important;
        display: inline-block !important;
    }
    /* Style assistant bubble (completely transparent/borderless) */
    div[data-testid="stChatMessage"]:nth-child(even) div[data-testid="stChatMessageContent"] {
        background-color: transparent !important;
        padding: 10px 0 !important;
        color: #0d0d0d !important;
    }
</style>
""", unsafe_allow_html=True)


# ==================== Sidebar: ChatGPT Multi-Session Panel ====================
with st.sidebar:
    st.markdown('<h2 style="font-size:1.4rem; margin-bottom:0.5rem; color:#0d0d0d; display:flex; align-items:center;">✨ ChatBI 场景管理</h2>', unsafe_allow_html=True)
    st.markdown("---")

    # [+] New Chat Button
    if st.button("➕ 新建聊天", use_container_width=True, key="new_chat_btn"):
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {
            "id": new_id,
            "title": "新聊天",
            "messages": [],
            "is_pinned": False
        }
        st.session_state.active_session_id = new_id
        st.rerun()

    st.markdown("<p style='font-size:0.8rem; font-weight:600; color:#9ca3af; margin: 1rem 0 0.3rem 0;'>会话历史</p>", unsafe_allow_html=True)
    
    # Sort sessions: Pinned first, then Pinned = False
    all_sessions = list(st.session_state.sessions.items())
    pinned_sessions = [item for item in all_sessions if item[1].get("is_pinned", False)]
    regular_sessions = [item for item in all_sessions if not item[1].get("is_pinned", False)]
    
    sorted_sessions = pinned_sessions + regular_sessions

    # Render Sessions List
    for s_id, s in sorted_sessions:
        is_active = (s_id == active_id)
        
        # Determine visual title
        pin_prefix = "📌 " if s.get("is_pinned") else ""
        btn_label = f"{pin_prefix}{s['title']}"
        if is_active:
            btn_label = f"👉 {btn_label}"
            
        # Form block for renaming
        if st.session_state.get(f"renaming_{s_id}"):
            with st.form(key=f"rename_form_{s_id}"):
                new_title = st.text_input("重命名", value=s['title'], key=f"new_title_val_{s_id}", label_visibility="collapsed")
                cols_form = st.columns(2)
                if cols_form[0].form_submit_button("💾"):
                    if new_title.strip():
                        s['title'] = new_title.strip()
                    st.session_state.pop(f"renaming_{s_id}", None)
                    st.rerun()
                if cols_form[1].form_submit_button("❌"):
                    st.session_state.pop(f"renaming_{s_id}", None)
                    st.rerun()
            continue
            
        # Dialog block for delete confirmation
        if st.session_state.get(f"confirm_delete_{s_id}"):
            st.markdown(f"<p style='font-size:0.8rem; color:#dc2626; font-weight:bold; margin-bottom:4px;'>⚠️ 确定要删除会话吗？</p>", unsafe_allow_html=True)
            cols_del = st.columns(2)
            if cols_del[0].button("✅", key=f"do_delete_{s_id}", help="确认删除"):
                st.session_state.sessions.pop(s_id, None)
                st.session_state.pop(f"confirm_delete_{s_id}", None)
                
                # If deleted active, fallback
                if st.session_state.active_session_id == s_id:
                    remaining = list(st.session_state.sessions.keys())
                    if remaining:
                        st.session_state.active_session_id = remaining[0]
                    else:
                        new_id = str(uuid.uuid4())
                        st.session_state.sessions[new_id] = {
                            "id": new_id,
                            "title": "新聊天",
                            "messages": [],
                            "is_pinned": False
                        }
                        st.session_state.active_session_id = new_id
                st.rerun()
            if cols_del[1].button("❌", key=f"cancel_delete_{s_id}", help="取消"):
                st.session_state.pop(f"confirm_delete_{s_id}", None)
                st.rerun()
            continue

        # Render normal session row with columns
        cols = st.columns([0.64, 0.12, 0.12, 0.12])
        
        # 1. Select session button
        if cols[0].button(btn_label, key=f"select_{s_id}", use_container_width=True):
            st.session_state.active_session_id = s_id
            st.rerun()
            
        # 2. Pin/Unpin
        pin_icon = "📍" if s.get("is_pinned") else "📌"
        if cols[1].button(pin_icon, key=f"pin_btn_{s_id}", help="置顶/取消置顶"):
            s["is_pinned"] = not s.get("is_pinned", False)
            st.rerun()
            
        # 3. Rename
        if cols[2].button("✏️", key=f"rename_btn_{s_id}", help="重命名"):
            st.session_state[f"renaming_{s_id}"] = True
            st.rerun()
            
        # 4. Delete
        if cols[3].button("🗑️", key=f"delete_btn_{s_id}", help="删除会话"):
            st.session_state[f"confirm_delete_{s_id}"] = True
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
    api_key = st.text_input("API Key", type="password", value=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "", label_visibility="collapsed", placeholder="输入 API Key 开启 Real 模式")
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

# If chat is empty, show the premium home page brand
if len(active_sess["messages"]) == 0:
    st.markdown('<h1 class="main-title" style="margin-top: 5rem;">你在忙什么？</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">基于 SOP & MCP 双层引擎的智能数据助理，产销存指标对话与决策分析平台</p>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    # Minimalist Suggestion Cards
    st.markdown("<p style='font-size:0.95rem; font-weight: 500; color:#4b5563; margin-bottom: 0.8rem; text-align:center;'>💡 推荐快速测试案例</p>", unsafe_allow_html=True)
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
    st.markdown(f'<p style="font-size:0.8rem; color:#6b7280; margin-bottom: 1.2rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.5rem;">💬 当前对话场景: <b>{selected_theme}</b> • 当前会话: <b>{active_sess["title"]}</b></p>', unsafe_allow_html=True)
    clicked_example = None

# Render all past messages in conversational history of current session
for msg_idx, msg in enumerate(active_sess["messages"]):
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
                                <p style="margin: 5px 0 2px 0; font-weight: bold; color: #1a73e8;">输入参数 (Arguments):</p>
                                <pre>{mcp_in_str}</pre>
                                <p style="margin: 8px 0 2px 0; font-weight: bold; color: #1a73e8;">输出数据 (Raw Return):</p>
                                <pre>{mcp_out_str}</pre>
                            </details>
                            """, unsafe_allow_html=True)
                        elif step_type == "workflow_error":
                            st.error(f"**工作流失败**: {step.get('error', '')}")
                    
                    # Append Mermaid
                    mermaid_code = ["graph TD"]
                    mermaid_code.append("    classDef start fill:#4285f4,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef process fill:#34a853,stroke:#fff,stroke-width:1px,color:#fff;")
                    mermaid_code.append("    classDef active fill:#fbbc05,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef endNode fill:#ea4335,stroke:#fff,stroke-width:2px,color:#fff;")
                    
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
user_query = st.chat_input("💬 有问题，尽管问...")

if clicked_example:
    user_query = clicked_example

if user_query:
    # Auto-Naming on first question
    if len(active_sess["messages"]) == 0 and active_sess["title"] == "新聊天":
        clean_q = user_query.strip()
        summary_title = clean_q[:10] + ("..." if len(clean_q) > 10 else "")
        active_sess["title"] = summary_title

    # 1. Append User Message
    active_sess["messages"].append({"role": "user", "content": user_query})
    
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
                active_sess["messages"].append({
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
                                <p style="margin: 5px 0 2px 0; font-weight: bold; color: #1a73e8;">输入参数 (Arguments):</p>
                                <pre>{mcp_in_str}</pre>
                                <p style="margin: 8px 0 2px 0; font-weight: bold; color: #1a73e8;">输出数据 (Raw Return):</p>
                                <pre>{mcp_out_str}</pre>
                            </details>
                            """, unsafe_allow_html=True)
                        elif step_type == "workflow_error":
                            st.error(f"**工作流失败**: {step.get('error', '')}")
                    
                    # Append Mermaid
                    mermaid_code = ["graph TD"]
                    mermaid_code.append("    classDef start fill:#4285f4,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef process fill:#34a853,stroke:#fff,stroke-width:1px,color:#fff;")
                    mermaid_code.append("    classDef active fill:#fbbc05,stroke:#fff,stroke-width:2px,color:#fff;")
                    mermaid_code.append("    classDef endNode fill:#ea4335,stroke:#fff,stroke-width:2px,color:#fff;")
                    
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
                active_sess["messages"].append({
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
st.markdown("<div style='margin-top: 5rem;'></div>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:0.8rem; color:#9ca3af; border-top: 1px solid #f0f0f0; padding-top: 1rem;'>Powered by SOP & Model Context Protocol Engine • Google DeepMind Advanced Agentic Coding</p>", unsafe_allow_html=True)
