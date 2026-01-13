"""缓存管理工具类"""
import time
from typing import Dict, Any, Optional, Callable, Tuple
from collections import OrderedDict
from threading import Lock
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LRUCache:
    """LRU缓存实现（线程安全）"""
    
    def __init__(self, max_size: int = 1000):
        """
        初始化LRU缓存
        
        Args:
            max_size: 最大缓存数量
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                # 移动到末尾（最近使用）
                self._cache.move_to_end(key)
                return self._cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                # 更新现有值并移动到末尾
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                # 添加新值
                self._cache[key] = value
                # 如果超过最大大小，删除最旧的项
                if len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    logger.debug(f"LRU缓存已满，删除最旧项: {oldest_key}")
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list:
        """获取所有键"""
        with self._lock:
            return list(self._cache.keys())


class TTLCache:
    """TTL缓存实现（带过期时间）"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        初始化TTL缓存
        
        Args:
            default_ttl: 默认TTL（秒）
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（如果未过期）"""
        with self._lock:
            if key in self._cache:
                value, expire_time = self._cache[key]
                if time.time() < expire_time:
                    return value
                else:
                    # 已过期，删除
                    del self._cache[key]
                    logger.debug(f"TTL缓存项已过期: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            expire_time = time.time() + (ttl or self.default_ttl)
            self._cache[key] = (value, expire_time)
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """清理过期项，返回清理的数量"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expire_time) in self._cache.items()
                if expire_time <= current_time
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")
            return len(expired_keys)
    
    def size(self) -> int:
        """获取缓存大小（包括未过期的项）"""
        with self._lock:
            return len(self._cache)


class LRUTTLCache:
    """LRU + TTL 组合缓存"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化LRU+TTL缓存
        
        Args:
            max_size: 最大缓存数量
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（检查TTL和LRU）"""
        with self._lock:
            if key in self._cache:
                value, expire_time = self._cache[key]
                current_time = time.time()
                
                if current_time < expire_time:
                    # 未过期，移动到末尾（最近使用）
                    self._cache.move_to_end(key)
                    return value
                else:
                    # 已过期，删除
                    del self._cache[key]
                    logger.debug(f"LRU+TTL缓存项已过期: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            expire_time = time.time() + (ttl or self.default_ttl)
            
            if key in self._cache:
                # 更新现有值并移动到末尾
                self._cache.move_to_end(key)
                self._cache[key] = (value, expire_time)
            else:
                # 添加新值
                self._cache[key] = (value, expire_time)
                # 如果超过最大大小，删除最旧的项
                if len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    logger.debug(f"LRU+TTL缓存已满，删除最旧项: {oldest_key}")
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """清理过期项，返回清理的数量"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expire_time) in self._cache.items()
                if expire_time <= current_time
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")
            return len(expired_keys)
    
    def size(self) -> int:
        """获取缓存大小（包括未过期的项）"""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list:
        """获取所有键（包括未过期的）"""
        with self._lock:
            return list(self._cache.keys())
