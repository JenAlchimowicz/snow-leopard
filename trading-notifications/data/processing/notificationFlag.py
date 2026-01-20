import polars as pl
from datetime import timedelta
from typing import List
from utils.tradingDay import get_trading_day

def add_notification_flag(dd: pl.DataFrame) -> pl.DataFrame:
    window_size = 10
    dd = dd.sort(["id", "date"])
    dd = dd.with_columns([
        (
            # rolling_max returns 1 if any row is True, then we cast to Boolean
            pl.col("flag_ema_200_tuching_price").cast(pl.Int8).rolling_max(window_size=window_size).cast(pl.Boolean)
            &
            pl.col("flag_ema5_x_ema20_on_green_candle")
            &
            pl.col("flag_rsi_above_50").cast(pl.Int8).rolling_max(window_size=window_size).cast(pl.Boolean)
        )
        .over("id")
        .alias("flag_notification")
    ])

    # Deduplicate notifications - keep only the first occurrence in a series of True values
    dd = dd.with_columns(
        (
            pl.col("flag_notification")
        .cast(pl.Int8)                # Convert True/False to 1/0 first
        .diff()                      # Now subtraction (1 - 0) works
        .fill_null(1)                # If the first row is True, we want to keep it
        .over("id")
        .eq(1)                       # Keep only the rows where it just became 1
        & pl.col("flag_notification") # Double check it's actually True (handles edge cases)
        ).alias("flag_notification_deduplicated")
    )
    return dd


def final_filter(
        data: pl.DataFrame,
        exchanges: List[str],
        lookback: int = 0,
        volume_threshold: int = 250000
) -> pl.DataFrame:
    return (
        data
        .filter(
            (pl.col("flag_notification_deduplicated") == True)
            & (pl.col("exchange_short_name").is_in(exchanges))
        )
        .filter(pl.col("volume") > volume_threshold)
        .with_columns(
            pl.col("date").str.to_date()
        )
        .filter(
            pl.col("date") >= pl.lit(get_trading_day() - timedelta(days=lookback))
        )
        .sort("date", descending=True)
    )
