from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

def get_trading_day() -> date:
    """
    Returns the trading day this analysis run represents.
    
    If run before 9am UK time, we're analyzing the previous calendar day's trading.
    Otherwise, we're analyzing today's trading.
    """
    run_time = datetime.now(ZoneInfo('Europe/London'))
    
    if run_time.time() < time(9, 0):
        return (run_time - timedelta(days=1)).date()
    
    return run_time.date()