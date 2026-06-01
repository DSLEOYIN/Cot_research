"""
ChatBI Clean Agent - Minimalist SOP & MCP Double-layer Execution Engine UI

Features:
- Premium minimalist light design 100% matching ChatGPT Light Mode.
- Dynamic conversation history with multi-session management (Pin, Rename, Confirm Delete).
- Real-time deep reasoning progress updates via Streamlit's native st.status connected to langgraph_cot callback.
- Auto-collapses the deep reasoning box upon completion, leaving only the pristine final answer on screen.
- Streamlined sidebar: hides advanced schemas, white-lists, and registers inside a single "Advanced Developer Tools" box.
"""

from __future__ import annotations

import streamlit as st
import html
import json
import os
import uuid

from langgraph_cot import run_agent
from skills import list_skills
from mcps import list_mcps
from app_config import get_config
import theme_loader


def render_echarts_markdown(md_table: str):
    """
    Parses a markdown table, extracts category X-data and numerical Y-data,
    and renders a stunning, responsive ECharts 5.x chart via HTML iframe component.
    """
    import streamlit.components.v1 as components
    import json
    
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
            
        # Category Data (X-axis) - first column
        x_data = [row[0] for row in rows_data]
        
        # Series list (Y-axis numerical values)
        series_list = []
        
        # Check every remaining column to see if it is numeric
        for col_idx in range(1, len(headers)):
            col_name = headers[col_idx]
            y_data = []
            is_numeric = True
            for row in rows_data:
                val = row[col_idx]
                try:
                    # Strip symbols like %, commas and spaces
                    cleaned = val.replace("%", "").replace(",", "").strip()
                    y_data.append(float(cleaned))
                except ValueError:
                    is_numeric = False
                    break
            
            if is_numeric:
                series_list.append({
                    "name": col_name,
                    "type": "bar",
                    "data": y_data,
                    "itemStyle": {
                        "borderRadius": [6, 6, 0, 0] # Beautiful rounded bars matching modern charts
                    },
                    "barMaxWidth": 40 # Limit bar width to look professional
                })
        
        if not series_list:
            return
            
        # Build ECharts options in JSON
        echarts_options = {
            "tooltip": {
                "trigger": "axis",
                "backgroundColor": "rgba(255, 255, 255, 0.95)",
                "borderColor": "#e3e3e3",
                "borderWidth": 1,
                "textStyle": {
                    "color": "#0d0d0d",
                    "fontFamily": "Inter, sans-serif"
                },
                "axisPointer": {
                    "type": "shadow"
                }
            },
            "legend": {
                "data": [s["name"] for s in series_list],
                "textStyle": {
                    "color": "#4b5563",
                    "fontFamily": "Inter, sans-serif"
                },
                "top": "0%"
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "top": "15%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "data": x_data,
                "axisLine": {
                    "lineStyle": {
                        "color": "#e5e7eb"
                    }
                },
                "axisLabel": {
                    "color": "#4b5563",
                    "fontFamily": "Inter, sans-serif"
                }
            },
            "yAxis": {
                "type": "value",
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#f3f4f6"
                    }
                },
                "axisLabel": {
                    "color": "#4b5563",
                    "fontFamily": "Inter, sans-serif"
                }
            },
            "color": ["#1a73e8", "#34a853", "#fbbc05", "#ea4335", "#8e8e8e"], # Soft pastel colors
            "series": series_list
        }
        
        options_json = json.dumps(echarts_options, ensure_ascii=False)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: transparent;
                }}
                #chart-container {{
                    width: 100%;
                    height: 330px;
                }}
            </style>
        </head>
        <body>
            <div id="chart-container"></div>
            <script>
                var chartDom = document.getElementById('chart-container');
                var myChart = echarts.init(chartDom);
                var option = {options_json};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{
                    myChart.resize();
                }});
            </script>
        </body>
        </html>
        """
        
        st.markdown("<p style='font-size:0.95rem; font-weight:600; color:#0d0d0d; margin-top:1.2rem; margin-bottom:0.2rem;'>📈 动态数据智能分析图表 (ECharts)</p>", unsafe_allow_html=True)
        components.html(html_content, height=340)
        
    except Exception:
        pass


def render_split_assistant_content(final_answer_text: str):
    """
    Parses and splits the combined assistant final answer text, and renders the elements
    strictly in the requested business order:
    1. Data Table (📊 数据查询结果)
    2. ECharts Chart (📈 动态分析图表)
    3. Business Analysis & Interpretation (💡 业务分析与深度解读)
    4. Data Scope & Explanation (🛡️ 数据统计口径说明)
    """
    table_section = ""
    analysis_section = ""
    scope_section = ""
    is_yoy = "同环比" in final_answer_text or "YOY" in final_answer_text.upper()
    
    # 1. Split logic based on standard headers
    if "### 📊 数据查询结果" in final_answer_text:
        parts = final_answer_text.split("### 💡 业务分析与解读")
        table_part = parts[0].replace("### 📊 数据查询结果", "").strip()
        table_section = table_part
        
        if len(parts) > 1:
            rest = parts[1]
            if "### 🛡️ 数据统计口径说明" in rest:
                sub_parts = rest.split("### 🛡️ 数据统计口径说明")
                analysis_section = sub_parts[0].strip()
                scope_section = sub_parts[1].strip()
            else:
                analysis_section = rest.strip()
                
    elif "### 📊 同环比计算数据" in final_answer_text:
        parts = final_answer_text.split("### 💡 同环比深度解读")
        table_part = parts[0].replace("### 📊 同环比计算数据", "").strip()
        table_section = table_part
        
        if len(parts) > 1:
            analysis_section = parts[1].strip()
            
    else:
        # Fallback for chat or non-structured responses
        table_section = ""
        analysis_section = final_answer_text
        scope_section = ""
        
    # 2. Render structured blocks sequentially
    
    # Step 1: Render Data Table
    if table_section:
        if is_yoy:
            st.markdown("### 📊 同环比计算数据")
        else:
            st.markdown("### 📊 数据查询结果")
        st.markdown(table_section)
        
        # Step 2: Render ECharts Visualization directly beneath the data table
        try:
            table_part = ""
            for line in table_section.split("\n"):
                if line.strip().startswith("|"):
                    table_part += line + "\n"
            if table_part:
                render_echarts_markdown(table_part)
        except Exception:
            pass
            
    # Step 3: Render Business Analysis & Interpretation
    if analysis_section:
        if is_yoy:
            st.markdown("### 💡 同环比深度解读")
        else:
            st.markdown("### 💡 业务分析与解读")
        st.markdown(analysis_section)
        
    # Step 4: Render Data Scope / Explanation
    if scope_section:
        st.markdown("### 🛡️ 数据统计口径说明")
        st.markdown(f"> {scope_section.lstrip('>').strip()}")


def build_codex_thought_timeline_html(thought_process, selected_skill=None, question="", open_by_default=False, is_running=False):
    """Build compact Codex-style execution timeline markup."""
    if not thought_process:
        running_text = "正在等待执行步骤..." if is_running else "暂无执行明细"
        thought_process = [{"step_type": "pending", "reason": running_text}]

    rows = []
    for step in thought_process:
        step_type = step.get("step_type", "")
        title = ""
        meta = ""
        body = ""

        if step_type == "select_skill":
            title = "意图识别"
            meta = selected_skill or "直接回答"
            body = step.get("reason", "") or step.get("decision", "")
        elif step_type == "execute_mcp":
            decision = step.get("decision", "")
            mcp_name = decision.split("调用原子工具 [")[-1].replace("]", "").split()[0] if "调用原子工具 [" in decision else "mcp"
            skill_step = decision.split("[")[1].split("]")[0] if "[" in decision else f"step_{step.get('step', 0)}"
            title = skill_step
            meta = mcp_name
            body = step.get("reason", "") or decision
        elif step_type == "workflow_error":
            title = "工作流中断"
            meta = "error"
            body = step.get("error", "") or step.get("decision", "")
        elif step_type == "sql_correction":
            title = "SQL 自动纠错"
            meta = "retry"
            body = step.get("reason", "") or step.get("decision", "")
        elif step_type == "final_answer":
            title = "生成回答"
            meta = "complete"
            body = "已完成结果整理与业务解读"
        elif step_type == "pending":
            title = "准备中"
            meta = "running"
            body = step.get("reason", "")
        else:
            title = step_type or "执行步骤"
            meta = f"step {step.get('step', '')}".strip()
            body = step.get("reason", "") or step.get("decision", "")

        rows.append(
            "<div class='codex-trace-row'>"
            "<span class='codex-trace-dot'></span>"
            "<div class='codex-trace-content'>"
            f"<div class='codex-trace-line'><span>{html.escape(title)}</span><code>{html.escape(meta)}</code></div>"
            f"<p>{html.escape(body)}</p>"
            "</div>"
            "</div>"
        )

    question_label = html.escape(question[:36] + ("..." if len(question) > 36 else "")) if question else "本次请求"
    open_attr = " open" if open_by_default else ""
    running_class = " is-running" if is_running else ""
    return f"""
