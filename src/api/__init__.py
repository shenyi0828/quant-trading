from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    orders_router,
    risk_router,
    strategies_router,
    portfolio_router,
    backtest_router,
)
from api.routes.strategies import register_strategy_class
from strategy_engine.examples.dual_thrust import DualThrust


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Quant Trading API started")
    yield
    print("Quant Trading API shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Quant Trading API",
        description="A股量化交易系统 REST API 服务层",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(strategies_router, tags=["策略管理"])
    app.include_router(orders_router, tags=["订单管理"])
    app.include_router(portfolio_router, tags=["组合管理"])
    app.include_router(risk_router, tags=["风控管理"])
    app.include_router(backtest_router, tags=["回测服务"])

    register_strategy_class("DualThrust", DualThrust)

    @app.get("/health", tags=["系统"])
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()