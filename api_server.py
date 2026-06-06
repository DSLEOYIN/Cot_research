from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat_repository import ChatRepository, DEFAULT_DB_PATH
from langgraph_cot import run_agent


DEFAULT_SESSION_TITLES = {"新对话", "新聊天"}
SESSION_TITLE_MAX_LENGTH = 20
SESSION_SUMMARY_MAX_LENGTH = 48


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


def _save_step(repo: ChatRepository, assistant_message_id: str, index: int, thought: dict[str, Any]) -> dict[str, Any]:
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
    )


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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


def create_app(db_path: Optional[Union[str, Path]] = None) -> FastAPI:
    repo = ChatRepository(db_path or os.getenv("CHAT_DB_PATH") or DEFAULT_DB_PATH)
    app = FastAPI(title="ChatBI Web API")
    app.state.repo = repo

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

            while True:
                event, data = await queue.get()
                if event == "step_completed":
                    step = _save_step(repo, assistant_message["id"], len(saved_steps) + 1, data)
                    saved_steps.append(step)
                    yield _sse(event, step)
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
            yield _sse("answer_completed", assistant_message)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return app


app = create_app()
