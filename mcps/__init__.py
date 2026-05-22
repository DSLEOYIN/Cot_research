"""
MCPs - 工具执行层
每个 MCP 是一个具体的可执行工具

用户可自行添加新的 MCP 文件来扩展系统工具
"""

from typing import Callable, Any, Dict
import importlib
import sys

# MCP 注册表，包含配置与函数引用
MCP_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_mcp(mcp_config: dict, func: Callable = None):
    """
    注册 MCP 到注册表。支持装饰器方式与直接调用方式。
    """
    name = mcp_config.get("name")
    if not name:
        return

    # 直接调用方式：register_mcp(MCP_CONFIG, my_function)
    if func is not None:
        MCP_REGISTRY[name] = {
            "config": mcp_config,
            "func": func
        }
        return func

    # 装饰器方式：
    # @register_mcp(MCP_CONFIG)
    # def my_function(): ...
    def decorator(wrapped_func: Callable):
        MCP_REGISTRY[name] = {
            "config": mcp_config,
            "func": wrapped_func
        }
        return wrapped_func
    return decorator


def get_mcp(name: str) -> dict | None:
    """获取 MCP 配置"""
    # 如果未注册，尝试动态载入对应模块进行注册
    if name not in MCP_REGISTRY:
        try:
            importlib.import_module(f"mcps.{name}_mcp")
        except ImportError:
            pass
            
    if name in MCP_REGISTRY:
        return MCP_REGISTRY[name]["config"]
    return None


def list_mcps() -> list[dict]:
    """列出所有已注册的 MCP 配置"""
    # 强制预加载所有内置的 MCP 模块
    modules = ["sql_executor", "knowledge_retrieval", "llm", "time", "text_analysis", "n2sql"]
    for mod in modules:
        if mod not in MCP_REGISTRY:
            try:
                importlib.import_module(f"mcps.{mod}_mcp")
            except ImportError:
                pass
                
    return [entry["config"] for entry in MCP_REGISTRY.values()]


def list_mcp_names() -> list[str]:
    """列出所有已注册的 MCP 名称"""
    list_mcps() # 预载入
    return list(MCP_REGISTRY.keys())


def execute_mcp(name: str, **kwargs) -> str:
    """
    执行已注册的 MCP 函数。
    """
    # 尝试加载模块确保注册
    if name not in MCP_REGISTRY:
        try:
            importlib.import_module(f"mcps.{name}_mcp")
        except ImportError:
            pass

    if name in MCP_REGISTRY:
        entry = MCP_REGISTRY[name]
        func = entry["func"]
        try:
            import json
            result = func(**kwargs)
            if isinstance(result, str):
                try:
                    result_data = json.loads(result)
                except Exception:
                    return json.dumps({
                        "success": True,
                        "data": result,
                        "error": None,
                        "error_type": None
                    }, ensure_ascii=False)
            else:
                result_data = result

            if isinstance(result_data, dict):
                result_data.setdefault("success", True)
                result_data.setdefault("error", None)
                result_data.setdefault("error_type", None)
                return json.dumps(result_data, ensure_ascii=False)

            return json.dumps({
                "success": True,
                "data": result_data,
                "error": None,
                "error_type": None
            }, ensure_ascii=False)
        except Exception as e:
            import json
            return json.dumps({
                "success": False,
                "error": f"Error executing MCP {name}: {str(e)}",
                "error_type": type(e).__name__
            }, ensure_ascii=False)
            
    import json
    return json.dumps({
        "success": False,
        "error": f"MCP {name} not found in registry",
        "error_type": "MCPNotFound"
    }, ensure_ascii=False)


# 导入所有 MCP 以自动注册
# 必须在这里导入，因为需要用到 register_mcp 函数
from . import sql_executor_mcp
from . import knowledge_retrieval_mcp
from . import llm_mcp
from . import time_mcp
from . import text_analysis_mcp
from . import n2sql_mcp

__all__ = ["MCP_REGISTRY", "get_mcp", "list_mcps", "list_mcp_names", "execute_mcp"]
