"""
Centralized runtime configuration.

The project should be able to start without real credentials. Real external
services are used only when APP_MODE=real and the required settings exist.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parent


def _load_dotenv() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


@dataclass(frozen=True)
class ModelConfig:
    api_key: str | None
    base_url: str
    model: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class DatabaseConfig:
    host: str | None
    port: int
    user: str | None
    password: str | None
    name: str | None
    charset: str
    allowed_tables: tuple[str, ...]
    max_rows: int
    connect_timeout: int
    read_timeout: int
    write_timeout: int


@dataclass(frozen=True)
class SSHConfig:
    enabled: bool
    host: str | None
    port: int
    user: str | None
    password: str | None


@dataclass(frozen=True)
class DifyConfig:
    enabled: bool
    base_url: str
    api_key: str | None
    dataset_id: str | None


@dataclass(frozen=True)
class AppConfig:
    app_mode: str
    mock_enabled: bool
    model: ModelConfig
    database: DatabaseConfig
    ssh: SSHConfig
    dify: DifyConfig


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _database_from_uri(db_uri: str) -> DatabaseConfig:
    parsed = urlparse(db_uri)
    return DatabaseConfig(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        name=parsed.path.lstrip("/") or None,
        charset=os.getenv("DB_CHARSET", "utf8mb4"),
        allowed_tables=_allowed_tables(),
        max_rows=_env_int("SQL_MAX_ROWS", 500),
        connect_timeout=_env_int("DB_CONNECT_TIMEOUT", 5),
        read_timeout=_env_int("DB_READ_TIMEOUT", 30),
        write_timeout=_env_int("DB_WRITE_TIMEOUT", 30),
    )


def _parse_ssh_config(root_dir: Path) -> SSHConfig:
    # 1. Try standard environment variables
    ssh_host = os.getenv("SSH_HOST")
    ssh_port = _env_int("SSH_PORT", 22)
    ssh_user = os.getenv("SSH_USER")
    ssh_password = os.getenv("SSH_PASSWORD")

    if ssh_host and ssh_user:
        return SSHConfig(
            enabled=_env_bool("SSH_ENABLED", True),
            host=ssh_host,
            port=ssh_port,
            user=ssh_user,
            password=ssh_password,
        )

    # 2. Fallback to parsing user's custom format in .env
    env_path = root_dir / ".env"
    if not env_path.exists():
        return SSHConfig(enabled=False, host=None, port=22, user=None, password=None)

    import re
    try:
        content = env_path.read_text(encoding="utf-8")
        
        # Regex matching an IP and port (e.g. 10.30.8.37：9081)
        ip_port_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:：](\d+)", content)
        if ip_port_match:
            ssh_host = ip_port_match.group(1)
            ssh_port = int(ip_port_match.group(2))
            
        # Search for user: "账号：model" or "账号:model"
        user_match = re.search(r"(?:账号|user|username)[:：\s=]+([^\s\r\n]+)", content)
        if user_match:
            ssh_user = user_match.group(1).strip()
            
        # Search for password: "密码：^Dskj@Model1" or "密码:^Dskj@Model1"
        password_match = re.search(r"(?:密码|password|pass)[:：\s=]+([^\s\r\n]+)", content)
        if password_match:
            ssh_password = password_match.group(1).strip()
    except Exception:
        pass

    enabled = bool(ssh_host and ssh_user)
    return SSHConfig(
        enabled=enabled,
        host=ssh_host,
        port=ssh_port,
        user=ssh_user,
        password=ssh_password,
    )


def get_config(db_uri: str | None = None) -> AppConfig:
    app_mode = os.getenv("APP_MODE", "mock").strip().lower()
    mock_enabled = app_mode == "mock" or _env_bool("MOCK_ENABLED", app_mode != "real")

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = ModelConfig(
        api_key=api_key,
        base_url=os.getenv("MODEL_BASE_URL", "https://api.deepseek.com/chat/completions"),
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=_env_float("MODEL_TEMPERATURE", 0.2),
        max_tokens=_env_int("MODEL_MAX_TOKENS", 4096),
    )

    if db_uri:
        database = _database_from_uri(db_uri)
    else:
        database = DatabaseConfig(
            host=os.getenv("DB_HOST"),
            port=_env_int("DB_PORT", 3306),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            name=os.getenv("DB_NAME"),
            charset=os.getenv("DB_CHARSET", "utf8mb4"),
            allowed_tables=_allowed_tables(),
            max_rows=_env_int("SQL_MAX_ROWS", 500),
            connect_timeout=_env_int("DB_CONNECT_TIMEOUT", 5),
            read_timeout=_env_int("DB_READ_TIMEOUT", 30),
            write_timeout=_env_int("DB_WRITE_TIMEOUT", 30),
        )

    ssh = _parse_ssh_config(ROOT_DIR)

    dify_enabled = _env_bool("DIFY_ENABLED", True)
    dify_base_url = os.getenv("DIFY_BASE_URL", "http://10.30.11.215:9879").rstrip("/")
    dify_api_key = os.getenv("DIFY_API_KEY", "dataset-S5L6smkj8ovnSz8rMl5DZUvj")
    dify_dataset_id = os.getenv("DIFY_DATASET_ID", "ffa84ba6-4ec9-44a0-8f6d-594b27f7a829")

    dify = DifyConfig(
        enabled=dify_enabled and bool(dify_api_key and dify_dataset_id),
        base_url=dify_base_url,
        api_key=dify_api_key,
        dataset_id=dify_dataset_id,
    )

    return AppConfig(
        app_mode=app_mode,
        mock_enabled=mock_enabled,
        model=model,
        database=database,
        ssh=ssh,
        dify=dify,
    )


def _allowed_tables() -> tuple[str, ...]:
    # 1. If DB_ALLOWED_TABLES is explicitly set in the environment, use it
    if os.getenv("DB_ALLOWED_TABLES"):
        raw = os.getenv("DB_ALLOWED_TABLES")
        return tuple(table.strip().lower() for table in raw.split(",") if table.strip())
    
    # 2. Otherwise, dynamically load from the active scenario theme
    try:
        import theme_loader
        tables = theme_loader.get_active_theme_tables()
        if tables:
            return tables
    except Exception:
        pass

    # 3. Fallback default tables
    return (
        "v_dm_sal_wolesale_terminal_dly",
        "v_dm_sal_stock_dly",
        "v_dm_sal_sc_order_dly",
        "v_dm_sal_scheduling_dly"
    )


def require_real_mode_config(config: AppConfig, *, need_model: bool = False, need_db: bool = False) -> str | None:
    if need_model and not config.model.api_key:
        return "real 模式缺少 DEEPSEEK_API_KEY 或 OPENAI_API_KEY"

    if need_db:
        db = config.database
        missing = [
            name for name, value in {
                "DB_HOST": db.host,
                "DB_USER": db.user,
                "DB_PASSWORD": db.password,
                "DB_NAME": db.name,
            }.items()
            if not value
        ]
        if missing:
            return f"real 模式缺少数据库配置: {', '.join(missing)}"

    return None
