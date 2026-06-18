from __future__ import annotations

import os
from pathlib import Path

from storage.base import StorageBackend
from storage.database_storage import DatabaseStorageBackend
from storage.json_storage import JSONStorageBackend


def create_storage_backend(data_dir: Path) -> StorageBackend:
    """
    根据环境变量创建存储后端

    环境变量：
    - STORAGE_BACKEND: json|sqlite|postgres|mysql|database (默认 json)
    - DATABASE_URL: 数据库连接字符串 (用于 sqlite/postgres/mysql)
    - GIT_REPO_URL: Git 仓库地址 (用于 git)
    - GIT_TOKEN: Git 访问令牌 (用于 git)
    - GIT_BRANCH: Git 分支 (默认 main)
    - GIT_FILE_PATH: Git 仓库中的文件路径 (默认 accounts.json)

    在 .env 文件中配置，例如：
    STORAGE_BACKEND=json
    # 或使用数据库
    # STORAGE_BACKEND=postgres
    # DATABASE_URL=postgresql://user:password@localhost:5432/flowith
    """
    backend_type = os.getenv("STORAGE_BACKEND", "json").lower().strip()

    print(f"[storage] Initializing storage backend: {backend_type}")
    print(f"[storage] Supported backends: json (default), sqlite, postgres, mysql, database")
    
    if backend_type == "json":
        # 本地 JSON 文件存储
        # 从环境变量读取路径，否则使用默认值
        file_path = Path(os.getenv("ACCOUNTS_FILE", str(data_dir / "accounts.json")))
        auth_keys_path = Path(os.getenv("AUTH_KEYS_FILE", str(data_dir / "auth_keys.json")))
        print(f"[storage] Using JSON storage:")
        print(f"  - Accounts file: {file_path}")
        print(f"  - Auth keys file: {auth_keys_path}")
        return JSONStorageBackend(file_path, auth_keys_path)
    
    elif backend_type in ("sqlite", "postgres", "postgresql", "mysql", "database"):
        # 数据库存储
        database_url = os.getenv("DATABASE_URL", "").strip()
        
        if not database_url:
            # 如果没有指定 DATABASE_URL，使用本地 SQLite
            database_url = f"sqlite:///{data_dir / 'accounts.db'}"
            print(f"[storage] No DATABASE_URL provided, using local SQLite: {database_url}")
        else:
            print(f"[storage] Using database storage: {_mask_password(database_url)}")
        
        return DatabaseStorageBackend(database_url)
    
    else:
        raise ValueError(
            f"Unknown storage backend: '{backend_type}'. "
            f"Supported backends: json, sqlite, postgres, mysql, database\n"
            f"Set STORAGE_BACKEND in .env file to select a backend.\n"
            f"Example: STORAGE_BACKEND=json (default is local JSON file)"
        )


def _mask_password(url: str) -> str:
    """隐藏数据库连接字符串中的密码"""
    if "://" not in url:
        return url
    try:
        protocol, rest = url.split("://", 1)
        if "@" in rest:
            credentials, host = rest.split("@", 1)
            if ":" in credentials:
                username, _ = credentials.split(":", 1)
                return f"{protocol}://{username}:****@{host}"
        return url
    except Exception:
        return url


def _mask_token(url: str) -> str:
    """隐藏 URL 中的 token"""
    if "@" in url and "://" in url:
        protocol, rest = url.split("://", 1)
        if "@" in rest:
            _, host = rest.split("@", 1)
            return f"{protocol}://****@{host}"
    return url
