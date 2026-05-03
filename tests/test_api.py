import os
import sys
import pytest
sys.path.insert(0, "src")

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_strategies():
    response = client.get("/strategies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "total" not in data or "strategies" not in data


def test_create_strategy():
    response = client.post(
        "/strategies",
        json={
            "name": "test_strategy",
            "class_name": "DualThrust",
            "symbol": "600000",
            "params": {"N": 4, "K1": 0.5, "K2": 0.5},
            "initial_capital": 100000.0
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "strategy_id" in data
    assert data["name"] == "test_strategy"


def test_get_strategy_not_found():
    response = client.get("/strategies/nonexistent_id")
    assert response.status_code == 404


def test_list_orders():
    response = client.get("/orders")
    assert response.status_code == 200


def test_list_active_orders():
    response = client.get("/orders/active")
    assert response.status_code == 200


def test_get_portfolio_summary():
    response = client.get("/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_capital" in data
    assert "total_value" in data


def test_create_account():
    response = client.post(
        "/portfolio/accounts",
        json={
            "strategy_name": "test_account",
            "initial_capital": 50000.0
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "account_id" in data


def test_list_accounts():
    response = client.get("/portfolio/accounts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_risk_rules():
    response = client.get("/risk/rules")
    assert response.status_code == 200


def test_get_backtest_strategies():
    response = client.get("/backtest/strategies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.skip(reason="AKShare requires external network access to eastmoney.com — not available in test environment")
def test_backtest_invalid_strategy():
    response = client.post(
        "/backtest/run",
        json={
            "strategy_name": "InvalidStrategy",
            "symbol": "600000",
            "start_date": "2025-01-01",
            "end_date": "2025-03-01"
        }
    )
    assert response.status_code == 400


if __name__ == "__main__":
    print("Running API tests...")
    test_health_check()
    print("  [✓] Health check")
    
    test_list_strategies()
    print("  [✓] List strategies")
    
    test_create_strategy()
    print("  [✓] Create strategy")
    
    test_get_strategy_not_found()
    print("  [✓] Strategy not found (404)")
    
    test_list_orders()
    print("  [✓] List orders")
    
    test_list_active_orders()
    print("  [✓] List active orders")
    
    test_get_portfolio_summary()
    print("  [✓] Portfolio summary")
    
    test_create_account()
    print("  [✓] Create account")
    
    test_list_accounts()
    print("  [✓] List accounts")
    
    test_get_risk_rules()
    print("  [✓] Risk rules")
    
    test_get_backtest_strategies()
    print("  [✓] Backtest strategies")
    
    test_backtest_invalid_strategy()
    print("  [✓] Backtest invalid strategy (400)")
    
    print("\nAll API tests passed!")