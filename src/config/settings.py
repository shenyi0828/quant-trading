"""Configuration module with YAML loading and validation.

This module provides a configuration system that:
- Loads settings from YAML files
- Validates settings using pydantic
- Supports environment variable overrides
- Implements singleton pattern for global settings

Example YAML config (config.yaml):
    server:
        host: "0.0.0.0"
        port: 8000
        debug: false
    trading:
        initial_capital: 1000000.0
        commission_rate: 0.001
        default_exchange: "sse"
    risk:
        position_limit_ratio: 0.3
        order_limit_amount: 50000.0
        daily_loss_limit: 0.02
        concentration_limit: 10
    data:
        data_source: "akshare"
        cache_path: "./data/cache"

Example usage:
    from config import Settings
    
    # Load from YAML file
    settings = Settings.load_from_yaml("config.yaml")
    
    # Access config sections
    print(settings.server.host)
    print(settings.trading.initial_capital)
    
    # Get global singleton
    settings = Settings.get()
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, ClassVar

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class ServerConfig(BaseModel):
    """Server configuration for FastAPI server.
    
    Attributes:
        host: Server host address
        port: Server port number
        debug: Debug mode flag
    """
    
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port number (1-65535)"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            }
        }


class TradingConfig(BaseModel):
    """Trading configuration for TradingService.
    
    Attributes:
        initial_capital: Initial capital for trading
        commission_rate: Commission rate per trade
        default_exchange: Default exchange for orders
    """
    
    initial_capital: float = Field(
        default=1000000.0,
        ge=0,
        description="Initial capital for trading (must be >= 0)"
    )
    commission_rate: float = Field(
        default=0.001,
        ge=0,
        le=1,
        description="Commission rate per trade (0-1)"
    )
    default_exchange: str = Field(
        default="sse",
        description="Default exchange for orders (sse, szse, shfe, etc.)"
    )
    
    @field_validator("default_exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name."""
        valid_exchanges = ["sse", "szse", "shfe", "cffex", "dce", "czce"]
        if v.lower() not in valid_exchanges:
            raise ValueError(f"Invalid exchange '{v}'. Valid exchanges: {valid_exchanges}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "initial_capital": 1000000.0,
                "commission_rate": 0.001,
                "default_exchange": "sse"
            }
        }


class RiskConfig(BaseModel):
    """Risk management configuration for RiskChecker.
    
    Attributes:
        position_limit_ratio: Maximum position ratio per stock
        order_limit_amount: Maximum order amount
        daily_loss_limit: Maximum daily loss ratio
        concentration_limit: Maximum number of positions
    """
    
    position_limit_ratio: float = Field(
        default=0.3,
        ge=0,
        le=1,
        description="Maximum position ratio per stock (0-1)"
    )
    order_limit_amount: float = Field(
        default=50000.0,
        ge=0,
        description="Maximum order amount (must be >= 0)"
    )
    daily_loss_limit: float = Field(
        default=0.02,
        ge=0,
        le=1,
        description="Maximum daily loss ratio (0-1)"
    )
    concentration_limit: int = Field(
        default=10,
        ge=1,
        description="Maximum number of positions (must be >= 1)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "position_limit_ratio": 0.3,
                "order_limit_amount": 50000.0,
                "daily_loss_limit": 0.02,
                "concentration_limit": 10
            }
        }


