import pytest
from datetime import datetime, timedelta, timezone
from services.pricing_service import PricingEngine

def test_flat_pricing():
    entry = datetime.now(timezone.utc)
    config = {
        "amount": 5000.0,
        "free_grace_minutes": 15
    }
    
    # Under grace period (10 minutes) -> 0
    exit_grace = entry + timedelta(minutes=10)
    fee = PricingEngine.calculate_fee(entry, exit_grace, "flat", config)
    assert fee == 0.0
    
    # Over grace period -> flat rate
    exit_normal = entry + timedelta(hours=2)
    fee = PricingEngine.calculate_fee(entry, exit_normal, "flat", config)
    assert fee == 5000.0

def test_hourly_pricing():
    entry = datetime.now(timezone.utc)
    config = {
        "free_grace_minutes": 15,
        "first_hours": 4,
        "first_amount": 5000.0,
        "next_hour_amount": 2000.0,
        "max_daily_amount": 30000.0
    }
    
    # 1. Grace period (10 mins) -> 0
    assert PricingEngine.calculate_fee(entry, entry + timedelta(minutes=10), "hourly", config) == 0.0
    
    # 2. Within base hours (3 hours) -> 5000
    assert PricingEngine.calculate_fee(entry, entry + timedelta(hours=3), "hourly", config) == 5000.0
    
    # 3. Base boundary (4 hours) -> 5000
    assert PricingEngine.calculate_fee(entry, entry + timedelta(hours=4), "hourly", config) == 5000.0
    
    # 4. Extra hours (5 hours = 4 base + 1 extra) -> 5000 + 2000 = 7000
    assert PricingEngine.calculate_fee(entry, entry + timedelta(hours=5), "hourly", config) == 7000.0
    
    # 5. Over daily cap (20 hours = 4 base + 16 extra = 37000 -> capped at 30000)
    assert PricingEngine.calculate_fee(entry, entry + timedelta(hours=20), "hourly", config) == 30000.0
    
    # 6. Multi-day (26 hours = 24h cap [30000] + 2h of next day [5000]) -> 35000
    assert PricingEngine.calculate_fee(entry, entry + timedelta(hours=26), "hourly", config) == 35000.0
    
    # 7. Multi-day with remainder under daily cap (40 hours = 24h cap [30000] + 16h next day [29000]) -> 59000
    assert PricingEngine.calculate_fee(entry, entry + timedelta(hours=40), "hourly", config) == 59000.0

    # 8. Multi-day with remainder over daily cap (41 hours = 24h cap [30000] + 17h next day [31000 capped at 30000]) -> 60000
    assert PricingEngine.calculate_fee(entry, entry + timedelta(hours=41), "hourly", config) == 60000.0

def test_negative_duration():
    entry = datetime.now(timezone.utc)
    exit_time = entry - timedelta(hours=1)
    
    with pytest.raises(ValueError):
        PricingEngine.calculate_fee(entry, exit_time, "hourly", {})
