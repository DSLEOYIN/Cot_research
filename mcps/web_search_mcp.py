"""
联网检索 MCP

当前实现 Tavily Search API，用于 UAT 中验证外部联网检索能力。
"""

from __future__ import annotations

import json
from typing import TypedDict

from app_config import get_config, require_real_mode_config
from mcps import register_mcp


class WebSearchInput(TypedDict):
    query: str
    max_results: int | None
    search_depth: str | None


def web_search(query: str, max_results: int | None = None, search_depth: str = "basic") -> str:
    if not query or not isinstance(query, str):
        return json.dumps({
            "success": False,
            "results": [],
            "answer": None,
            "error": "联网检索 query 不能为空",
            "error_type": "ArgumentError",
        }, ensure_ascii=False)

    config = get_config()
    top_k = max_results or config.web_mcp.top_k

    if config.mock_enabled:
        return json.dumps({
            "success": True,
            "provider": "mock",
            "query": query,
            "answer": f"Mock web search summary for: {query}",
            "results": [
                {
                    "title": "Mock Tavily Result",
                    "url": "https://example.com/mock-tavily-result",
                    "content": f"Mock result snippet for {query}",
                    "score": 1.0,
                }
            ][:top_k],
            "error": None,
            "error_type": None,
            "mock": True,
        }, ensure_ascii=False)

    config_error = require_real_mode_config(config, need_web=True)
    if config_error:
        return json.dumps({
            "success": False,
            "provider": config.web_mcp.provider,
            "query": query,
            "answer": None,
            "results": [],
            "error": config_error,
            "error_type": "ConfigurationError",
        }, ensure_ascii=False)

    if config.web_mcp.provider != "tavily":
        return json.dumps({
            "success": False,
            "provider": config.web_mcp.provider,
            "query": query,
            "answer": None,
            "results": [],
            "error": f"暂不支持联网 MCP provider: {config.web_mcp.provider}",
            "error_type": "ConfigurationError",
        }, ensure_ascii=False)

    try:
        import httpx

        url = f"{config.web_mcp.base_url}{config.web_mcp.search_endpoint}"
        headers = {
            "Authorization": f"Bearer {config.web_mcp.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "max_results": top_k,
            "search_depth": search_depth,
            "include_answer": True,
        }
        if config.web_mcp.proxy:
            with httpx.Client(proxy=config.web_mcp.proxy, timeout=config.web_mcp.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        else:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=config.web_mcp.timeout,
            )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", [])[:top_k]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content") or item.get("snippet", ""),
                "score": item.get("score"),
            })

        return json.dumps({
            "success": True,
            "provider": "tavily",
            "query": query,
            "answer": data.get("answer"),
            "results": results,
            "error": None,
            "error_type": None,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "provider": "tavily",
            "query": query,
            "answer": None,
            "results": [],
            "error": str(e),
            "error_type": type(e).__name__,
        }, ensure_ascii=False)


MCP_CONFIG = {
    "name": "web_search",
    "description": "联网检索。当前支持 Tavily Search API，用于检索公开网页信息。",
    "category": "retrieval",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "联网检索查询词"
            },
            "max_results": {
                "type": "integer",
                "default": 5,
                "description": "返回结果数量"
            },
            "search_depth": {
                "type": "string",
                "enum": ["basic", "advanced"],
                "default": "basic",
                "description": "Tavily 检索深度"
            }
        },
        "required": ["query"]
    },
    "provider_env": {
        "provider": "WEB_MCP_PROVIDER=tavily",
        "base_url": "WEB_MCP_BASE_URL=https://api.tavily.com",
        "api_key": "WEB_MCP_API_KEY",
    },
}

register_mcp(MCP_CONFIG, web_search)
