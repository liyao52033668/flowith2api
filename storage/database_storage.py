from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import Column, String, Text, create_engine, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from storage.base import StorageBackend

Base = declarative_base()


class AccountModel(Base):
    """账号数据模型"""
    __tablename__ = "flowith_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    access_token = Column(Text, unique=True, nullable=False)
    access_token_hash = Column(String(32), unique=True, nullable=False, index=True)
    data = Column(Text, nullable=False)  # JSON 格式存储完整账号数据


class AuthKeyModel(Base):
    """鉴权密钥数据模型"""
    __tablename__ = "flowith_auth_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_id = Column(String(255), unique=True, nullable=False, index=True)
    data = Column(Text, nullable=False)


class ConfigModel(Base):
    """应用配置数据模型"""
    __tablename__ = "flowith_app_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(255), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)


class DatabaseStorageBackend(StorageBackend):
    """数据库存储后端（支持 SQLite、PostgreSQL、MySQL 等）"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,  # 自动检测连接是否有效
            pool_recycle=3600,   # 1小时回收连接
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def load_accounts(self) -> list[dict[str, Any]]:
        """从数据库加载账号数据"""
        session = self.Session()
        try:
            accounts = []
            for row in session.query(AccountModel).all():
                try:
                    account_data = json.loads(row.data)
                    if isinstance(account_data, dict):
                        accounts.append(account_data)
                except json.JSONDecodeError:
                    continue
            return accounts
        finally:
            session.close()

    def save_accounts(self, accounts: list[dict[str, Any]]) -> None:
        """保存账号数据到数据库"""
        self._save_rows(AccountModel, accounts, "access_token")

    def load_auth_keys(self) -> list[dict[str, Any]]:
        """从数据库加载鉴权密钥数据"""
        return self._load_rows(AuthKeyModel)

    def save_auth_keys(self, auth_keys: list[dict[str, Any]]) -> None:
        """保存鉴权密钥数据到数据库"""
        self._save_rows(AuthKeyModel, auth_keys, "id", "key_id")

    def _load_rows(self, model: type[AccountModel] | type[AuthKeyModel]) -> list[dict[str, Any]]:
        session = self.Session()
        try:
            items = []
            for row in session.query(model).all():
                try:
                    item_data = json.loads(row.data)
                    if isinstance(item_data, dict):
                        items.append(item_data)
                except json.JSONDecodeError:
                    continue
            return items
        finally:
            session.close()

    def _save_rows(
        self,
        model: type[AccountModel] | type[AuthKeyModel],
        items: list[dict[str, Any]],
        source_key: str,
        target_key: str | None = None,
    ) -> None:
        session = self.Session()
        try:
            session.query(model).delete()
            for item in items:
                if not isinstance(item, dict):
                    continue
                key_value = str(item.get(source_key) or "").strip()
                if not key_value:
                    continue
                if model == AccountModel:
                    token_hash = hashlib.md5(key_value.encode('utf-8')).hexdigest()
                    session.add(
                        model(
                            access_token=key_value,
                            access_token_hash=token_hash,
                            data=json.dumps(item, ensure_ascii=False),
                        )
                    )
                else:
                    session.add(
                        model(
                            **{target_key or source_key: key_value},
                            data=json.dumps(item, ensure_ascii=False),
                        )
                    )
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            session = self.Session()
            try:
                # 尝试执行简单查询
                session.execute(text("SELECT 1"))
                count = session.query(AccountModel).count()
                auth_key_count = session.query(AuthKeyModel).count()
                return {
                    "status": "healthy",
                    "backend": "database",
                    "database_url": self._mask_password(self.database_url),
                    "account_count": count,
                    "auth_key_count": auth_key_count,
                }
            finally:
                session.close()
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "database",
                "error": str(e),
            }

    def get_backend_info(self) -> dict[str, Any]:
        """获取存储后端信息"""
        db_type = "unknown"
        if "sqlite" in self.database_url:
            db_type = "sqlite"
        elif "postgresql" in self.database_url or "postgres" in self.database_url:
            db_type = "postgresql"
        elif "mysql" in self.database_url:
            db_type = "mysql"

        return {
            "type": "database",
            "db_type": db_type,
            "description": f"数据库存储 ({db_type})",
            "database_url": self._mask_password(self.database_url),
        }

    # ==================== 配置管理实现 ====================
    def load_config(self) -> dict[str, Any]:
        """从数据库加载应用配置"""
        session = self.Session()
        try:
            config = {}
            for row in session.query(ConfigModel).all():
                try:
                    # 尝试解析 JSON，如果失败则直接存储原始值
                    value = json.loads(row.config_value)
                    config[row.config_key] = value
                except json.JSONDecodeError:
                    config[row.config_key] = row.config_value
            return config
        finally:
            session.close()

    def save_config(self, config: dict[str, Any]) -> None:
        """保存应用到数据库"""
        session = self.Session()
        try:
            # 删除所有现有配置
            session.query(ConfigModel).delete()
            # 插入新配置
            for key, value in config.items():
                session.add(
                    ConfigModel(
                        config_key=str(key),
                        config_value=json.dumps(value, ensure_ascii=False),
                    )
                )
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        session = self.Session()
        try:
            row = session.query(ConfigModel).filter(
                ConfigModel.config_key == key
            ).first()
            if row:
                try:
                    return json.loads(row.config_value)
                except json.JSONDecodeError:
                    return row.config_value
            return default
        finally:
            session.close()

    def set_config(self, key: str, value: Any) -> None:
        """设置配置项"""
        session = self.Session()
        try:
            # 先删除现有配置
            session.query(ConfigModel).filter(
                ConfigModel.config_key == key
            ).delete()
            # 插入新配置
            session.add(
                ConfigModel(
                    config_key=str(key),
                    config_value=json.dumps(value, ensure_ascii=False),
                )
            )
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
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
