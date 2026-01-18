import polars as pl
from config import ColumnConfig

def add_ema5_x_ema20_flag(frame: pl.DataFrame) -> pl.DataFrame:
    for col in [
        ColumnConfig.ID,
        ColumnConfig.DATE,
        "ema_5",
        "ema_20",
        ColumnConfig.OPEN,
        ColumnConfig.ADJUSTED_CLOSE,
        ColumnConfig.HIGH,
    ]:
        assert col in frame.columns, f"{col} not in dataframe"
    
    frame = frame.sort([ColumnConfig.ID, ColumnConfig.DATE])
    return (
        frame
        .with_columns([
            (
                # previously ema_5 was below or equal ema_20
                (pl.col("ema_5").shift(1) <= pl.col("ema_20").shift(1))
                &
                # now ema_5 is above ema_20
                (pl.col("ema_5") > pl.col("ema_20"))
                &
                # green candle: ADJUSTED_CLOSE > open
                (pl.col(ColumnConfig.ADJUSTED_CLOSE) > pl.col(ColumnConfig.OPEN))
                &
                # adjusted close within 1% of high
                (pl.col(ColumnConfig.ADJUSTED_CLOSE) >= 0.99 * pl.col(ColumnConfig.HIGH))
                &
                # open and low of cross over candle should be on or above 5 ema (with tolerance)
                (pl.col(ColumnConfig.OPEN) >= 0.995 * pl.col("ema_5"))
                &
                (pl.col(ColumnConfig.LOW) >= 0.995 * pl.col("ema_5"))
                &
                # No part of the candle on cross over candle has gone below 20 ema
                (pl.col(ColumnConfig.OPEN) >= pl.col("ema_20"))
                &
                (pl.col(ColumnConfig.HIGH) >= pl.col("ema_20"))
                # previous candle of cross over candle is not  red candle
                & (pl.col(ColumnConfig.ADJUSTED_CLOSE).shift(1) > pl.col(ColumnConfig.OPEN).shift(1))
            )
            .alias("flag_ema5_x_ema20_on_green_candle")
        ])
    )

def add_ema_200_flag(frame: pl.DataFrame, tolerance: float = 0.05) -> pl.DataFrame:
    for col in ["ema_200", ColumnConfig.ADJUSTED_CLOSE, ColumnConfig.ID, ColumnConfig.DATE]:
        assert col in frame.columns, f"{col} not in dataframe"

    frame = frame.sort([ColumnConfig.ID, ColumnConfig.DATE])
    return (
        frame
        .with_columns([
            (pl.col(ColumnConfig.ADJUSTED_CLOSE) > pl.col("ema_200"))
                .alias("close_bigger_than_ema"),
            (pl.col(ColumnConfig.ADJUSTED_CLOSE) <= pl.col("ema_200") * (1 + tolerance))
                .alias("ema_within_tolerance"),
        ])
        .with_columns([
            (
                (pl.col("close_bigger_than_ema") & pl.col("ema_within_tolerance"))
                .rolling_min(window_size=10)
                .cast(pl.Boolean)
                .over(ColumnConfig.ID)
            ).alias("flag_ema_200_tuching_price")
        ])
        .drop(["close_bigger_than_ema", "ema_within_tolerance"])
    )

def add_rsi_approaching_50_flag(frame: pl.DataFrame) -> pl.DataFrame:
    for col in [
        ColumnConfig.ID,
        ColumnConfig.DATE,
        "rsi_14",
    ]:
        assert col in frame.columns, f"{col} not in dataframe"

    frame = frame.sort([ColumnConfig.ID, ColumnConfig.DATE])
    return (
        frame
        .with_columns([
            (
                pl.col("rsi_14") > 50
            ).alias("flag_rsi_above_50")
        ])
    )