class DataConfig(BaseModel):
    """Data configuration for DataAPI.
    
    Attributes:
        data_source: Data source type
        cache_path: Path to cache directory
    """
    
    data_source: str = Field(
        default="akshare",
        description="Data source type (akshare, tushare, etc.)"
    )
    cache_path: str = Field(
        default="./data/cache",
        description="Path to cache directory"
    )
    
    @field_validator("cache_path")
    @classmethod
    def validate_cache_path(cls, v: str) -> str:
        """Validate and normalize cache path."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path.resolve())
    
    class Config:
        json_schema_extra = {
            "example": {
                "data_source": "akshare",
                "cache_path": "./data/cache"
            }
        }


class Settings(BaseModel):
    """Main settings class containing all configuration sections.
    
    This class provides:
    - YAML file loading
    - Environment variable overrides
    - Singleton pattern for global settings
    - Validation using pydantic
    
    Attributes:
        server: Server configuration
        trading: Trading configuration
        risk: Risk management configuration
        data: Data configuration
    """
    
    server: ServerConfig = Field(default_factory=ServerConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    
    _instance: ClassVar[Optional[Settings]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "server": {
                    "host": "0.0.0.0",
                    "port": 8000,
                    "debug": False
                },
                "trading": {
                    "initial_capital": 1000000.0,
                    "commission_rate": 0.001,
                    "default_exchange": "sse"
                },
                "risk": {
                    "position_limit_ratio": 0.3,
                    "order_limit_amount": 50000.0,
                    "daily_loss_limit": 0.02,
                    "concentration_limit": 10
                },
                "data": {
                    "data_source": "akshare",
                    "cache_path": "./data/cache"
                }
            }
        }
    
    @classmethod
    def load_from_yaml(cls, path: str | Path) -> Settings:
        """Load settings from a YAML file.
        
        Args:
            path: Path to YAML configuration file
            
        Returns:
            Settings instance with loaded configuration
            
        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValidationError: If configuration validation fails
            yaml.YAMLError: If YAML parsing fails
        """
        yaml_path = Path(path)
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        if config_data is None:
            config_data = {}
        
        settings = cls(**config_data)
        cls._instance = settings
        
        return settings
    
    @classmethod
    def load_from_env(cls) -> Settings:
        """Load settings with environment variable overrides.
        
        Environment variables follow the pattern:
        - QUANT_SERVER_HOST
        - QUANT_SERVER_PORT
        - QUANT_SERVER_DEBUG
        - QUANT_TRADING_INITIAL_CAPITAL
        - QUANT_TRADING_COMMISSION_RATE
        - QUANT_TRADING_DEFAULT_EXCHANGE
        - QUANT_RISK_POSITION_LIMIT_RATIO
        - QUANT_RISK_ORDER_LIMIT_AMOUNT
        - QUANT_RISK_DAILY_LOSS_LIMIT
        - QUANT_RISK_CONCENTRATION_LIMIT
        - QUANT_DATA_DATA_SOURCE
        - QUANT_DATA_CACHE_PATH
        
        Returns:
            Settings instance with environment overrides applied
        """
        if cls._instance is not None:
            base_data = cls._instance.to_dict()
        else:
            base_data = {}
        
        env_mappings = {
            "QUANT_SERVER_HOST": ("server", "host"),
            "QUANT_SERVER_PORT": ("server", "port"),
            "QUANT_SERVER_DEBUG": ("server", "debug"),
            "QUANT_TRADING_INITIAL_CAPITAL": ("trading", "initial_capital"),
            "QUANT_TRADING_COMMISSION_RATE": ("trading", "commission_rate"),
            "QUANT_TRADING_DEFAULT_EXCHANGE": ("trading", "default_exchange"),
            "QUANT_RISK_POSITION_LIMIT_RATIO": ("risk", "position_limit_ratio"),
            "QUANT_RISK_ORDER_LIMIT_AMOUNT": ("risk", "order_limit_amount"),
            "QUANT_RISK_DAILY_LOSS_LIMIT": ("risk", "daily_loss_limit"),
            "QUANT_RISK_CONCENTRATION_LIMIT": ("risk", "concentration_limit"),
            "QUANT_DATA_DATA_SOURCE": ("data", "data_source"),
            "QUANT_DATA_CACHE_PATH": ("data", "cache_path"),
        }
        
        for env_var, (section, field_name) in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                if section not in base_data:
                    base_data[section] = {}
                base_data[section][field_name] = cls._convert_env_value(
                    env_value, section, field_name
                )
        
        settings = cls(**base_data)
        cls._instance = settings
        
        return settings
    
    @classmethod
    def _convert_env_value(cls, value: str, section: str, field_name: str) -> Any:
        """Convert environment variable string to appropriate type.
        
        Args:
            value: Environment variable string value
            section: Configuration section name
            field_name: Field name within section
            
        Returns:
            Converted value with appropriate type
        """
        type_mappings = {
            ("server", "port"): int,
            ("server", "debug"): lambda v: v.lower() in ("true", "1", "yes"),
            ("trading", "initial_capital"): float,
            ("trading", "commission_rate"): float,
            ("risk", "position_limit_ratio"): float,
            ("risk", "order_limit_amount"): float,
            ("risk", "daily_loss_limit"): float,
            ("risk", "concentration_limit"): int,
        }
        
        converter = type_mappings.get((section, field_name), str)
        
        try:
            return converter(value)
        except (ValueError, TypeError):
            return value
    
    @classmethod
    def get(cls) -> Settings:
        """Get the global settings singleton instance.
        
        If no instance exists, creates one with default values.
        
        Returns:
            Global Settings instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the global settings singleton.
        
        This clears the singleton instance, allowing a fresh
        configuration to be loaded.
        """
        cls._instance = None
    
    def validate_settings(self) -> None:
        """Explicitly validate all settings.
        
        Raises:
            ValidationError: If any setting fails validation
        """
        Settings(**self.model_dump())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary format.
        
        Returns:
            Dictionary containing all configuration values
        """
        return self.model_dump()
    
    def save_to_yaml(self, path: str | Path) -> None:
        """Save current settings to a YAML file.
        
        Args:
            path: Path to output YAML file
        """
        yaml_path = Path(path)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False)
    
    def __repr__(self) -> str:
        return (
            f"Settings("
            f"server={self.server}, "
            f"trading={self.trading}, "
            f"risk={self.risk}, "
            f"data={self.data})"
        )


# Convenience function for quick loading
def load_config(path: Optional[str | Path] = None, env_override: bool = True) -> Settings:
    """Load configuration from YAML file with optional env overrides.
    
    This is a convenience function that combines load_from_yaml
    and load_from_env in a single call.
    
    Args:
        path: Optional path to YAML file. If None, tries default paths.
        env_override: Whether to apply environment variable overrides
        
    Returns:
        Settings instance with loaded configuration
    """
    default_paths = [
        Path("config.yaml"),
        Path("settings.yaml"),
        Path("quant-trading/config.yaml"),
        Path("quant-trading/settings.yaml"),
    ]
    
    yaml_path = None
    
    if path is not None:
        yaml_path = Path(path)
    else:
        for p in default_paths:
            if p.exists():
                yaml_path = p
                break
    
    if yaml_path is not None and yaml_path.exists():
        settings = Settings.load_from_yaml(yaml_path)
        if env_override:
            settings = Settings.load_from_env()
        return settings
    
    if env_override:
        return Settings.load_from_env()
    
    return Settings.get()