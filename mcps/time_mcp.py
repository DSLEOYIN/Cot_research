"""
时间 MCP

获取当前时间
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TypedDict, Literal
from mcps import register_mcp


class TimeInput(TypedDict):
    format: str
    timezone: Literal[
        "UTC",
        "Asia/Shanghai",
        "Asia/Tokyo",
        "Asia/Dubai",
        "America/New_York",
        "Europe/London"
    ]


class TimeResult(TypedDict):
    success: bool
    time: str
    timestamp: int
    timezone: str


def get_current_time(
    format: str = "%Y-%m-%d %H:%M:%S",
    timezone: str = "Asia/Shanghai"
) -> str:
    """
    获取当前时间 MCP

    Args:
        format: 时间格式（strftime标准）
        timezone: 时区

    Returns:
        格式化的时间字符串

    支持的时区:
        - UTC
        - Asia/Shanghai (亚洲/上海)
        - Asia/Tokyo (亚洲/东京)
        - Asia/Dubai (亚洲/迪拜)
        - America/New_York (美洲/纽约)
        - Europe/London (欧洲/伦敦)
    """
    try:
        from datetime import timezone as pytz
        import pytz as tz

        # 获取时区对象
        tz_obj = tz.timezone(timezone)

        # 获取当前时间（UTC）并转换到目标时区
        utc_now = datetime.now(tz.utc)
        local_time = utc_now.astimezone(tz_obj)

        formatted_time = local_time.strftime(format)
        timestamp = int(utc_now.timestamp())

        return json.dumps({
            "success": True,
            "time": formatted_time,
            "timestamp": timestamp,
            "timezone": timezone,
            "formatted": local_time.isoformat()
        }, ensure_ascii=False)

    except ImportError:
        # 如果没有 pytz，使用简单实现
        now = datetime.now()
        return json.dumps({
            "success": True,
            "time": now.strftime(format),
            "timestamp": int(datetime.now().timestamp()),
            "timezone": timezone,
            "formatted": now.isoformat()
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "time": "",
            "timestamp": 0,
            "timezone": timezone
        }, ensure_ascii=False)


MCP_CONFIG = {
    "name": "time",
    "description": "获取当前时间。用于记录查询时间、生成数据口径等场景。",
    "category": "utility",
    "inputSchema": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "default": "%Y-%m-%d %H:%M:%S",
                "description": "时间格式，strftime标准，如 %Y-%m-%d %H:%M:%S"
            },
            "timezone": {
                "type": "string",
                "enum": [
                    "UTC",
                    "Asia/Shanghai",
                    "Asia/Tokyo",
                    "Asia/Dubai",
                    "Asia/Ho_Chi_Minh",
                    "Asia/Singapore",
                    "America/New_York",
                    "America/Los_Angeles",
                    "America/Chicago",
                    "America/Sao_Paulo",
                    "Europe/London",
                    "Europe/Berlin",
                    "Europe/Moscow",
                    "Australia/Sydney",
                    "Pacific/Auckland",
                    "Africa/Cairo"
                ],
                "default": "Asia/Shanghai",
                "description": "时区"
            }
        },
        "required": ["format"]
    },
    "examples": [
        {
            "input": {"format": "%Y-%m-%d %H:%M:%S", "timezone": "Asia/Shanghai"},
            "description": "获取当前时间（上海时区）"
        }
    ]
}

register_mcp(MCP_CONFIG, get_current_time)
