"""算法引擎

AlgoEngine 管理多个算法实例的生命周期，
支持注册、启动、停止、暂停等操作。
"""
import threading
from datetime import datetime
from typing import Dict, List, Optional, Type, Callable, Any
from uuid import uuid4

from execution import OrderManager
from algo_trading.base import BaseAlgo
from algo_trading.types import AlgoStatus, AlgoResult, AlgoInstance, AlgoStatistics, AlgoParams


class AlgoEngine:
    """算法引擎
    
    管理 TWAP/VWAP/Iceberg 等算法实例:
    - register_algo(): 注册算法实例
    - start_algo(): 启动算法
    - stop_algo(): 停止算法
    - pause_algo(): 暂停算法
    - resume_algo(): 恢复算法
    - get_all_algos(): 获取所有算法实例信息
    
    支持:
    - 多算法并行运行
    - 统一的订单管理
    - 状态监控和回调
    """
    
    def __init__(self, order_manager: OrderManager):
        self._order_manager = order_manager
        self._algos: Dict[str, BaseAlgo] = {}
        self._instances: Dict[str, AlgoInstance] = {}
        self._lock = threading.RLock()
        
        self._tick_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._bar_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._complete_callbacks: List[Callable[[str, AlgoResult, AlgoStatistics], None]] = []
    
    def register_algo(
        self,
        algo_class: Type[BaseAlgo],
        params: AlgoParams,
        on_complete: Optional[Callable[[AlgoResult, AlgoStatistics], None]] = None,
    ) -> str:
        """注册算法实例
        
        Args:
            algo_class: 算法类 (TWAPAlgo, VWAPAlgo, IcebergAlgo 等)
            params: 算法参数
            on_complete: 完成回调
            
        Returns:
            算法实例 ID
        """
        algo = algo_class(
            params=params,
            order_manager=self._order_manager,
            on_complete=on_complete,
        )
        
        algo_id = algo.algo_id
        
        with self._lock:
            self._algos[algo_id] = algo
            self._instances[algo_id] = algo.get_instance()
        
        return algo_id
    
    def unregister_algo(self, algo_id: str) -> bool:
        """注销算法实例
        
        Args:
            algo_id: 算法实例 ID
            
        Returns:
            是否成功注销
        """
        with self._lock:
            if algo_id not in self._algos:
                return False
            
            algo = self._algos[algo_id]
            
            if algo.get_status() == AlgoStatus.RUNNING:
                algo.stop()
            
            del self._algos[algo_id]
            del self._instances[algo_id]
        
        return True
    
    def start_algo(self, algo_id: str) -> bool:
        """启动算法
        
        Args:
            algo_id: 算法实例 ID
            
        Returns:
            是否成功启动
        """
        with self._lock:
            if algo_id not in self._algos:
                return False
            
            algo = self._algos[algo_id]
            algo.start()
            self._instances[algo_id] = algo.get_instance()
        
        return True
    
    def stop_algo(self, algo_id: str) -> bool:
        """停止算法
        
        Args:
            algo_id: 算法实例 ID
            
        Returns:
            是否成功停止
        """
        with self._lock:
            if algo_id not in self._algos:
                return False
            
            algo = self._algos[algo_id]
            algo.stop()
            self._instances[algo_id] = algo.get_instance()
        
        return True
    
    def pause_algo(self, algo_id: str) -> bool:
        """暂停算法
        
        Args:
            algo_id: 算法实例 ID
            
        Returns:
            是否成功暂停
        """
        with self._lock:
            if algo_id not in self._algos:
                return False
            
            algo = self._algos[algo_id]
            algo.pause()
            self._instances[algo_id] = algo.get_instance()
        
        return True
    
    def resume_algo(self, algo_id: str) -> bool:
        """恢复算法
        
        Args:
            algo_id: 算法实例 ID
            
        Returns:
            是否成功恢复
        """
        with self._lock:
            if algo_id not in self._algos:
                return False
            
            algo = self._algos[algo_id]
            algo.resume()
            self._instances[algo_id] = algo.get_instance()
        
        return True
    
    def get_algo(self, algo_id: str) -> Optional[BaseAlgo]:
        """获取算法实例"""
        return self._algos.get(algo_id)
    
    def get_algo_status(self, algo_id: str) -> Optional[AlgoStatus]:
        """获取算法状态"""
        algo = self._algos.get(algo_id)
        return algo.get_status() if algo else None
    
    def get_algo_statistics(self, algo_id: str) -> Optional[AlgoStatistics]:
        """获取算法执行统计"""
        algo = self._algos.get(algo_id)
        return algo.get_statistics() if algo else None
    
    def get_all_algos(self) -> List[AlgoInstance]:
        """获取所有算法实例信息
        
        Returns:
            算法实例列表，每个包含:
            - algo_id: 算法 ID
            - algo_name: 算法名称
            - algo_type: 算法类型
            - status: 当前状态
            - statistics: 执行统计
        """
        with self._lock:
            result = []
            for algo_id, algo in self._algos.items():
                self._instances[algo_id] = algo.get_instance()
                result.append(self._instances[algo_id])
            return result
    
    def get_running_algos(self) -> List[AlgoInstance]:
        """获取所有运行中的算法"""
        return [
            inst for inst in self.get_all_algos()
            if inst.status == AlgoStatus.RUNNING
        ]
    
    def stop_all_algos(self) -> int:
        """停止所有算法
        
        Returns:
            停止的算法数量
        """
        stopped = 0
        with self._lock:
            for algo_id in list(self._algos.keys()):
                if self.stop_algo(algo_id):
                    stopped += 1
        return stopped
    
    def on_tick(self, tick_data: Dict[str, Any]):
        """向所有运行算法推送 Tick 数据
        
        Args:
            tick_data: Tick 数据字典，包含 symbol, price, volume 等
        """
        symbol = tick_data.get("symbol", "")
        
        with self._lock:
            for algo in self._algos.values():
                if algo.get_status() != AlgoStatus.RUNNING:
                    continue
                
                if algo.params.symbol != symbol:
                    continue
                
                algo.on_tick(tick_data)
        
        for callback in self._tick_callbacks:
            callback(tick_data)
    
    def on_bar(self, bar_data: Dict[str, Any]):
        """向所有运行算法推送 Bar 数据
        
        Args:
            bar_data: Bar 数据字典，包含 symbol, open, high, low, close, volume 等
        """
        symbol = bar_data.get("symbol", "")
        
        with self._lock:
            for algo in self._algos.values():
                if algo.get_status() != AlgoStatus.RUNNING:
                    continue
                
                if algo.params.symbol != symbol:
                    continue
                
                algo.on_bar(bar_data)
        
        for callback in self._bar_callbacks:
            callback(bar_data)
    
    def register_tick_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """注册 Tick 数据回调"""
        self._tick_callbacks.append(callback)
    
    def register_bar_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """注册 Bar 数据回调"""
        self._bar_callbacks.append(callback)
    
    def register_complete_callback(
        self,
        callback: Callable[[str, AlgoResult, AlgoStatistics], None]
    ):
        """注册算法完成回调"""
        self._complete_callbacks.append(callback)
    
    @property
    def order_manager(self) -> OrderManager:
        return self._order_manager
    
    @property
    def algo_count(self) -> int:
        return len(self._algos)