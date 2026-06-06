from chat_repository import ChatRepository


def test_session_lifecycle_persists_to_sqlite(tmp_path):
    repo = ChatRepository(tmp_path / "chat.db")

    session = repo.create_session("初始会话")
    assert session["title"] == "初始会话"
    assert session["is_pinned"] is False

    repo.update_session(session["id"], title="中东销量分析", is_pinned=True)
    sessions = repo.list_sessions()

    assert len(sessions) == 1
    assert sessions[0]["id"] == session["id"]
    assert sessions[0]["title"] == "中东销量分析"
    assert sessions[0]["is_pinned"] is True

    repo.delete_session(session["id"])
    assert repo.list_sessions() == []


def test_messages_and_steps_are_loaded_in_order(tmp_path):
    repo = ChatRepository(tmp_path / "chat.db")
    session = repo.create_session("分析会话")

    user_message = repo.add_message(
        session["id"],
        role="user",
        content="2024年中东公司终端量是多少？",
        web_search_enabled=True,
    )
    assistant_message = repo.add_message(
        session["id"],
        role="assistant",
        content="正在分析",
        selected_skill="data_web_compare_analysis",
        trace_open=True,
    )
    repo.add_step(
        assistant_message["id"],
        step_index=1,
        step_type="select_skill",
        title="意图识别",
        status="completed",
        summary="选择内部数据与联网分析",
        llm_output="[SKILL]data_web_compare_analysis[/SKILL]",
        duration_ms=12,
    )
    repo.update_message(assistant_message["id"], content="最终答案")

    detail = repo.get_session(session["id"])

    assert detail["messages"][0]["id"] == user_message["id"]
    assert detail["messages"][1]["content"] == "最终答案"
    assert detail["messages"][1]["steps"][0]["title"] == "意图识别"
    assert detail["messages"][1]["steps"][0]["status"] == "completed"


def test_session_summary_falls_back_to_latest_user_message(tmp_path):
    repo = ChatRepository(tmp_path / "chat.db")
    session = repo.create_session("旧会话")
    repo.add_message(session["id"], role="user", content="第一条历史问题")
    repo.add_message(session["id"], role="assistant", content="回答")
    repo.add_message(session["id"], role="user", content="最近一条历史追问")

    listed = repo.list_sessions()
    detail = repo.get_session(session["id"])

    assert listed[0]["summary"] == "最近一条历史追问"
    assert detail["summary"] == "最近一条历史追问"
