# Quant Trading

A股量化交易系统 — 开源量化交易框架

## 项目结构

```
quant-trading/
├── src/
│   └── data_center/     # 数据中心模块
│       ├── interfaces/  # 数据源接口定义
│       ├── models/      # SQLAlchemy数据模型
│       ├── sources/     # 数据源实现 (AKShare)
│       ├── storage/     # SQLite持久化层
│       └── api/         # 统一对外API
├── frontend/
│   └── dashboard/       # 监控面板 (React+TS)
├── tests/
├── data/                # 运行时数据 (gitignore)
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 安装

```bash
# 后端
pip install -e ".[test]"

# 前端
cd frontend/dashboard && npm install
```

## 快速开始

```python
from data_center import DataAPI

api = DataAPI()
api.initialize()

# 股票列表
stocks = api.list_stocks()
print(f"A股: {len(stocks)}只")

# 日K线
bars = api.get_daily_bar("000001", start, end)

# 交易日判断
api.is_trading_day(date.today())
```

## Sprint 进度

| Sprint | 模块 | 状态 |
|--------|------|------|
| 1 | 数据中心 MVP | ✅ 已完成 |
| 1 | 监控面板 MVP | ✅ 已完成 |
| 2 | 策略引擎 | 🔄 进行中 |
| 2 | 回测引擎 | 🔄 进行中 |

## 数据源

当前接入: **AKShare** (免费A股数据)
- 股票列表 (沪深全市场)
- 日K线 OHLCV
- 交易日历

## License

MIT
