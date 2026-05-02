"""绩效指标计算"""
from typing import List, Tuple
import math


def calculate_total_return(final_value: float, initial_capital: float) -> float:
    if initial_capital == 0:
        return 0.0
    return (final_value - initial_capital) / initial_capital


def calculate_annualized_return(total_return: float, days: int) -> float:
    if days <= 0:
        return 0.0
    return (1 + total_return) ** (252 / days) - 1


def calculate_max_drawdown(values: List[float]) -> Tuple[float, int, int]:
    if not values:
        return 0.0, 0, 0
    
    peak = values[0]
    peak_idx = 0
    max_dd = 0.0
    max_dd_start = 0
    max_dd_end = 0
    
    for i, v in enumerate(values):
        if v > peak:
            peak = v
            peak_idx = i
        
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
            max_dd_start = peak_idx
            max_dd_end = i
    
    return max_dd, max_dd_start, max_dd_end


def calculate_sharpe_ratio(
    daily_returns: List[float], 
    risk_free_rate: float = 0.02
) -> float:
    if not daily_returns:
        return 0.0
    
    mean_return = sum(daily_returns) / len(daily_returns)
    
    variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
    std_return = math.sqrt(variance) if variance > 0 else 0.0
    
    if std_return == 0:
        return 0.0
    
    annualized_std = std_return * math.sqrt(252)
    daily_rf = risk_free_rate / 252
    
    excess_return = mean_return - daily_rf
    sharpe = (excess_return * 252) / annualized_std if annualized_std > 0 else 0.0
    
    return sharpe


def calculate_trade_metrics(trades: List) -> dict:
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_loss_ratio": 0.0,
            "total_profit": 0.0,
            "total_loss": 0.0,
        }
    
    profits = []
    losses = []
    
    for trade in trades:
        if trade.direction.value == "long":
            pnl = trade.price * trade.quantity - trade.commission
        else:
            pnl = trade.price * trade.quantity - trade.commission
        
        if pnl > 0:
            profits.append(pnl)
        else:
            losses.append(abs(pnl))
    
    total_trades = len(trades)
    win_count = len(profits)
    win_rate = win_count / total_trades if total_trades > 0 else 0.0
    
    total_profit = sum(profits)
    total_loss = sum(losses)
    
    avg_profit = total_profit / win_count if win_count > 0 else 0.0
    avg_loss = total_loss / (total_trades - win_count) if (total_trades - win_count) > 0 else 0.0
    
    profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0.0
    
    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_loss_ratio": profit_loss_ratio,
        "total_profit": total_profit,
        "total_loss": total_loss,
    }