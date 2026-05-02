# Data Center MVP

A股行情数据接入与存储模块

## 功能

- **股票列表**: A股全部股票信息 (5201只: 2312上海 + 2889深圳)
- **日K线数据**: OHLCV数据获取与存储
- **交易日历**: 交易日判断与查询 (2026年242个交易日)
- **数据持久化**: SQLite本地存储

## 架构

```
data_center/
├── interfaces/          # 抽象接口层
│   └── data_source.py   # IDataSource 接口定义
├── models/              # 数据模型
│   └── schema.py        # SQLAlchemy 表结构
├── sources/             # 数据源实现
│   └── akshare_source.py # AKShare适配器
├── storage/             # 存储层
│   └── sqlite_storage.py # SQLite存储实现
├── api/                 # 对外API
│   └── data_api.py      # DataAPI 统一接口
└── config.py            # 配置
```

## 使用

```python
from data_center import DataAPI

api = DataAPI()
api.initialize()  # 同步股票列表和交易日历

# 获取股票列表
stocks = api.list_stocks()  # 全部A股
sh_stocks = api.list_stocks(exchange="SH")  # 仅上海

# 获取日K线
from datetime import date, timedelta
bars = api.get_daily_bar("600000", date(2026, 1, 1), date(2026, 4, 30))

# 判断交易日
api.is_trading_day(date.today())  # True/False
api.get_last_trading_day()  # 最近交易日

# 查询交易日历
calendar = api.get_trading_days(year=2026)
```

## 依赖

```
akshare>=1.12.0
sqlalchemy>=2.0.0
pandas>=2.0.0
```

## 验收标准

| 功能 | 状态 | 说明 |
|------|------|------|
| list_stocks() | ✅ | 返回A股列表 (5201只) |
| get_daily_bar(symbol, start, end) | ✅ | 返回日线OHLCV数据 |
| is_trading_day(date) | ✅ | 判断是否为A股交易日 |
| 数据持久化存储 | ✅ | SQLite存储 |
| 查询性能 | ✅ | 可接受 |

## 数据存储位置

- 数据库: `data/market.db`
- 缓存目录: `data/cache/`