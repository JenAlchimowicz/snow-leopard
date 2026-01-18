import polars as pl
from config import ColumnConfig

def add_ema_column(
    frame: pl.DataFrame,
    span: int,
) -> pl.DataFrame:
    """Append an exponential moving average column."""
    if span <= 0:
        raise ValueError("span must be positive.")
    return (
        frame
        .sort([ColumnConfig.ID, ColumnConfig.DATE])
        .with_columns(
            pl.col(ColumnConfig.ADJUSTED_CLOSE)
              .ewm_mean(span=span, adjust=False)
              .over(ColumnConfig.ID)
              .alias(f"ema_{span}")
        )
    )


def add_rsi_column(
    frame: pl.DataFrame,
    length: int = 14,
) -> pl.DataFrame:
    """
    Append a Relative Strength Index (RSI) column using Wilder's smoothing,
    computed per id on adjusted_close.
    """
    if length <= 0:
        raise ValueError("length must be positive.")

    alpha = 1.0 / float(length)  # Wilder smoothing factor

    df = frame.sort([ColumnConfig.ID, ColumnConfig.DATE])
    df = df.with_columns(
        # 1) Price change
        pl.col(ColumnConfig.ADJUSTED_CLOSE)
          .diff()
          .over(ColumnConfig.ID)
          .alias("delta")
    ).with_columns(
        # 2) Gains and losses
        pl.when(pl.col("delta") > 0)
          .then(pl.col("delta"))
          .otherwise(0.0)
          .alias("gain"),
        pl.when(pl.col("delta") < 0)
          .then(-pl.col("delta"))
          .otherwise(0.0)
          .alias("loss"),
    ).with_columns(
        # 3) Wilder-style smoothed averages (EMA with alpha = 1/length)
        pl.col("gain")
          .ewm_mean(alpha=alpha, adjust=False)
          .over(ColumnConfig.ID)
          .alias("avg_gain"),
        pl.col("loss")
          .ewm_mean(alpha=alpha, adjust=False)
          .over(ColumnConfig.ID)
          .alias("avg_loss"),
    ).with_columns(
        # 4) RSI calculation
        pl.when(pl.col("avg_loss") == 0)
          .then(100.0)  # no losses → RSI = 100
          .otherwise(
              100.0 - 100.0 / (1.0 + (pl.col("avg_gain") / pl.col("avg_loss")))
          )
          .alias(f"rsi_{length}")
    )

    # Optional: hide RSI for the warmup region (first `length` rows per id)
    df = df.with_columns(
        pl.when(
            pl.arange(0, pl.len()).over(ColumnConfig.ID) < length
        )
        .then(None)
        .otherwise(pl.col(f"rsi_{length}"))
        .alias(f"rsi_{length}")
    )

    # Drop intermediates
    return df.drop(["delta", "gain", "loss", "avg_gain", "avg_loss"])


def add_all_time_high(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    for col in [
        ColumnConfig.ADJUSTED_CLOSE,
        ColumnConfig.ID,
        ColumnConfig.DATE,
    ]:
        assert col in frame.columns, f"{col} not in dataframe"
    
    frame = frame.sort([ColumnConfig.ID, ColumnConfig.DATE])
    
    return (
        frame
        .with_columns([
            (
                pl.col(ColumnConfig.ADJUSTED_CLOSE)
                .cum_max()
                .over(ColumnConfig.ID)
            )
            .alias("all_time_high_price")
        ])
    )
