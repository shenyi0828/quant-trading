"""数据中心配置"""
from pathlib import Path
from typing import Optional

class Config:
    """数据中心全局配置"""
    
    # 数据库路径
    DATABASE_PATH: Path = Path(__file__).parent.parent / "data" / "market.db"
    
    # 数据缓存目录
    CACHE_DIR: Path = Path(__file__).parent.parent / "data" / "cache"
    
    # AKShare 配置
    AKSHARE_REQUEST_TIMEOUT: int = 30  # 秒
    AKSHARE_MAX_RETRIES: int = 3
    
    # 数据更新频率
    DAILY_UPDATE_TIME: str = "16:00"  # 每日更新时间 (A 股收盘后)
    
    @classmethod
    def ensure_directories(cls) -> None:
        """确保必要的目录存在"""
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)