from data.loaders.DataLoader import DataLoader
from data.loaders.EodhdClient import EodhdClient
from data.loaders.storage.S3StorageClient import S3StorageClient
from data.processing.indicators import add_ema_column, add_rsi_column, add_all_time_high
from data.processing.flags import add_ema_200_flag, add_ema5_x_ema20_flag, add_rsi_approaching_50_flag
from data.processing.notificationFlag import add_notification_flag, final_filter
from smsecrets.secrets import get_secrets
from notifications.email import send_update_email
from notifications.graphs import create_charts
from utils.tradingDay import get_trading_day
from config import Config, ColumnConfig
from datetime import date
import polars as pl

def main():
    print(f"Hello from trading-notifications, system date is {date.today().isoformat()}, trading day is {get_trading_day().isoformat()}")

    # Load configuration
    secrets = get_secrets()
    eodhdApiKey = secrets['eodhd_api_key']
    exchanges = [e.strip() for e in secrets["exchanges"].split(",")]
    lookback = int(secrets["lookback"])
    volume_threshold = int(secrets["volume_threshold"])
    recipients = [e.strip() for e in secrets["email_recipients"].split(",")]
    print(f"Configured to notify for exchanges: {exchanges}, lookback: {lookback}, volume threshold: {volume_threshold}, email recipients: {recipients}")

    # Prep data
    eodhdClient = EodhdClient(eodhdApiKey)
    s3StorageClient = S3StorageClient(Config.S3_BUCKET_NAME, base_path=Config.S3_DATA_PATH)
    dataLoader = DataLoader(eodhdClient, s3StorageClient)

    dataLoader.load_missing_data()

    data = dataLoader.load_data(date_from=date(2024,1,1))
    data = data.with_columns((pl.col(ColumnConfig.EXCHANGE_SHORT_NAME) + "_" + pl.col(ColumnConfig.CODE)).alias(ColumnConfig.ID))
    print(f"Data loaded with shape: {data.shape}")

    # Indicators
    data = add_ema_column(data, span=200)
    data = add_ema_column(data, span=20)
    data = add_ema_column(data, span=5)
    data = add_rsi_column(data)
    data = add_all_time_high(data)
    print(f"Indicators added, data shape: {data.shape}")

    # Flags
    data = add_ema_200_flag(data, 0.05)
    data = add_ema5_x_ema20_flag(data)
    data = add_rsi_approaching_50_flag(data)
    data = add_notification_flag(data)
    print(f"Flags added, data shape: {data.shape}")

    # Final filter
    filtered = final_filter(data, exchanges, lookback, volume_threshold)
    print(f"After final filter, data shape: {filtered.shape}")
    tickers = filtered.select(pl.col(ColumnConfig.ID)).unique().to_series().to_list()
    print(f"Notifications for {len(tickers)} tickers: {tickers}")

    try:
        create_charts(data, tickers)
    except Exception as e:
        print(f"Error creating charts: {e}")

    if tickers:
        send_update_email(tickers, recipients)

if __name__ == "__main__":
    main()
