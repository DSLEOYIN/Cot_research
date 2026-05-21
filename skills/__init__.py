"""
Skills - 业务能力单元
每个 Skill 封装一个完整的业务能力，包含多个 MCP 工具

用户可自行添加新的 Skill 文件来扩展系统能力
"""

from typing import Any

# Skill 注册表
SKILL_REGISTRY: dict[str, dict] = {}


def register_skill(skill_config: dict):
    """注册 Skill 到注册表"""
    name = skill_config.get("name")
    if name:
        SKILL_REGISTRY[name] = skill_config


def get_skill(name: str) -> dict | None:
    """获取 Skill 配置"""
    return SKILL_REGISTRY.get(name)


def list_skills() -> list[dict]:
    """列出所有已注册的 Skill"""
    return list(SKILL_REGISTRY.values())


def list_skill_names() -> list[str]:
    """列出所有 Skill 名称"""
    return list(SKILL_REGISTRY.keys())


# 导入所有 Skill 以自动注册
from . import data_query_skill
from . import chat_skill
from . import yoy_yoy_analysis_skill

__all__ = ["SKILL_REGISTRY", "get_skill", "list_skills", "list_skill_names"]
