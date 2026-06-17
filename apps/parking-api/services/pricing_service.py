from abc import ABC, abstractmethod
from datetime import datetime, timezone
import math
from typing import Dict, Any, Type
import logging

logger = logging.getLogger("parking-api")

class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, entry_time: datetime, exit_time: datetime, config: Dict[str, Any]) -> float:
        pass

class FlatPricingStrategy(PricingStrategy):
    """
    Flat rate per parking session (per turn).
    Config format:
    {
        "amount": 5000.0,
        "free_grace_minutes": 15
    }
    """
    def calculate(self, entry_time: datetime, exit_time: datetime, config: Dict[str, Any]) -> float:
        free_grace_minutes = config.get("free_grace_minutes", 15)
        duration_sec = (exit_time - entry_time).total_seconds()
        
        if duration_sec <= free_grace_minutes * 60:
            return 0.0
            
        return float(config.get("amount", 5000.0))

class HourlyPricingStrategy(PricingStrategy):
    """
    Hourly progressive rate, with optional grace period, initial hours base rate,
    subsequent hours rate, and daily caps.
    Config format:
    {
        "free_grace_minutes": 15,
        "first_hours": 4,
        "first_amount": 5000.0,
        "next_hour_amount": 2000.0,
        "max_daily_amount": 30000.0
    }
    """
    def calculate(self, entry_time: datetime, exit_time: datetime, config: Dict[str, Any]) -> float:
        duration_sec = (exit_time - entry_time).total_seconds()
        
        # Check grace period
        free_grace_minutes = config.get("free_grace_minutes", 15)
        if duration_sec <= free_grace_minutes * 60:
            return 0.0
            
        duration_hours = duration_sec / 3600.0
        
        first_hours = config.get("first_hours", 4)
        first_amount = config.get("first_amount", 5000.0)
        next_hour_amount = config.get("next_hour_amount", 2000.0)
        max_daily_amount = config.get("max_daily_amount", 30000.0)
        
        # Calculate for duration under 24 hours
        def calculate_sub_24h(hours: float) -> float:
            if hours <= first_hours:
                return float(first_amount)
            extra_hours = math.ceil(hours - first_hours)
            fee = first_amount + (extra_hours * next_hour_amount)
            return float(min(fee, max_daily_amount))
            
        # Multi-day parking logic
        days = math.floor(duration_hours / 24.0)
        remaining_hours = duration_hours % 24.0
        
        if days > 0:
            days_fee = days * max_daily_amount
            rem_fee = calculate_sub_24h(remaining_hours) if remaining_hours > 0 else 0.0
            return float(days_fee + rem_fee)
        else:
            return calculate_sub_24h(duration_hours)

class PricingEngine:
    _strategies: Dict[str, Type[PricingStrategy]] = {
        "flat": FlatPricingStrategy,
        "hourly": HourlyPricingStrategy
    }
    
    @classmethod
    def register_strategy(cls, name: str, strategy_cls: Type[PricingStrategy]):
        cls._strategies[name] = strategy_cls
        logger.info(f"Registered pricing strategy: {name}")

    @classmethod
    def calculate_fee(
        cls, 
        entry_time: datetime, 
        exit_time: datetime, 
        rule_type: str, 
        config: Dict[str, Any]
    ) -> float:
        # Guarantee timezone aware comparison
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)
        if exit_time.tzinfo is None:
            exit_time = exit_time.replace(tzinfo=timezone.utc)
            
        if exit_time < entry_time:
            raise ValueError("Exit time cannot be earlier than entry time")
            
        strategy_cls = cls._strategies.get(rule_type)
        if not strategy_cls:
            logger.warning(f"Pricing strategy '{rule_type}' not found. Falling back to hourly.")
            strategy_cls = HourlyPricingStrategy
            
        strategy = strategy_cls()
        return strategy.calculate(entry_time, exit_time, config)
