from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """抽象存储后端基类"""

    # ==================== 账号/Token 管理 ====================
    @abstractmethod
    def load_accounts(self) -> list[dict[str, Any]]:
        """加载所有账号数据（tokens）"""
        pass

    @abstractmethod
    def save_accounts(self, accounts: list[dict[str, Any]]) -> None:
        """保存所有账号数据"""
        pass

    # ==================== 鉴权密钥管理 ====================
    @abstractmethod
    def load_auth_keys(self) -> list[dict[str, Any]]:
        """加载所有鉴权密钥数据"""
        pass

    @abstractmethod
    def save_auth_keys(self, auth_keys: list[dict[str, Any]]) -> None:
        """保存所有鉴权密钥数据"""
        pass

    # ==================== 应用配置管理 ====================
    @abstractmethod
    def load_config(self) -> dict[str, Any]:
        """加载应用配置（server_host, admin, api_key 等）"""
        pass

    @abstractmethod
    def save_config(self, config: dict[str, Any]) -> None:
        """保存应用配置"""
        pass

    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        pass

    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """设置配置项"""
        pass

    # ==================== 健康检查 ====================
    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """健康检查，返回存储后端状态"""
        pass

    @abstractmethod
    def get_backend_info(self) -> dict[str, Any]:
        """获取存储后端信息"""
        pass
