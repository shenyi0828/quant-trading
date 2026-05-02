# Quant Trading

A股量化交易系统

## 项目结构

```
quant-trading/
├── data_center/     # 数据中心模块
│   ├── interfaces/  # 数据源接口定义
│   ├── models/      # 数据模型 (SQLAlchemy)
│   ├── sources/     # 数据源实现 (AKShare)
│   ├── storage/     # SQLite存储层
│   └── api/         # 对外API
├── data/            # 数据存储目录
│   ├── market.db    # SQLite数据库
│   └── cache/       # 缓存目录
└ requirements.txt   # Python依赖
└ test_data_center.py # 测试脚本
```

## 数据中心 MVP

### 功能

- **股票列表**: 5201只A股 (2312上海 + 2889深圳)
- **日K线数据**: OHLCV数据获取与存储
- **交易日历**: 交易日判断 (2026年242个交易日)
- **数据持久化**: SQLite本地存储

### 使用

```python
from data_center import DataAPI

api = DataAPI()
api.initialize()

stocks = api.list_stocks()
api.is_trading_day(date.today())
api.get_daily_bar("600000", start, end)
```

### 安装依赖

```bash
pip install akshare sqlalchemy pandas
```

## Sprint 1 进度

| 模块 | 状态 | 分支 |
|------|------|------|
| 数据中心 MVP | ✅ 完成 | main |
| 监控面板 MVP | 🚧 开发中 | feature/monitor-dashboard |

## 下一步

Sprint 2: 策略引擎 + 回测引擎