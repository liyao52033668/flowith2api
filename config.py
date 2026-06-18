"""
统一配置管理模块

使用 storage 模块统一管理所有配置：
- tokens (账号/Token)
- auth_keys (鉴权密钥)
- app_config (应用配置)

通过环境变量 STORAGE_BACKEND 选择存储后端：
- json (默认) - 本地 JSON 文件
- sqlite - 本地 SQLite
- postgres - PostgreSQL
- mysql - MySQL
"""

from __future__ import annotations

import os
import bcrypt
import uuid
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 从环境变量读取配置，否则使用默认值
_BASE_DIR = Path(__file__).parent
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", str(_BASE_DIR / "data")))
CONFIG_FILE = Path(os.getenv("CONFIG_FILE", str(CONFIG_DIR / "config.json")))
TOKENS_FILE = Path(os.getenv("TOKENS_FILE", str(CONFIG_DIR / "tokens.json")))
DB_FILE = Path(os.getenv("DB_FILE", str(CONFIG_DIR / "flowith.db")))

# JSON 存储文件路径
ACCOUNTS_FILE = Path(os.getenv("ACCOUNTS_FILE", str(CONFIG_DIR / "accounts.json")))
AUTH_KEYS_FILE = Path(os.getenv("AUTH_KEYS_FILE", str(CONFIG_DIR / "auth_keys.json")))

# 确保目录存在
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# 默认配置
DEFAULT_CONFIG = {
    "server_host": "0.0.0.0",
    "server_port": 8000,
    "admin_username": "admin",
    "admin_password_hash": bcrypt.hashpw("admin".encode(), bcrypt.gensalt()).decode(),
    "api_key": "sk-flowith",
    "proxy_enabled": False,
    "proxy_url": "",
    "debug": False,
}


class AppConfig:
    """
    统一配置管理类

    使用 storage 模块作为后端，支持多种存储方式。
    兼容原有的 config.py API。
    """

    def __init__(self):
        """初始化配置管理器"""
        # 延迟导入，避免循环依赖
        from storage.factory import create_storage_backend

        # 根据环境变量选择存储后端
        backend_type = os.getenv("STORAGE_BACKEND", "json").lower().strip()
        print(f"[config] Initializing with storage backend: {backend_type}")

        # 创建存储后端
        if backend_type == "json":
            self._storage = create_storage_backend(CONFIG_DIR)
        else:
            # 对于数据库后端，使用 CONFIG_DIR 作为数据目录
            self._storage = create_storage_backend(CONFIG_DIR)

        # 加载配置
        self._load_or_initialize()

    def _load_or_initialize(self):
        """加载现有配置或初始化默认配置"""
        # 加载应用配置
        config_data = self._storage.load_config()

        # 如果没有配置，初始化默认配置
        if not config_data or "admin_username" not in config_data:
            # 迁移现有 tokens（如果有的话）
            existing_tokens = self._storage.load_accounts()
            if existing_tokens:
                config_data["tokens"] = existing_tokens
            else:
                config_data.update(dict(DEFAULT_CONFIG))
                config_data["tokens"] = []

            self._storage.save_config(config_data)
            print("[config] Initialized with default configuration")
        else:
            print("[config] Loaded existing configuration")

        # 缓存配置数据
        self._config_cache = config_data

    def _reload(self):
        """重新加载配置"""
        self._config_cache = self._storage.load_config()

    # ==================== Token 管理 (兼容原有 API) ====================

    @property
    def tokens(self) -> list:
        """获取所有 tokens"""
        return self._config_cache.get("tokens", [])

    @tokens.setter
    def tokens(self, value: list):
        """设置 tokens"""
        self._config_cache["tokens"] = value
        self._storage.save_config(self._config_cache)

    def get_tokens(self) -> list[dict[str, Any]]:
        """获取 tokens 列表"""
        return self.tokens

    def set_tokens(self, tokens: list[dict[str, Any]]) -> None:
        """设置 tokens 列表"""
        self.tokens = tokens

    # ==================== 配置管理 (兼容原有 API) ====================

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config_cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._config_cache[key] = value
        self._storage.save_config(self._config_cache)

    def update(self, d: dict[str, Any]) -> None:
        """批量更新配置"""
        self._config_cache.update(d)
        self._storage.save_config(self._config_cache)

    # ==================== 兼容原有 config.py 的属性 ====================

    @property
    def admin_username(self) -> str:
        return self._config_cache.get("admin_username", "admin")

    @admin_username.setter
    def admin_username(self, value: str) -> None:
        self.set("admin_username", value)

    @property
    def admin_password_hash(self) -> str:
        return self._config_cache.get("admin_password_hash", "")

    @admin_password_hash.setter
    def admin_password_hash(self, value: str) -> None:
        self.set("admin_password_hash", value)

    @property
    def api_key(self) -> str:
        return self._config_cache.get("api_key", "sk-flowith")

    @api_key.setter
    def api_key(self, value: str) -> None:
        self.set("api_key", value)

    @property
    def server_host(self) -> str:
        return self._config_cache.get("server_host", "0.0.0.0")

    @property
    def server_port(self) -> int:
        return self._config_cache.get("server_port", 8000)

    # ==================== 存储后端信息 ====================

    @property
    def storage_backend(self):
        """获取存储后端实例"""
        return self._storage

    def get_backend_info(self) -> dict[str, Any]:
        """获取存储后端信息"""
        return self._storage.get_backend_info()

    def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return self._storage.health_check()


# 全局配置实例
config = AppConfig()
