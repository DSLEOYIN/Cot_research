"""
Run a small health check against all registered MCPs.

Usage:
    python scripts/check_mcps.py
    python scripts/check_mcps.py --mode mock
    python scripts/check_mcps.py --mode real-missing-config
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcps import execute_mcp  # noqa: E402


EXTERNAL_ENV_KEYS = [
    "DEEPSEEK_API_KEY",
    "OPENAI_API_KEY",
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
    "DB_URI",
]


@dataclass(frozen=True)
class CheckCase:
    name: str
    args: dict[str, Any]
    expected_success: bool
    required_keys: tuple[str, ...] = ("success", "error", "error_type")


MOCK_CASES = [
    CheckCase("llm", {"prompt": "How often should a car be serviced?", "prompt_type": "chat"}, True),
    CheckCase("n2sql", {"query": "monthly Middle East sales"}, True, ("success", "sql", "error", "error_type")),
    CheckCase("sql_executor", {"query": "SELECT 1", "format": "md"}, True),
    CheckCase("knowledge_retrieval", {"query": "terminal sales", "dataset_ids": ["table usage"]}, True),
    CheckCase("time", {"format": "%Y-%m-%d %H:%M:%S", "timezone": "Asia/Shanghai"}, True),
    CheckCase("text_analysis", {"text": "Sales increased by 15% this month.", "task": "sentiment"}, True),
]


REAL_MISSING_CONFIG_CASES = [
    CheckCase("llm", {"prompt": "hello", "prompt_type": "chat"}, False),
    CheckCase("n2sql", {"query": "monthly Middle East sales"}, False, ("success", "sql", "error", "error_type")),
    CheckCase("sql_executor", {"query": "SELECT 1", "format": "md"}, False),
]


REAL_REQUIRED_ENV = [
    "DEEPSEEK_API_KEY or OPENAI_API_KEY",
    "DB_HOST",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
]


REAL_CASES = [
    CheckCase("llm", {"prompt": "请用一句话回复：模型连接正常。", "prompt_type": "chat"}, True),
    CheckCase("n2sql", {"query": "本月中东公司销量多少？"}, True, ("success", "sql", "error", "error_type")),
    CheckCase("sql_executor", {"query": "SELECT 1", "format": "json"}, True),
    CheckCase("knowledge_retrieval", {"query": "终端量", "dataset_ids": ["字段标准查询名检索"]}, True),
    CheckCase("time", {"format": "%Y-%m-%d %H:%M:%S", "timezone": "Asia/Shanghai"}, True),
    CheckCase("text_analysis", {"text": "本月销量同比增长15%", "task": "sentiment"}, True),
]


def configure_environment(mode: str) -> dict[str, str | None]:
    previous = {key: os.environ.get(key) for key in ["APP_MODE", "MOCK_ENABLED", *EXTERNAL_ENV_KEYS]}

    if mode == "mock":
        os.environ["APP_MODE"] = "mock"
        os.environ["MOCK_ENABLED"] = "true"
    elif mode == "real-missing-config":
        os.environ["APP_MODE"] = "real"
        os.environ["MOCK_ENABLED"] = "false"
        for key in EXTERNAL_ENV_KEYS:
            os.environ.pop(key, None)
    elif mode == "real":
        os.environ["APP_MODE"] = "real"
        os.environ["MOCK_ENABLED"] = "false"
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return previous


def restore_environment(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def parse_result(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": f"Invalid JSON result: {exc}",
            "error_type": "InvalidJSON",
            "raw": raw,
        }

    if not isinstance(data, dict):
        return {
            "success": False,
            "error": "MCP result is not a JSON object",
            "error_type": "InvalidResultType",
            "raw": raw,
        }

    return data


def run_case(case: CheckCase) -> tuple[bool, str, dict[str, Any]]:
    raw = execute_mcp(case.name, **case.args)
    data = parse_result(raw)

    missing_keys = [key for key in case.required_keys if key not in data]
    if missing_keys:
        return False, f"missing keys: {', '.join(missing_keys)}", data

    if data.get("success") is not case.expected_success:
        return False, f"expected success={case.expected_success}, got {data.get('success')}", data

    if case.expected_success is False and not data.get("error"):
        return False, "failure case did not include an error message", data

    return True, "ok", data


def run_suite(mode: str, cases: list[CheckCase]) -> bool:
    previous = configure_environment(mode)
    all_ok = True
    try:
        print(f"\nMCP health check: {mode}")
        print("-" * 72)
        print(f"{'MCP':<24} {'STATUS':<8} DETAILS")
        print("-" * 72)

        for case in cases:
            ok, details, data = run_case(case)
            all_ok = all_ok and ok
            status = "OK" if ok else "FAIL"
            if ok and data.get("success") is False:
                details = f"graceful failure: {data.get('error_type') or 'UnknownError'}"
            print(f"{case.name:<24} {status:<8} {details}")
    finally:
        restore_environment(previous)

    return all_ok


def missing_real_config() -> list[str]:
    missing = []
    if not (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        missing.append("DEEPSEEK_API_KEY or OPENAI_API_KEY")
    for key in ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]:
        if not os.environ.get(key):
            missing.append(key)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MCP health in mock and missing-config real modes.")
    parser.add_argument(
        "--mode",
        choices=["mock", "real-missing-config", "real", "all"],
        default="all",
        help="Which health check suite to run.",
    )
    args = parser.parse_args()

    if args.mode == "real":
        missing = missing_real_config()
        if missing:
            print("Real MCP health check is not ready. Missing config:")
            for item in missing:
                print(f"- {item}")
            print("\nFill .env or environment variables, then run:")
            print("python scripts/check_mcps.py --mode real")
            return 2

    suites = []
    if args.mode in {"mock", "all"}:
        suites.append(("mock", MOCK_CASES))
    if args.mode in {"real-missing-config", "all"}:
        suites.append(("real-missing-config", REAL_MISSING_CONFIG_CASES))
    if args.mode == "real":
        suites.append(("real", REAL_CASES))

    all_ok = True
    for mode, cases in suites:
        all_ok = run_suite(mode, cases) and all_ok

    print("\nResult:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