<details class="codex-trace{running_class}"{open_attr}>
  <summary>
    <span class="codex-trace-title">思考与执行明细</span>
    <span class="codex-trace-subtitle">{question_label}</span>
  </summary>
  <div class="codex-trace-panel">
    {''.join(rows)}
  </div>
</details>
"""


def render_codex_thought_timeline(thought_process, selected_skill=None, question="", open_by_default=False, is_running=False):
    """Render execution details as a compact Codex-style timeline."""
    st.markdown(
        build_codex_thought_timeline_html(thought_process, selected_skill, question, open_by_default, is_running),
        unsafe_allow_html=True,
    )


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
    
    /* Sidebar List Item Select Buttons */
    section[data-testid="stSidebar"] div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #374151 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.88rem !important;
        padding: 0.5rem 0.8rem !important;
        min-height: auto !important;
        border-radius: 8px !important;
        width: 100% !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #ececec !important;
        color: #0d0d0d !important;
    }
    
    /* Sidebar Action/Control Row Buttons */
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton button {
        background-color: #ffffff !important;
        border: 1px solid #e3e3e3 !important;
        border-radius: 8px !important;
        color: #374151 !important;
        padding: 0 !important;
        height: 34px !important;
        min-height: 34px !important;
        font-size: 0.78rem !important;
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        width: 100% !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton button:hover {
        background-color: #f4f4f4 !important;
        border-color: #b4b4b4 !important;
        color: #0d0d0d !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton button p {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 0.78rem !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }
    
    /* Pinned and Active Session visual indicators */
    .active-session-indicator {
        font-weight: 600 !important;
        background-color: #ececec !important;
        color: #0d0d0d !important;
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

    /* Codex-style thinking timeline */
    details.codex-trace {
        background: transparent !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        padding: 0 !important;
        margin: 0.75rem 0 1.1rem 0 !important;
        overflow: hidden;
    }
    details.codex-trace.is-running {
        border-color: #d1d5db !important;
        box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04);
    }
    details.codex-trace summary {
        list-style: none !important;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        min-height: 42px;
        padding: 0 14px !important;
        color: #111827 !important;
        cursor: pointer;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }
    details.codex-trace summary::-webkit-details-marker {
        display: none;
    }
    details.codex-trace summary::before {
        content: "";
        width: 7px;
        height: 7px;
        border-right: 1.5px solid #6b7280;
        border-bottom: 1.5px solid #6b7280;
        transform: rotate(-45deg);
        transition: transform 0.16s ease;
        flex: 0 0 auto;
    }
    details.codex-trace[open] summary::before {
        transform: rotate(45deg);
    }
    .codex-trace-title {
        flex: 1;
        color: #111827;
    }
    .codex-trace-subtitle {
        color: #6b7280;
        font-size: 0.78rem;
        font-weight: 400;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 45%;
    }
    .codex-trace-panel {
        border-top: 1px solid #eef2f7;
        padding: 8px 14px 12px 14px;
        background: #ffffff;
    }
    .codex-trace-row {
        position: relative;
        display: grid;
        grid-template-columns: 14px 1fr;
        gap: 10px;
        padding: 8px 0;
    }
    .codex-trace-row:not(:last-child)::after {
        content: "";
        position: absolute;
        left: 5px;
        top: 22px;
        bottom: -8px;
        width: 1px;
        background: #e5e7eb;
    }
    .codex-trace-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        margin-top: 5px;
        background: #111827;
        box-shadow: 0 0 0 3px #f3f4f6;
        z-index: 1;
    }
    details.codex-trace.is-running .codex-trace-row:last-child .codex-trace-dot {
        animation: codexPulse 1.25s ease-in-out infinite;
    }
    @keyframes codexPulse {
        0%, 100% { box-shadow: 0 0 0 3px #f3f4f6; }
        50% { box-shadow: 0 0 0 6px #e5e7eb; }
    }
    .codex-trace-line {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
    }
    .codex-trace-line span {
        color: #111827;
        font-size: 0.86rem;
        font-weight: 560;
    }
    .codex-trace-line code {
        background: #f3f4f6 !important;
        color: #4b5563 !important;
        border-radius: 999px;
        padding: 2px 7px;
        font-size: 0.72rem;
        font-family: 'Inter', sans-serif;
        white-space: nowrap;
    }
    .codex-trace-content p {
        margin: 4px 0 0 0 !important;
        color: #6b7280;
        font-size: 0.8rem;
        line-height: 1.55;
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
    st.markdown('<h2 style="font-size:1.4rem; margin-bottom:0.2rem; color:#0d0d0d; display:flex; align-items:center;">✨ ChatBI 场景管理</h2>', unsafe_allow_html=True)
    st.caption("💡 侧边栏支持使用左上角 ◀ 按钮进行折叠/展开")
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
        pin_prefix = "📌 " if s.get("is_pinned") else "💬 "
        btn_label = f"{pin_prefix}{s['title']}"
        if is_active:
            btn_label = f"👉 {btn_label}"
            
        # Form block for renaming
        if st.session_state.get(f"renaming_{s_id}"):
            with st.form(key=f"rename_form_{s_id}"):
                new_title = st.text_input("重命名会话", value=s['title'], key=f"new_title_val_{s_id}", label_visibility="collapsed")
                cols_form = st.columns(2)
                if cols_form[0].form_submit_button("💾 保存"):
                    if new_title.strip():
                        s['title'] = new_title.strip()
                    st.session_state.pop(f"renaming_{s_id}", None)
                    st.rerun()
                if cols_form[1].form_submit_button("❌ 取消"):
                    st.session_state.pop(f"renaming_{s_id}", None)
                    st.rerun()
            continue
            
        # Dialog block for delete confirmation
        if st.session_state.get(f"confirm_delete_{s_id}"):
            st.markdown(f"<p style='font-size:0.8rem; color:#dc2626; font-weight:bold; margin-bottom:4px; margin-top:8px;'>⚠️ 确定要删除会话吗？</p>", unsafe_allow_html=True)
            cols_del = st.columns(2)
            if cols_del[0].button("✅ 确定", key=f"do_delete_{s_id}", help="确认删除"):
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
            if cols_del[1].button("❌ 取消", key=f"cancel_delete_{s_id}", help="取消"):
                st.session_state.pop(f"confirm_delete_{s_id}", None)
                st.rerun()
            continue

        # 1. Render Session Name Select button (100% width, no side-by-side columns to squeeze)
        if st.button(btn_label, key=f"select_{s_id}", use_container_width=True):
            st.session_state.active_session_id = s_id
            st.rerun()
            
        # 2. Render small Action Bar ONLY under the ACTIVE session (ChatGPT premium dropdown-like bar)
        if is_active:
            st.markdown("<div class='sidebar-action-bar'>", unsafe_allow_html=True)
            cols_act = st.columns([0.33, 0.33, 0.34])
            
            pin_lbl = "取消置顶" if s.get("is_pinned") else "置顶"
            if cols_act[0].button(pin_lbl, key=f"pin_act_{s_id}", help="置顶/取消置顶", use_container_width=True):
                s["is_pinned"] = not s.get("is_pinned", False)
                st.rerun()
                
            if cols_act[1].button("改名", key=f"rename_act_{s_id}", help="重命名会话", use_container_width=True):
                st.session_state[f"renaming_{s_id}"] = True
                st.rerun()
                
            if cols_act[2].button("删除", key=f"delete_act_{s_id}", help="删除当前会话", use_container_width=True):
                st.session_state[f"confirm_delete_{s_id}"] = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

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
    
    # Minimalist Suggestion Cards (Completely pure text cards, no emoji icons!)
    st.markdown("<p style='font-size:0.95rem; font-weight: 500; color:#4b5563; margin-bottom: 0.8rem; text-align:center;'>💡 推荐快速测试案例</p>", unsafe_allow_html=True)
    cols = st.columns(4)
    examples = [
        ("本月中东公司销量多少？", "本月中东公司销量多少？", 0),
        ("同比去年怎么样？", "本月终端量同比去年怎么样？", 1),
        ("什么是库存周转率？", "什么是库存周转率？", 2),
        ("汽车保养公里数？", "汽车保养一般多少公里做一次？", 3)
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
                render_codex_thought_timeline(thought_process, selected_skill, question)
            
            # Render assistant reply with perfect order: Table -> ECharts -> Analysis -> Scope
            render_split_assistant_content(msg["content"])

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
        live_steps = []
        trace_placeholder = st.empty()
        trace_placeholder.markdown(
            build_codex_thought_timeline_html(live_steps, question=user_query, open_by_default=True, is_running=True),
            unsafe_allow_html=True,
        )

        def step_callback(step):
            live_steps.append(step)
            trace_placeholder.markdown(
                build_codex_thought_timeline_html(live_steps, question=user_query, open_by_default=True, is_running=True),
                unsafe_allow_html=True,
            )

        result = run_agent(user_query, callback=step_callback)

        if "error" in result:
            error_step = {
                "step_type": "workflow_error",
                "error": result["error"],
                "decision": "执行失败",
            }
            live_steps.append(error_step)
            trace_placeholder.markdown(
                build_codex_thought_timeline_html(live_steps, question=user_query, open_by_default=True, is_running=False),
                unsafe_allow_html=True,
            )
            st.error(result["error"])

            active_sess["messages"].append({
                "role": "assistant",
                "content": f"决策分析执行失败: {result['error']}",
                "thought_process": live_steps,
                "selected_skill": None,
                "question": user_query
            })
        else:
            thought_process = result.get("thought_process", live_steps)
            selected_skill = result.get("selected_skill")
            trace_placeholder.markdown(
                build_codex_thought_timeline_html(thought_process, selected_skill, user_query, open_by_default=True, is_running=False),
                unsafe_allow_html=True,
            )

            final_answer_text = ""
            for step in thought_process:
                if "final_answer" in step:
                    final_answer_text = step["final_answer"]
                    break

            if not final_answer_text:
                final_answer_text = "未生成完整的最终解答。"

            render_split_assistant_content(final_answer_text)

            active_sess["messages"].append({
                "role": "assistant",
                "content": final_answer_text,
                "thought_process": thought_process,
                "selected_skill": selected_skill,
                "question": user_query
            })


# ==================== Footer ====================
st.markdown("<div style='margin-top: 5rem;'></div>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:0.8rem; color:#9ca3af; border-top: 1px solid #f0f0f0; padding-top: 1rem;'>Powered by SOP & Model Context Protocol Engine • Google DeepMind Advanced Agentic Coding</p>", unsafe_allow_html=True)
